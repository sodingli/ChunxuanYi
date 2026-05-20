// Companion 模块 - 日常陪伴：天气、音乐、用药提醒
import { EventBus, Events } from './event-bus.js';

let medicines = [];
let musicList = [];
let audioCtx = null;
let isPlaying = false;
let currentPlayId = null;

// 中国五声音阶旋律生成
const PENTATONIC = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25];

function playMelody(title) {
  if (isPlaying) stopMelody();
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  isPlaying = true;
  currentPlayId = 'music_' + Date.now();

  const melodies = {
    '茉莉花': [4,4,5,6,6,5,4,3,2,2,3,4,4,3,3,2, 4,4,5,6,6,5,4,3,2,2,3,4,3,2,2,1],
    '月亮代表我的心': [3,3,4,5,5,4,3,2,1,1,2,3,3,2,2,1, 3,3,4,5,5,4,3,4,5,5,6,5,4,3,2,1],
    '在那遥远的地方': [5,5,4,3,2,2,3,4,4,3,2,1,1,2,3,3, 5,5,6,5,4,3,2,3,4,4,3,2,1,1,2,1],
    '梁祝': [3,4,5,5,6,5,4,3,2,3,4,3,2,1,1,2, 3,4,5,6,5,4,3,2,3,4,3,2,1,2,3,1],
    '二泉映月': [2,3,4,4,3,2,1,1,2,3,2,1,2,3,4,3, 2,1,1,2,3,4,3,2,1,2,3,2,1,1,2,1],
  };

  const notes = melodies[title] || [3,4,5,4,3,2,1,2,3,4,5,6,5,4,3,2];
  const myId = currentPlayId;
  let noteIndex = 0;

  function playNote() {
    if (!isPlaying || currentPlayId !== myId) return;
    if (noteIndex >= notes.length * 2) { stopMelody(); return; }

    const idx = notes[noteIndex % notes.length];
    const freq = PENTATONIC[idx] || PENTATONIC[3];
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.45);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(audioCtx.currentTime);
    osc.stop(audioCtx.currentTime + 0.5);

    noteIndex++;
    setTimeout(playNote, 500);
  }

  playNote();
}

function stopMelody() {
  isPlaying = false;
  currentPlayId = null;
  if (audioCtx) { try { audioCtx.close(); } catch(e) {} audioCtx = null; }
  updateMusicListUI();
}

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
      updateMusicListUI();
    })
    .catch(() => {});
}

function updateMusicListUI() {
  const container = document.getElementById('musicList');
  if (musicList.length === 0) {
    container.innerHTML = '<div class="memory-item"><div class="label">暂无内容</div></div>';
    return;
  }
  container.innerHTML = musicList.map(item => {
    const playing = isPlaying && currentPlayId === item.id ? '⏸️' : '▶';
    return `<div class="music-item" onclick="YiApp.companion.play(${item.id})"><span>${item.type === 'music' ? '🎵' : '📖'} ${item.title}</span><span class="play-icon">${playing}</span></div>`;
  }).join('');
}

export function play(id) {
  // 如果正在播放同一个，则停止
  if (isPlaying && currentPlayId === id) {
    stopMelody();
    const msg = '已停止播放。';
    addChatMessage(msg, 'ai');
    return;
  }

  const item = musicList.find(m => m.id === id);
  if (!item) return;

  currentPlayId = id;

  if (item.type === 'music') {
    // 音乐：生成旋律 + TTS 介绍
    const msg = `正在为您播放《${item.title}》，希望您喜欢！`;
    addChatMessage(msg, 'ai');
    EventBus.emit(Events.CHAT_AI_MSG, { text: msg, speak: true });
    setTimeout(() => playMelody(item.title), 2000);
  } else {
    // 故事：从后端获取内容，TTS 朗读
    const intro = `好的，我来给您讲《${item.title}》的故事。`;
    addChatMessage(intro, 'ai');
    EventBus.emit(Events.CHAT_AI_MSG, { text: intro, speak: true });

    fetch(`/api/companion/story/${id}`)
      .then(r => r.json())
      .then(data => {
        if (data.content) {
          setTimeout(() => {
            addChatMessage(data.content, 'ai');
            EventBus.emit(Events.CHAT_AI_MSG, { text: data.content, speak: true });
          }, 3000);
        }
      })
      .catch(() => {
        addChatMessage('抱歉，故事加载失败了。', 'ai');
      });
  }

  updateMusicListUI();
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
