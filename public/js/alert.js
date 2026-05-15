// Alert 模块 - 分级告警 + 多通道通知
import { EventBus, Events } from './event-bus.js';

let activeAlert = null;

export function init() {
  // 监听跌倒事件 → 高级告警
  EventBus.on(Events.VISION_FALL, (data) => {
    triggerAlert('high', 'fall', '检测到老人可能跌倒，请立即确认！', data);
  });

  // 监听情绪低落 → 中级告警
  EventBus.on(Events.VISION_EMOTION, ({ dominant }) => {
    if (dominant.emotion === 'sad' && dominant.value > 0.7) {
      triggerAlert('medium', 'emotion_low', '老人情绪持续低落', { emotion: dominant.emotion, value: dominant.value });
    }
  });

  // 告警确认/误报按钮
  document.getElementById('alertConfirmBtn').addEventListener('click', () => {
    if (activeAlert) {
      confirmAlert(activeAlert.id);
    }
  });

  document.getElementById('alertDismissBtn').addEventListener('click', () => {
    if (activeAlert) {
      dismissAlert(activeAlert.id);
    }
  });
}

function triggerAlert(level, type, message, extra = {}) {
  activeAlert = { id: Date.now(), level, type, message, ...extra };

  // 显示告警面板
  const panel = document.getElementById('alertPanel');
  const content = document.getElementById('alertContent');
  panel.style.display = 'block';

  const levelText = { high: '🔴 高级', medium: '🟡 中级', low: '🟢 低级' };
  content.innerHTML = `<div class="level">${levelText[level] || level}</div><div>${message}</div>`;

  EventBus.emit(Events.ALERT_TRIGGER, activeAlert);

  // 通知后端
  fetch('/api/alert', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ level, type, message }),
  }).then(r => r.json()).then(data => {
    updateAlertLogUI();
  }).catch(() => {});
}

function confirmAlert(id) {
  const panel = document.getElementById('alertPanel');
  panel.style.display = 'none';
  activeAlert = null;
  EventBus.emit(Events.ALERT_CONFIRM, { id });

  fetch('/api/alert', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ level: 'low', type: 'alert_confirmed', message: '告警已确认' }),
  }).catch(() => {});
}

function dismissAlert(id) {
  const panel = document.getElementById('alertPanel');
  panel.style.display = 'none';
  activeAlert = null;
  EventBus.emit(Events.ALERT_DISMISS, { id });
}

async function updateAlertLogUI() {
  try {
    // 简易本地记录
    const list = document.getElementById('alertLog');
    if (!activeAlert) return;
    const levelClass = activeAlert.level;
    const time = new Date().toLocaleTimeString('zh-CN');
    list.innerHTML = `<div class="alert-log-item ${levelClass}"><div class="time">${time}</div><div class="level">${activeAlert.level.toUpperCase()}</div><div>${activeAlert.message}</div></div>` + list.innerHTML;
  } catch (e) {}
}
