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

// 初始化所有模块
document.addEventListener('DOMContentLoaded', () => {
  drawDeviceFace();

  visionInit();
  voiceInit();
  chatInit();
  memoryInit();
  alertInit();
  companionInit();

  console.log('椿萱·颐 v2.0 已初始化');
});
