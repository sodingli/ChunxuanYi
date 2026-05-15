// Memory 模块 - 记忆 + 提醒 + 健康
import { EventBus, Events } from './event-bus.js';

let reminders = [];
let healthReminders = [];

export function init() {
  loadReminders();
  checkDueReminders();
  setInterval(checkDueReminders, 60000);
}

export function addReminder() {
  const content = document.getElementById('reminderInput').value.trim();
  const date = document.getElementById('reminderDate').value;
  if (!content || !date) { alert('请填写提醒内容和日期'); return; }

  fetch('/api/memory/reminder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, date }),
  }).then(r => r.json()).then(item => {
    reminders.push(item);
    updateRemindersUI();
    document.getElementById('reminderInput').value = '';
    document.getElementById('reminderDate').value = '';
  }).catch(() => alert('添加失败'));
}

export function addHealthReminder() {
  const content = document.getElementById('healthInput').value.trim();
  const date = document.getElementById('healthDate').value;
  if (!content || !date) { alert('请填写健康提醒内容和日期'); return; }

  fetch('/api/memory/health', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, date }),
  }).then(r => r.json()).then(item => {
    healthReminders.push(item);
    updateHealthUI();
    document.getElementById('healthInput').value = '';
    document.getElementById('healthDate').value = '';
  }).catch(() => alert('添加失败'));
}

async function loadReminders() {
  try {
    const resp = await fetch('/api/memory');
    const data = await resp.json();
    if (data.reminders) { reminders = data.reminders; updateRemindersUI(); }
    if (data.health) { healthReminders = data.health; updateHealthUI(); }
  } catch (e) {}
}

function updateRemindersUI() {
  const list = document.getElementById('remindersList');
  if (reminders.length === 0) {
    list.innerHTML = '<div class="reminder-item"><div class="date">暂无提醒</div><div>点击下方添加提醒</div></div>';
    return;
  }
  list.innerHTML = reminders.map(r =>
    `<div class="reminder-item"><div class="date">${escapeHtml(r.date)}</div><div>${escapeHtml(r.content)}</div></div>`
  ).join('');
}

function updateHealthUI() {
  const list = document.getElementById('healthList');
  if (healthReminders.length === 0) {
    list.innerHTML = '<div class="reminder-item health"><div class="date">暂无健康提醒</div><div>点击下方添加</div></div>';
    return;
  }
  list.innerHTML = healthReminders.map(r =>
    `<div class="reminder-item health"><div class="date">${escapeHtml(r.date)}</div><div>${escapeHtml(r.content)}</div></div>`
  ).join('');
}

function checkDueReminders() {
  const today = new Date().toISOString().split('T')[0];
  const due = reminders.filter(r => !r.completed && r.date === today)
    .concat(healthReminders.filter(r => !r.completed && r.date === today));

  due.forEach(r => {
    EventBus.emit(Events.MEMORY_REMINDER_DUE, { reminder: r });
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
