const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '..', 'data', 'store.json');

function readStore() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
    }
  } catch (e) {
    console.error('Failed to read store:', e.message);
  }
  return { memories: [], reminders: [], healthReminders: [], emotionRecords: [] };
}

function writeStore(store) {
  try {
    fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
    fs.writeFileSync(DATA_FILE, JSON.stringify(store, null, 2), 'utf-8');
  } catch (e) {
    console.error('Failed to write store:', e.message);
  }
}

function addMemory(content, type = 'conversation') {
  const store = readStore();
  const item = { id: Date.now(), content, type, timestamp: new Date().toISOString() };
  store.memories.push(item);
  if (store.memories.length > 100) store.memories = store.memories.slice(-100);
  writeStore(store);
  return item;
}

function getMemories() {
  return readStore().memories;
}

function addReminder(content, date) {
  const store = readStore();
  const item = { id: Date.now(), content, date, completed: false };
  store.reminders.push(item);
  writeStore(store);
  return item;
}

function getReminders() {
  return readStore().reminders;
}

function removeReminder(id) {
  const store = readStore();
  store.reminders = store.reminders.filter(r => r.id !== id);
  writeStore(store);
}

function addHealthReminder(content, date) {
  const store = readStore();
  const item = { id: Date.now(), content, date, completed: false };
  store.healthReminders.push(item);
  writeStore(store);
  return item;
}

function getHealthReminders() {
  return readStore().healthReminders;
}

function removeHealthReminder(id) {
  const store = readStore();
  store.healthReminders = store.healthReminders.filter(r => r.id !== id);
  writeStore(store);
}

function getDueReminders() {
  const today = new Date().toISOString().split('T')[0];
  const store = readStore();
  const due = store.reminders.filter(r => !r.completed && r.date === today)
    .concat(store.healthReminders.filter(r => !r.completed && r.date === today));
  return due;
}

function addEmotionRecord(emotion, value) {
  const store = readStore();
  store.emotionRecords.push({
    id: Date.now(),
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().split(' ')[0],
    emotion, value,
  });
  if (store.emotionRecords.length > 500) store.emotionRecords = store.emotionRecords.slice(-500);
  writeStore(store);
}

function getEmotionRecords() {
  return readStore().emotionRecords;
}

module.exports = {
  addMemory, getMemories,
  addReminder, getReminders, removeReminder,
  addHealthReminder, getHealthReminders, removeHealthReminder,
  getDueReminders,
  addEmotionRecord, getEmotionRecords,
};
