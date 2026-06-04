#!/usr/bin/env node
const express = require('express');
const path = require('path');
const config = require('./config');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ============ API Routes ============

// 配置检查 & 设置
app.get('/api/config/status', (req, res) => {
  const llm = require('./modules/llm');
  res.json({ configured: llm.isConfigured() });
});

app.post('/api/config/key', (req, res) => {
  const { apiKey } = req.body;
  if (!apiKey || !apiKey.startsWith('sk-')) {
    return res.status(400).json({ error: '无效的 API Key 格式' });
  }
  require('./modules/llm').setApiKey(apiKey);
  res.json({ ok: true, message: 'API Key 已设置' });
});

function validateString(val, maxLen = 1000) {
  return typeof val === 'string' && val.length > 0 && val.length <= maxLen;
}

// LLM 对话
app.post('/api/chat', async (req, res) => {
  const { message, context } = req.body;
  if (!validateString(message)) return res.status(400).json({ error: 'message is required (max 1000 chars)' });

  try {
    const reply = await require('./modules/llm').chat(message, context);
    res.json({ reply });
  } catch (err) {
    console.error('Chat API error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// 情绪分析
app.post('/api/emotion', async (req, res) => {
  const { text } = req.body;
  if (!validateString(text)) return res.status(400).json({ error: 'text is required (max 1000 chars)' });

  try {
    const result = await require('./modules/llm').analyzeEmotion(text);
    res.json(result);
  } catch (err) {
    console.error('Emotion API error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// 告警
app.post('/api/alert', async (req, res) => {
  const { level, type, message } = req.body;
  if (!level || !type) return res.status(400).json({ error: 'level and type are required' });

  try {
    const result = await require('./modules/alert-service').send({ level, type, message });
    res.json(result);
  } catch (err) {
    console.error('Alert error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// 记忆 - CRUD
app.get('/api/memory', (req, res) => {
  const store = require('./modules/memory-store');
  res.json({ memories: store.getMemories(), reminders: store.getReminders(), health: store.getHealthReminders() });
});

app.post('/api/memory', (req, res) => {
  const { content, type } = req.body;
  if (!validateString(content)) return res.status(400).json({ error: 'content is required (max 1000 chars)' });
  const item = require('./modules/memory-store').addMemory(content, type);
  res.json(item);
});

app.post('/api/memory/reminder', (req, res) => {
  const { content, date } = req.body;
  if (!validateString(content) || !validateString(date, 20)) return res.status(400).json({ error: 'content and date are required' });
  const item = require('./modules/memory-store').addReminder(content, date);
  res.json(item);
});

app.post('/api/memory/health', (req, res) => {
  const { content, date } = req.body;
  if (!validateString(content) || !validateString(date, 20)) return res.status(400).json({ error: 'content and date are required' });
  const item = require('./modules/memory-store').addHealthReminder(content, date);
  res.json(item);
});

app.delete('/api/memory/reminder/:id', (req, res) => {
  require('./modules/memory-store').removeReminder(parseInt(req.params.id));
  res.json({ ok: true });
});

app.delete('/api/memory/health/:id', (req, res) => {
  require('./modules/memory-store').removeHealthReminder(parseInt(req.params.id));
  res.json({ ok: true });
});

// 日常陪伴
app.get('/api/companion/weather', async (req, res) => {
  try {
    const weather = await require('./modules/companion-service').getWeather(req.query.city || '北京');
    res.json(weather);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/companion/music', (req, res) => {
  const list = require('./modules/companion-service').getMusicList();
  res.json(list);
});

app.get('/api/companion/story/:id', (req, res) => {
  const list = require('./modules/companion-service').getStoryContent(parseInt(req.params.id));
  if (!list) return res.status(404).json({ error: 'not found' });
  res.json(list);
});

app.listen(PORT, () => {
  console.log(`椿萱·颐 模拟器已启动: http://localhost:${PORT}`);
});
