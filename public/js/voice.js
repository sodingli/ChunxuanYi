// Voice 模块 - 语音识别 + TTS + 唤醒
import { EventBus, Events } from './event-bus.js';

let isListening = false;
let recognition = null;
let isSpeaking = false;
let speakGeneration = 0;
let preferredVoice = null;

let silenceTimer = null;
let finalTranscript = '';
const SILENCE_TIMEOUT = 3000;

// 唤醒词（模拟）
let wakeEnabled = false;
let wakeListening = false;
let wakeRecognition = null;
const WAKE_WORD = '你好颐';

let ttsUnlocked = false;

function unlockTTS() {
  if (ttsUnlocked || !('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance('');
  utterance.volume = 0;
  speechSynthesis.speak(utterance);
  ttsUnlocked = true;
}

export function init() {
  unlockTTS();

  // 页面加载后提前发起麦克风权限请求（安全上下文下 getUserMedia 无需用户手势）
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(mic => mic.getTracks().forEach(t => t.stop()))
      .catch(() => {});
  }

  const voiceBtn = document.getElementById('voiceBtn');
  const wakeBtn = document.getElementById('wakeBtn');

  // 检查浏览器是否支持语音识别
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.disabled = true;
    voiceBtn.title = '当前浏览器不支持语音识别';
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    voiceBtn.disabled = true;
    voiceBtn.title = '当前页面不是安全上下文（需要 HTTPS 或 localhost）';
  }

  voiceBtn.addEventListener('click', () => {
    if (isSpeaking) {
      interruptSpeech();
    } else if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  });

  wakeBtn.addEventListener('click', () => {
    wakeEnabled = !wakeEnabled;
    wakeBtn.textContent = wakeEnabled ? '🔔 监听中' : '🔔 唤醒';
    wakeBtn.style.opacity = wakeEnabled ? '1' : '0.7';
    if (wakeEnabled) startWakeListening();
    else stopWakeListening();
  });

  // 监听聊天事件，需要TTS
  EventBus.on(Events.CHAT_AI_MSG, ({ text, speak: shouldSpeak }) => {
    if (shouldSpeak !== false) speak(text);
  });
  EventBus.on(Events.CHAT_PROACTIVE, ({ message }) => speak(message));
  EventBus.on(Events.VOICE_INTERRUPT, () => interruptSpeech());

  // 初始化TTS语音
  initTTS();
}

function initTTS() {
  if (!('speechSynthesis' in window)) return;
  speechSynthesis.onvoiceschanged = () => {
    preferredVoice = findBestChineseVoice();
  };
  preferredVoice = findBestChineseVoice();
}

function findBestChineseVoice() {
  const voices = speechSynthesis.getVoices();
  const priorities = [
    v => v.name.includes('Google') && v.lang.startsWith('zh'),
    v => v.name.includes('Microsoft') && v.lang.startsWith('zh') && v.name.includes('Female'),
    v => v.lang.startsWith('zh') && (v.name.includes('女') || v.name.includes('Female') || v.name.includes('Xiaoxiao')),
    v => v.lang.startsWith('zh-CN'),
    v => v.lang.startsWith('zh'),
  ];
  for (const test of priorities) {
    const found = voices.find(test);
    if (found) return found;
  }
  return voices.find(v => v.lang.startsWith('zh')) || null;
}

// ============ ASR ============

function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showError('您的浏览器不支持语音识别，请使用Chrome浏览器');
    return;
  }

  if (recognition) { try { recognition.abort(); } catch (e) {} }

  finalTranscript = '';

  recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  const voiceBtn = document.getElementById('voiceBtn');
  const listeningIndicator = document.getElementById('listeningIndicator');
  const voiceStatus = document.getElementById('voiceStatus');
  const messageInput = document.getElementById('messageInput');

  recognition.onstart = () => {
    isListening = true;
    voiceBtn.textContent = '⏹️ 停止';
    voiceBtn.classList.remove('speaking');
    listeningIndicator.classList.add('active');
    voiceStatus.textContent = '正在听您说话...';
    EventBus.emit(Events.VOICE_LISTENING_START, {});
  };

  recognition.onresult = (event) => {
    let interim = '';
    finalTranscript = '';
    for (let i = 0; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interim += transcript;
      }
    }

    const display = finalTranscript || interim;
    if (display) {
      messageInput.value = display;
      voiceStatus.textContent = '识别中: "' + display + '"';
    }

    resetSilenceTimer();
  };

  recognition.onerror = (event) => {
    if (event.error === 'no-speech') {
      voiceStatus.textContent = '未检测到语音，请靠近麦克风重试';
    } else if (event.error === 'not-allowed') {
      showError('麦克风权限被拒绝，请在浏览器地址栏左侧🔒或🔒图标处点击，将"麦克风"设为"允许"，然后刷新页面重新尝试');
    } else if (event.error === 'audio-capture') {
      showError('未检测到麦克风，请连接麦克风设备');
    } else if (event.error !== 'aborted' && event.error !== 'network') {
      voiceStatus.textContent = '语音识别出错: ' + event.error;
      console.warn('ASR error:', event.error);
    }
    cleanupListening();
  };

  recognition.onend = () => {
    const text = finalTranscript || messageInput.value.trim();
    if (text) {
      voiceStatus.textContent = '识别完成: "' + text + '"';
      messageInput.value = text;
      isListening = false;
      document.getElementById('listeningIndicator').classList.remove('active');
      voiceBtn.textContent = '🎤 语音';
      EventBus.emit(Events.VOICE_TRANSCRIPT, { text });
      EventBus.emit(Events.VOICE_LISTENING_END, {});
    } else {
      cleanupListening();
    }
  };

  try { recognition.start(); } catch (e) {
    voiceStatus.textContent = '启动语音识别失败，请重试';
  }
}

