// Chat 模块 - LLM对话 + 情绪触发
import { EventBus, Events } from './event-bus.js';

let memories = [];

export function init() {
  const sendBtn = document.getElementById('sendBtn');
  const messageInput = document.getElementById('messageInput');

  sendBtn.addEventListener('click', sendMessage);
  messageInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

  // 语音输入完成后发送
  EventBus.on(Events.VOICE_TRANSCRIPT, ({ text }) => {
    document.getElementById('messageInput').value = text;
    sendMessage();
  });

  // 情绪触发的主动聊天
  EventBus.on(Events.CHAT_PROACTIVE, ({ emotion, message }) => {
    addMessage(message, 'ai');
    addMemory('颐主动关怀(' + emotion + '): ' + message, 'proactive');
  });

  // 跌倒触发紧急对话
  EventBus.on(Events.VISION_FALL, ({ confidence }) => {
    addMessage('爷爷/奶奶！您还好吗？我检测到您可能摔倒了，请回应我！如果需要帮助，我会立即通知家人。', 'ai');
    addMemory('跌倒检测触发，置信度: ' + (confidence * 100).toFixed(0) + '%', 'alert');
  });

  // 加载记忆
  loadMemories();
}

async function sendMessage() {
  const messageInput = document.getElementById('messageInput');
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = '';

  addMessage(text, 'user');
  addMessage('正在思考...', 'ai', true);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, context: { memories } }),
    });

    const data = await resp.json();
    removeTempMessage();

    if (data.error) {
      addMessage('抱歉，出了点问题：' + data.error, 'ai');
    } else {
      addMessage(data.reply, 'ai');
      EventBus.emit(Events.CHAT_AI_MSG, { text: data.reply, speak: true });
      addMemory('用户说: ' + text, 'conversation');
      addMemory('颐回复: ' + data.reply, 'conversation');
    }
  } catch (err) {
    removeTempMessage();
    addMessage('抱歉，网络好像不太通，稍后再试试吧。', 'ai');
  }
}

function addMessage(text, sender, isTemp = false) {
  const chatMessages = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message message-' + sender;
  const name = sender === 'user' ? '您' : '颐';
  div.innerHTML = `<div class="sender">${name}</div><div class="bubble">${escapeHtml(text)}</div>`;
  if (isTemp) div.id = 'tempMessage';
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTempMessage() {
  const el = document.getElementById('tempMessage');
  if (el) el.remove();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function addMemory(content, type = 'conversation') {
  const item = { id: Date.now(), content, type, timestamp: new Date().toISOString() };
  memories.push(item);
  if (memories.length > 50) memories = memories.slice(-50);

  // 同步到后端
  fetch('/api/memory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, type }),
  }).catch(() => {});

  EventBus.emit(Events.MEMORY_ADD, { item });
  updateMemoriesUI();
}

function updateMemoriesUI() {
  const list = document.getElementById('memoriesList');
  if (memories.length === 0) {
    list.innerHTML = '<div class="memory-item"><div class="label">暂无记忆</div><div>开始对话后，我会记住重要信息</div></div>';
    return;
  }
  list.innerHTML = memories.slice(-15).map(m =>
    `<div class="memory-item"><div class="label">${m.type} - ${new Date(m.timestamp).toLocaleDateString('zh-CN')}</div><div>${escapeHtml(m.content)}</div></div>`
  ).join('');
}

async function loadMemories() {
  try {
    const resp = await fetch('/api/memory');
    const data = await resp.json();
    if (data.memories) {
      memories = data.memories;
      updateMemoriesUI();
    }
  } catch (e) {}
}
