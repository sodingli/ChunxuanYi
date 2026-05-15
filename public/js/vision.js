// Vision 模块 - 人脸检测 + 情绪识别 + 跌倒检测
import { EventBus, Events } from './event-bus.js';

let stream = null;
let isRunning = false;
let animationId = null;
let modelsLoaded = false;
let lastDetectTime = 0;
const DETECT_INTERVAL = 300;

// 情绪触发
const emotionBuffer = [];
const EMOTION_SAMPLE_INTERVAL = 1000;
const EMOTION_TRIGGER_DURATION = 7000;
const EMOTION_TRIGGER_THRESHOLD = 0.6;
let lastEmotionSampleTime = 0;
let emotionTriggered = false;
let lastTriggerTime = 0;
const TRIGGER_COOLDOWN = 60000;

const emotionPrompts = {
  happy: [
    '爷爷/奶奶看起来心情不错呀！是不是遇到什么开心的事了？',
    '您笑得真好看，今天一定是个好日子！',
    '看到您开心，我也高兴！要不要聊聊今天的好事？',
  ],
  sad: [
    '爷爷/奶奶，您看起来有点心事，愿意和我说说吗？',
    '别难过，我在这里陪着您呢。有什么烦心事可以说出来。',
    '看您不太开心，要不要听首老歌放松一下？',
  ],
  angry: [
    '爷爷/奶奶，是不是有什么事让您着急了？慢慢说，我听着呢。',
    '别生气了，气坏身体不值得。跟我说说怎么了？',
  ],
  fearful: [
    '爷爷/奶奶，您是不是有点担心什么？跟我说说，也许我能帮忙。',
    '别害怕，有我在呢。有什么不放心的可以告诉我。',
  ],
  surprised: [
    '爷爷/奶奶，是什么让您这么惊讶？快跟我说说！',
  ],
};

// 跌倒检测
let lastPoseData = null;
const FALL_FRAMES_REQUIRED = 3;
let fallFrameCount = 0;
let fallDetected = false;

export function init() {
  const video = document.getElementById('video');
  const overlay = document.getElementById('overlay');
  const ctx = overlay.getContext('2d');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const placeholder = document.getElementById('placeholder');

  startBtn.addEventListener('click', async () => {
    startBtn.disabled = true;
    startBtn.textContent = '加载中...';

    const ok = await loadModels();
    if (!ok) {
      startBtn.disabled = false;
      startBtn.textContent = '📷 开启';
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      video.srcObject = stream;
      video.style.display = 'block';
      placeholder.style.display = 'none';

      video.addEventListener('loadedmetadata', () => {
        overlay.width = video.videoWidth;
        overlay.height = video.videoHeight;
        stopBtn.disabled = false;
        isRunning = true;
        detectLoop(video, overlay, ctx);
      }, { once: true });

    } catch (err) {
      showError('无法访问摄像头: ' + err.message);
      startBtn.disabled = false;
      startBtn.textContent = '📷 开启';
    }
  });

  stopBtn.addEventListener('click', () => {
    isRunning = false;
    if (animationId) { cancelAnimationFrame(animationId); animationId = null; }
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.style.display = 'none';
    placeholder.style.display = 'block';
    startBtn.disabled = false;
    startBtn.textContent = '📷 开启';
    stopBtn.disabled = true;
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    document.getElementById('faceStatus').textContent = '未检测';
    document.getElementById('faceStatus').style.color = '#7f8c8d';
    document.getElementById('faceCount').textContent = '0';
    document.getElementById('emotionStatus').textContent = '-';
    document.getElementById('emotionBar').style.display = 'none';
    document.getElementById('fallStatus').textContent = '正常';
    document.getElementById('fallStatus').style.color = '#27ae60';
  });

  // 监听告警确认，重置跌倒状态
  EventBus.on(Events.ALERT_CONFIRM, () => {
    fallDetected = false;
    fallFrameCount = 0;
  });
  EventBus.on(Events.ALERT_DISMISS, () => {
    fallDetected = false;
    fallFrameCount = 0;
  });
}

async function loadModels() {
  if (modelsLoaded) return true;
  try {
    const MODEL_URL = 'https://justadudewhohacks.github.io/face-api.js/models';
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
    ]);
    modelsLoaded = true;
    return true;
  } catch (err) {
    showError('无法加载人脸检测模型，请检查网络连接');
    return false;
  }
}

async function detectLoop(video, overlay, ctx) {
  if (!isRunning) return;

  const now = performance.now();
  if (now - lastDetectTime >= DETECT_INTERVAL) {
    lastDetectTime = now;
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    try {
      const detections = await faceapi
        .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ scoreThreshold: 0.4 }))
        .withFaceLandmarks()
        .withFaceExpressions();

      if (detections && detections.length > 0) {
        const resized = faceapi.resizeResults(detections, {
          width: overlay.width, height: overlay.height,
        });
        faceapi.draw.drawDetections(ctx, resized);
        faceapi.draw.drawFaceLandmarks(ctx, resized);

        document.getElementById('faceStatus').textContent = '已检测';
        document.getElementById('faceStatus').style.color = '#27ae60';
        document.getElementById('faceCount').textContent = detections.length;

        const expressions = detections[0].expressions;
        updateEmotionUI(expressions);
        sampleEmotion(expressions);
        EventBus.emit(Events.VISION_EMOTION, { expressions, dominant: getDominantEmotion(expressions) });

        // 简易跌倒检测：基于人脸框位置突变（头位置急剧下降）
        checkFallFromFace(detections[0].detection.box);
      } else {
        document.getElementById('faceStatus').textContent = '未检测到';
        document.getElementById('faceStatus').style.color = '#e74c3c';
        document.getElementById('faceCount').textContent = '0';
        document.getElementById('emotionStatus').textContent = '-';
        document.getElementById('emotionBar').style.display = 'none';
        EventBus.emit(Events.VISION_FACE_LOST, {});
      }
    } catch (err) {
      // frame error, skip
    }
  }

  animationId = requestAnimationFrame(() => detectLoop(video, overlay, ctx));
}

