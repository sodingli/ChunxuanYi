const fetch = require('node-fetch');
const config = require('../config');

// ============ 天气 ============

async function getWeather(city = '北京') {
  // 如果配置了和风天气API，使用真实数据
  if (config.QWEATHER_KEY) {
    try {
      const resp = await fetch(
        `https://devapi.qweather.com/v7/weather/now?location=${encodeURIComponent(city)}&key=${config.QWEATHER_KEY}`,
        { timeout: 5000 }
      );
      const data = await resp.json();
      if (data.now) {
        return {
          city,
          temp: data.now.temp + '°C',
          text: data.now.text,
          wind: data.now.windDir + data.now.windScale + '级',
          humidity: data.now.humidity + '%',
        };
      }
    } catch (e) {
      console.error('Weather API error:', e.message);
    }
  }

  // 模拟数据
  return {
    city,
    temp: '22°C',
    text: '晴',
    wind: '微风',
    humidity: '45%',
    note: '模拟数据，配置QWEATHER_KEY后可获取真实天气',
  };
}

// ============ 音乐/故事 ============

const musicList = [
  { id: 1, title: '茉莉花', type: 'music', duration: '3:20' },
  { id: 2, title: '月亮代表我的心', type: 'music', duration: '4:05' },
  { id: 3, title: '在那遥远的地方', type: 'music', duration: '3:15' },
  { id: 4, title: '梁祝', type: 'music', duration: '5:30' },
  { id: 5, title: '二泉映月', type: 'music', duration: '6:45' },
];

const storyList = [
  { id: 101, title: '三只小猪', type: 'story', duration: '5:00' },
  { id: 102, title: '龟兔赛跑', type: 'story', duration: '4:30' },
  { id: 103, title: '愚公移山', type: 'story', duration: '6:00' },
  { id: 104, title: '孔融让梨', type: 'story', duration: '3:30' },
];

function getMusicList() {
  return { music: musicList, stories: storyList };
}

module.exports = { getWeather, getMusicList };
