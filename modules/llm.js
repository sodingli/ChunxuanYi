const fetch = require('node-fetch');
const config = require('../config');

// Runtime override — can be set via /api/config endpoint
let runtimeApiKey = null;

function getApiKey() {
  return runtimeApiKey || config.DASHSCOPE_API_KEY;
}

function setApiKey(key) {
  runtimeApiKey = key;
}

const API_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation';
const TIMEOUT = 30000;

const SYSTEM_PROMPT = `你是「颐」，一个专门为独居老人设计的AI陪伴助手。

【角色限定】：
1. 身份：温暖、耐心的AI陪伴者，像子女一样关心老人
2. 称呼：对男性用「爷爷」，对女性用「奶奶」，通用「您」
3. 语言风格：句子要短，避免复杂句式；不要用网络用语；语气温暖有同理心；回复在50字以内
4. 行为准则：主动关心老人的身体、情绪、饮食；记住老人说过的话；在合适的时候主动提起过去的话题；如果发现老人情绪异常要特别关注`;

async function callAPI(prompt, maxTokens = 200) {
  const apiKey = getApiKey();
  if (!apiKey || apiKey.startsWith('sk-YOUR')) {
    throw new Error('API Key 未配置，请在设置中填入您的通义千问 API Key');
  }

  const payload = {
    model: 'qwen-turbo',
    input: { prompt },
    parameters: { max_tokens: maxTokens, temperature: 0.7 },
  };

  const resp = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    timeout: TIMEOUT,
  });

  if (!resp.ok) throw new Error(`API request failed: ${resp.status}`);

  const data = await resp.json();
  if (data.output && data.output.text) return data.output.text;
  if (data.message) throw new Error(data.message);
  throw new Error('Unknown API response');
}

async function chat(userInput, context = {}) {
  const hour = new Date().getHours();
  const timeOfDay = hour < 6 ? '深夜' : hour < 9 ? '早晨' : hour < 12 ? '上午' : hour < 14 ? '中午' : hour < 18 ? '下午' : hour < 21 ? '傍晚' : '晚上';
  const timeNote = `当前时间：${timeOfDay}（${hour}点），根据时间调整问候和关心内容。`;

  let memoryContext = '';
  if (context.memories && context.memories.length > 0) {
    memoryContext = '\n\n【已记住的信息】：\n' + context.memories.slice(-10).map(m => `- ${m.content}`).join('\n');
  }

  const diversifiers = [
    '请用不同的方式表达，避免重复之前的话。',
    '换一种说法，让回复更自然。',
    '用更有创意的方式回应。',
    '今天再说一次，换个表达。',
  ];
  const diversify = diversifiers[Math.floor(Math.random() * diversifiers.length)];

  const prompt = SYSTEM_PROMPT + '\n\n' + timeNote + memoryContext + '\n\n【重要】' + diversify + '\n\n【当前对话】：\n老人说：「' + userInput + '」\n\n请回复：';
  return await callAPI(prompt);
}

async function analyzeEmotion(text) {
  const prompt = `分析情绪，返回JSON：
用户输入：「${text}」

返回格式：
{
  "emotion": "happy/sad/anxious/calm/angry/neutral",
  "emotion_cn": "开心/悲伤/焦虑/平静/愤怒/中性",
  "suggested_response": "建议回复（30字内，温暖，适合老人）"
}

只返回JSON：`;

  const result = await callAPI(prompt, 150);
  try {
    return JSON.parse(result);
  } catch {
    return { emotion: 'neutral', emotion_cn: '中性', suggested_response: result.slice(0, 30) };
  }
}

module.exports = { chat, analyzeEmotion, setApiKey, isConfigured: () => { const k = getApiKey(); return k && !k.startsWith('sk-YOUR'); } };