function getDominantEmotion(expressions) {
  let max = 'neutral', maxVal = 0;
  for (const key in expressions) {
    if (expressions[key] > maxVal) { maxVal = expressions[key]; max = key; }
  }
  return { emotion: max, value: maxVal };
}

function updateEmotionUI(expressions) {
  const emotionMap = {
    happy: '😊 开心', sad: '😢 悲伤', angry: '😠 愤怒',
    fearful: '😨 恐惧', surprised: '😲 惊讶', neutral: '😐 中性', disgusted: '🤢 厌恶',
  };
  const dominant = getDominantEmotion(expressions);
  document.getElementById('emotionStatus').textContent = emotionMap[dominant.emotion] || dominant.emotion;
  document.getElementById('emotionBar').style.display = 'block';
  document.getElementById('happyBar').style.width = (expressions.happy * 100).toFixed(1) + '%';
  document.getElementById('happyValue').textContent = (expressions.happy * 100).toFixed(1) + '%';
  document.getElementById('sadBar').style.width = (expressions.sad * 100).toFixed(1) + '%';
  document.getElementById('sadValue').textContent = (expressions.sad * 100).toFixed(1) + '%';
  document.getElementById('neutralBar').style.width = (expressions.neutral * 100).toFixed(1) + '%';
  document.getElementById('neutralValue').textContent = (expressions.neutral * 100).toFixed(1) + '%';
}

function sampleEmotion(expressions) {
  const now = Date.now();
  if (now - lastEmotionSampleTime < EMOTION_SAMPLE_INTERVAL) return;
  lastEmotionSampleTime = now;

  let maxEmotion = 'neutral', maxValue = 0;
  for (const key in expressions) {
    if (key === 'neutral' || key === 'disgusted') continue;
    if (expressions[key] > maxValue) { maxValue = expressions[key]; maxEmotion = key; }
  }

  if (maxValue >= EMOTION_TRIGGER_THRESHOLD && maxEmotion !== 'neutral') {
    emotionBuffer.push({ emotion: maxEmotion, value: maxValue, time: now });
  }

  const cutoff = now - EMOTION_TRIGGER_DURATION;
  while (emotionBuffer.length > 0 && emotionBuffer[0].time < cutoff) emotionBuffer.shift();

  checkEmotionTrigger();
}

function checkEmotionTrigger() {
  if (emotionTriggered) return;
  if (Date.now() - lastTriggerTime < TRIGGER_COOLDOWN) return;
  if (emotionBuffer.length < 5) return;

  const counts = {};
  emotionBuffer.forEach(s => { counts[s.emotion] = (counts[s.emotion] || 0) + 1; });

  let dominant = null, maxCount = 0;
  for (const e in counts) {
    if (counts[e] > maxCount) { maxCount = counts[e]; dominant = e; }
  }

  if (maxCount / emotionBuffer.length < 0.6) return;

  emotionTriggered = true;
  lastTriggerTime = Date.now();
  emotionBuffer.length = 0;

  const prompts = emotionPrompts[dominant];
  if (!prompts || prompts.length === 0) { emotionTriggered = false; return; }

  const msg = prompts[Math.floor(Math.random() * prompts.length)];
  EventBus.emit(Events.CHAT_PROACTIVE, { emotion: dominant, message: msg });

  setTimeout(() => { emotionTriggered = false; }, TRIGGER_COOLDOWN);
}

// 简易跌倒检测：基于人脸框Y坐标突变
function checkFallFromFace(box) {
  const currentY = box.y + box.height / 2;
  const fallStatusEl = document.getElementById('fallStatus');

  if (lastPoseData !== null) {
    const deltaY = currentY - lastPoseData.y;
    // 如果人脸中心急剧下移（超过画面高度25%），且人脸仍然存在
    if (deltaY > overlay_height() * 0.25) {
      fallFrameCount++;
      if (fallFrameCount >= FALL_FRAMES_REQUIRED && !fallDetected) {
        fallDetected = true;
        fallStatusEl.textContent = '⚠️ 异常';
        fallStatusEl.style.color = '#e74c3c';
        EventBus.emit(Events.VISION_FALL, { confidence: 0.8, deltaY });
      }
    } else {
      fallFrameCount = Math.max(0, fallFrameCount - 1);
      if (!fallDetected) {
        fallStatusEl.textContent = '正常';
        fallStatusEl.style.color = '#27ae60';
      }
    }
  }

  lastPoseData = { y: currentY, time: Date.now() };
}

function overlay_height() {
  const overlay = document.getElementById('overlay');
  return overlay ? overlay.height : 480;
}

function showError(msg) {
  const el = document.getElementById('errorMsg');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 5000);
}
