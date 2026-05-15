const fetch = require('node-fetch');
const config = require('../config');

const API_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation';
const TIMEOUT = 30000;

const SYSTEM_PROMPT = `你是「颐」，一个专门为独居老人设计的AI陪伴助手。

【角色限定】：
1. 身份：温暖、耐心的AI陪伴者，像子女一样关心老人
2. 称呼：对男性用「爷爷」，对女性用「奶奶」，通用「您」
3. 语言风格：句子要短，避免复杂句式；不要用网络用语；语气温暖有同理心；回复在50字以内
4. 行为准则：主动关心老人的身体、情绪、饮食；记住老人说过的话；在合适的时候主动提起过去的话题；如果发现老人情绪异常要特别关注`;

async function callAPI(prompt, maxTokens = 200) {
  if (!config.DASHSCOPE_API_KEY || config.DASHSCOPE_API_KEY.startsWith('sk-YOUR')) {
    throw new Error('API Key 未配置，请编辑 config.js');
  }

  const payload = {
    model: 'qwen-turbo',
    input: { prompt },
    parameters: { max_tokens: maxTokens, temperature: 0.7 },
  };

  const resp = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.DASHSCOPE_API_KEY}`,
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
  let memoryContext = '';
  if (context.memories && context.memories.length > 0) {
    memoryContext = '\n\n【已记住的信息】：\n' + context.memories.slice(-10).map(m => `- ${m.content}`).join('\n');
  }

  const prompt = SYSTEM_PROMPT + memoryContext + '\n\n【当前对话】：\n老人说：「' + userInput + '」\n\n请回复：';
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

module.exports = { chat, analyzeEmotion };
