// 告警服务 - 分级告警 + 多通道通知
const LEVELS = { high: 3, medium: 2, low: 1 };

const CHANNELS = {
  high: ['sms', 'wechat', 'app'],
  medium: ['wechat', 'app'],
  low: ['app'],
};

// 告警记录（内存）
let alertLog = [];

function send({ level, type, message }) {
  if (!LEVELS[level]) return { ok: false, error: 'Invalid level: ' + level };

  const alert = {
    id: Date.now(),
    level,
    type,
    message: message || getDefaultMessage(type),
    channels: CHANNELS[level] || ['app'],
    timestamp: new Date().toISOString(),
    status: 'sent',
  };

  alertLog.push(alert);
  if (alertLog.length > 200) alertLog = alertLog.slice(-200);

  // 模拟器阶段：只记录日志，实际推送需要接入短信/微信API
  console.log(`[ALERT ${level.toUpperCase()}] ${alert.type}: ${alert.message} → ${alert.channels.join(', ')}`);

  return { ok: true, alert };
}

function getDefaultMessage(type) {
  const messages = {
    fall: '检测到老人可能跌倒，请立即确认！',
    sos_voice: '老人发出语音求助信号！',
    inactivity: '老人长时间未活动，请关注',
    emotion_low: '老人情绪持续低落，建议关心',
    device_error: '设备异常，请检查',
  };
  return messages[type] || '需要关注';
}

function getLog(limit = 50) {
  return alertLog.slice(-limit);
}

function dismiss(id) {
  const alert = alertLog.find(a => a.id === id);
  if (alert) alert.status = 'dismissed';
  return alert;
}

module.exports = { send, getLog, dismiss };
