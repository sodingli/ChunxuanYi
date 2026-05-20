// App 主入口 - 初始化所有模块
import { EventBus, Events } from './event-bus.js';
import { init as visionInit } from './vision.js';
import { init as voiceInit } from './voice.js';
import { init as chatInit } from './chat.js';
import { init as memoryInit, addReminder, addHealthReminder } from './memory.js';
import { init as alertInit } from './alert.js';
import { init as companionInit, refreshWeather, play as playMusic, addMedicine } from './companion.js';

// 全局暴露（供HTML内联事件使用）
window.YiApp = {
  memory: { addReminder, addHealthReminder },
  companion: { refreshWeather, play: playMusic, addMedicine },
};

// Tab 切换
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(btn.dataset.tab + 'Tab').classList.add('active');
  });
});

// 设备表情（Canvas绘制）
function drawDeviceFace() {
  const canvas = document.getElementById('faceCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2, r = Math.min(w, h) * 0.35;

  ctx.clearRect(0, 0, w, h);

  // 脸
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = '#667eea';
  ctx.fill();
  ctx.strokeStyle = '#5a6fd6';
  ctx.lineWidth = 2;
  ctx.stroke();

  // 眼睛
  ctx.fillStyle = 'white';
  ctx.beginPath(); ctx.arc(cx - r * 0.3, cy - r * 0.15, r * 0.12, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(cx + r * 0.3, cy - r * 0.15, r * 0.12, 0, Math.PI * 2); ctx.fill();

  // 瞳孔
  ctx.fillStyle = '#2c3e50';
  ctx.beginPath(); ctx.arc(cx - r * 0.3, cy - r * 0.15, r * 0.06, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(cx + r * 0.3, cy - r * 0.15, r * 0.06, 0, Math.PI * 2); ctx.fill();

  // 微笑
  ctx.beginPath();
  ctx.arc(cx, cy + r * 0.05, r * 0.35, 0.1 * Math.PI, 0.9 * Math.PI);
  ctx.strokeStyle = 'white';
  ctx.lineWidth = 2.5;
  ctx.stroke();
}

// 设置弹窗
const settingsModal = document.getElementById('settingsModal');
const settingsApiKey = document.getElementById('settingsApiKey');
const settingsMsg = document.getElementById('settingsMsg');

document.getElementById('settingsBtn').addEventListener('click', () => {
  settingsModal.style.display = 'flex';
  settingsMsg.style.display = 'none';
  fetch('/api/config/status').then(r => r.json()).then(d => {
    if (d.configured) settingsMsg.style.display = 'none';
  });
});

document.getElementById('settingsCloseBtn').addEventListener('click', () => {
  settingsModal.style.display = 'none';
});

settingsModal.addEventListener('click', (e) => {
  if (e.target === settingsModal) settingsModal.style.display = 'none';
});

document.getElementById('settingsSaveBtn').addEventListener('click', () => {
  const key = settingsApiKey.value.trim();
  if (!key) { settingsMsg.textContent = '请输入 API Key'; settingsMsg.style.color = '#e74c3c'; settingsMsg.style.display = 'block'; return; }

  fetch('/api/config/key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ apiKey: key }),
  }).then(r => r.json()).then(d => {
    if (d.ok) {
      settingsMsg.textContent = '✓ API Key 已保存，可以开始对话了！';
      settingsMsg.style.color = '#27ae60';
      settingsMsg.style.display = 'block';
      setTimeout(() => settingsModal.style.display = 'none', 1500);
    } else {
      settingsMsg.textContent = d.error || '保存失败';
      settingsMsg.style.color = '#e74c3c';
      settingsMsg.style.display = 'block';
    }
  }).catch(() => {
    settingsMsg.textContent = '网络错误';
    settingsMsg.style.color = '#e74c3c';
    settingsMsg.style.display = 'block';
  });
});

// 初始化所有模块
document.addEventListener('DOMContentLoaded', () => {
  drawDeviceFace();

  // 检查 API Key 配置状态
  fetch('/api/config/status').then(r => r.json()).then(d => {
    if (!d.configured) settingsModal.style.display = 'flex';
  });

  visionInit();
  voiceInit();
  chatInit();
  memoryInit();
  alertInit();
  companionInit();

  // 延迟朗读初始问候语（等待 TTS 解锁和用户交互）
  const greetText = '爷爷奶奶您好！我是颐，会记住咱们聊过的话，也会提醒您重要的事情。有什么我可以帮您的吗？';
  const greetOnce = () => {
    EventBus.emit(Events.CHAT_AI_MSG, { text: greetText, speak: true });
    document.removeEventListener('click', greetOnce);
    document.removeEventListener('keydown', greetOnce);
  };
  document.addEventListener('click', greetOnce, { once: true });
  document.addEventListener('keydown', greetOnce, { once: true });

  console.log('椿萱·颐 v2.0 已初始化');
});