function stopListening() {
  if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
  if (recognition) { try { recognition.stop(); } catch (e) {} }
}

function cleanupListening() {
  if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
  isListening = false;
  const voiceBtn = document.getElementById('voiceBtn');
  voiceBtn.textContent = '🎤 语音';
  document.getElementById('listeningIndicator').classList.remove('active');
  EventBus.emit(Events.VOICE_LISTENING_END, {});
}

function resetSilenceTimer() {
  if (silenceTimer) clearTimeout(silenceTimer);
  silenceTimer = setTimeout(() => {
    if (isListening) {
      document.getElementById('voiceStatus').textContent = '检测到静音，自动发送...';
      if (recognition) { try { recognition.stop(); } catch (e) {} }
    }
  }, SILENCE_TIMEOUT);
}

// ============ TTS ============

function speak(text) {
  if (!('speechSynthesis' in window)) return;

  // 确保 TTS 已解锁
  unlockTTS();

  speakGeneration++;
  const myGeneration = speakGeneration;
  speechSynthesis.cancel();

  const sentences = text.match(/[^。！？；\n]+[。！？；\n]?/g) || [text];
  let index = 0;

  const voiceBtn = document.getElementById('voiceBtn');
  const speakingIndicator = document.getElementById('speakingIndicator');
  const voiceStatus = document.getElementById('voiceStatus');

  function finishSpeaking() {
    if (speakGeneration !== myGeneration) return;
    isSpeaking = false;
    speakingIndicator.classList.remove('active');
    voiceBtn.textContent = '🎤 语音';
    voiceBtn.classList.remove('speaking');
    voiceStatus.textContent = '';
    EventBus.emit(Events.VOICE_SPEAKING_END, {});
  }

  function speakNext() {
    if (speakGeneration !== myGeneration) return;
    if (index >= sentences.length) { finishSpeaking(); return; }

    const sentence = sentences[index].trim();
    if (!sentence) { index++; speakNext(); return; }

    const utterance = new SpeechSynthesisUtterance(sentence);
    utterance.lang = 'zh-CN';
    utterance.rate = 0.88;
    utterance.pitch = 1.1;
    utterance.volume = 1.0;
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.onend = () => {
      index++;
      if (speakGeneration !== myGeneration) return;
      if (index < sentences.length) {
        setTimeout(speakNext, 150);
      } else {
        finishSpeaking();
      }
    };

    utterance.onerror = (e) => {
      if (speakGeneration !== myGeneration) return;
      // 非取消错误才结束
      if (e.error !== 'canceled') finishSpeaking();
    };

    speechSynthesis.speak(utterance);
  }

  isSpeaking = true;
  speakingIndicator.classList.add('active');
  voiceBtn.textContent = '🎤 打断';
  voiceBtn.classList.add('speaking');
  voiceStatus.textContent = '颐正在说话...';
  EventBus.emit(Events.VOICE_SPEAKING_START, {});
  speakNext();
}

function interruptSpeech() {
  speakGeneration++;
  speechSynthesis.cancel();
  isSpeaking = false;
  document.getElementById('speakingIndicator').classList.remove('active');
  document.getElementById('voiceBtn').textContent = '🎤 语音';
  document.getElementById('voiceBtn').classList.remove('speaking');
  document.getElementById('voiceStatus').textContent = '已打断，开始听您说话...';
  startListening();
}

// ============ 唤醒词 ============

function startWakeListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  if (wakeRecognition) { try { wakeRecognition.abort(); } catch (e) {} }

  wakeRecognition = new SpeechRecognition();
  wakeRecognition.lang = 'zh-CN';
  wakeRecognition.continuous = true;
  wakeRecognition.interimResults = false;

  wakeRecognition.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (transcript.includes('颐') || transcript.includes('你好') || transcript.includes('在吗')) {
        EventBus.emit(Events.VOICE_WAKE, { text: transcript });
        // 唤醒后自动进入对话
        startListening();
      }
    }
  };

  wakeRecognition.onend = () => {
    if (wakeEnabled && !isListening) {
      // 自动重启
      try { wakeRecognition.start(); } catch (e) {}
    }
  };

  try { wakeRecognition.start(); } catch (e) {}
  document.getElementById('voiceStatus').textContent = '唤醒词监听中：说"你好颐"开始对话';
}

function stopWakeListening() {
  if (wakeRecognition) {
    try { wakeRecognition.abort(); } catch (e) {}
    wakeRecognition = null;
  }
  document.getElementById('voiceStatus').textContent = '';
}

function showError(msg) {
  const el = document.getElementById('errorMsg');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 5000);
}
