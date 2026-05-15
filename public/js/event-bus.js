// 前端事件总线 - 模块间解耦通信
const EventBus = {
  _handlers: {},

  on(event, handler) {
    if (!this._handlers[event]) this._handlers[event] = [];
    this._handlers[event].push(handler);
    return () => this.off(event, handler);
  },

  off(event, handler) {
    if (!this._handlers[event]) return;
    this._handlers[event] = this._handlers[event].filter(h => h !== handler);
  },

  emit(event, data) {
    if (!this._handlers[event]) return;
    this._handlers[event].forEach(h => {
      try { h(data); } catch (e) { console.error(`EventBus error [${event}]:`, e); }
    });
  },

  once(event, handler) {
    const wrapper = (data) => { this.off(event, wrapper); handler(data); };
    this.on(event, wrapper);
  },
};

// 标准事件定义
const Events = {
  // Vision 模块
  VISION_FACE_DETECTED: 'vision:faceDetected',
  VISION_FACE_LOST: 'vision:faceLost',
  VISION_EMOTION: 'vision:emotion',
  VISION_FALL: 'vision:fall',

  // Voice 模块
  VOICE_TRANSCRIPT: 'voice:transcript',
  VOICE_LISTENING_START: 'voice:listeningStart',
  VOICE_LISTENING_END: 'voice:listeningEnd',
  VOICE_SPEAKING_START: 'voice:speakingStart',
  VOICE_SPEAKING_END: 'voice:speakingEnd',
  VOICE_INTERRUPT: 'voice:interrupt',
  VOICE_WAKE: 'voice:wake',

  // Chat 模块
  CHAT_USER_MSG: 'chat:userMsg',
  CHAT_AI_MSG: 'chat:aiMsg',
  CHAT_PROACTIVE: 'chat:proactive',

  // Memory 模块
  MEMORY_ADD: 'memory:add',
  MEMORY_REMINDER_DUE: 'memory:reminderDue',

  // Alert 模块
  ALERT_TRIGGER: 'alert:trigger',
  ALERT_DISMISS: 'alert:dismiss',
  ALERT_CONFIRM: 'alert:confirm',

  // Companion 模块
  COMPANION_WEATHER: 'companion:weather',
  COMPANION_MUSIC: 'companion:music',
  COMPANION_MEDICINE: 'companion:medicine',
};

export { EventBus, Events };
