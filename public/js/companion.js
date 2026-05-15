// Companion 模块 - 日常陪伴：天气、音乐、用药提醒
import { EventBus, Events } from './event-bus.js';

let medicines = [];
let musicList = [];

export function init() {
  refreshWeather();
  loadMusic();
  loadMedicines();
  setInterval(checkMedicineReminders, 30000);
}

export function refreshWeather() {
  fetch('/api/companion/weather')
    .then(r => r.json())
    .then(data => {
      const container = document.getElementById('weatherInfo');
      if (data.error) {
        container.innerHTML = `<p style="color:#e74c3c;">${data.error}</p>`;
        return;
      }
      container.innerHTML = `
        <div class="temp">${data.temp}</div>
        <div>${data.city} · ${data.text}</div>
        <div class="detail">${data.wind} | 湿度 ${data.humidity}</div>
        ${data.note ? '<div class="detail" style="color:#ffc107;">' + data.note + '</div>' : ''}
      `;
    })
    .catch(() => {
      document.getElementById('weatherInfo').innerHTML = '<p style="color:#7f8c8d;">天气服务暂时不可用</p>';
    });
}

function loadMusic() {
  fetch('/api/companion/music')
    .then(r => r.json())
    .then(data => {
      musicList = [...(data.music || []), ...(data.stories || [])];
      const container = document.getElementById('musicList');
      if (musicList.length === 0) {
        container.innerHTML = '<div class="memory-item"><div class="label">暂无内容</div></div>';
        return;
      }
      container.innerHTML = musicList.map(item =>
        `<div class="music-item" onclick="YiApp.companion.play(${item.id})"><span>${item.type === 'music' ? '🎵' : '📖'} ${item.title}</span><span class="play-icon">▶</span></div>`
      ).join('');
    })
    .catch(() => {});
}

export function play(id) {
  const item = musicList.find(m => m.id === id);
  if (!item) return;

  // 模拟播放：通过TTS播报
  const msg = item.type === 'music'
    ? `正在为您播放《${item.title}》，希望您喜欢！`
    : `好的，我来给您讲《${item.title}》的故事。`;
  EventBus.emit(Events.CHAT_AI_MSG, { text: msg, speak: true });
  addChatMessage(msg, 'ai');
}

function addChatMessage(text, sender) {
  const chatMessages = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message message-' + sender;
  div.innerHTML = `<div class="sender">${sender === 'user' ? '您' : '颐'}</div><div class="bubble">${text}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

export function addMedicine() {
  const name = document.getElementById('medicineInput').value.trim();
  const time = document.getElementById('medicineTime').value;
  if (!name || !time) { alert('请填写药品名称和时间'); return; }

  medicines.push({ id: Date.now(), name, time, taken: false });
  updateMedicinesUI();
  document.getElementById('medicineInput').value = '';
  document.getElementById('medicineTime').value = '';

  // 保存到localStorage
  localStorage.setItem('yi_medicines', JSON.stringify(medicines));
}

function loadMedicines() {
  try {
    const saved = localStorage.getItem('yi_medicines');
    if (saved) { medicines = JSON.parse(saved); updateMedicinesUI(); }
  } catch (e) {}
}

function updateMedicinesUI() {
  const list = document.getElementById('medicineList');
  if (medicines.length === 0) {
    list.innerHTML = '<div class="reminder-item"><div class="date">暂无用药提醒</div></div>';
    return;
  }
  list.innerHTML = medicines.map(m =>
    `<div class="reminder-item health"><div class="date">${m.time}</div><div>${escapeHtml(m.name)}${m.taken ? ' ✅' : ''}</div></div>`
  ).join('');
}

function checkMedicineReminders() {
  const now = new Date();
  const currentTime = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

  medicines.forEach(m => {
    if (!m.taken && m.time === currentTime) {
      const msg = `爷爷/奶奶，该吃药了！记得吃${m.name}哦。`;
      EventBus.emit(Events.COMPANION_MEDICINE, { medicine: m });
      EventBus.emit(Events.CHAT_PROACTIVE, { emotion: 'neutral', message: msg });
      addChatMessage(msg, 'ai');
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
