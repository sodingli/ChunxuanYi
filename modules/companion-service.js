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
  {
    id: 101, title: '三只小猪', type: 'story', duration: '5:00',
    content: '从前，有三只小猪离开妈妈，各自去建造自己的房子。老大偷懒，用稻草搭了一间草屋。老二也不太勤快，用木头建了一间木屋。只有老三最勤劳，用砖头砌了一间坚固的砖房。有一天，大灰狼来了。他来到老大的草屋前，深吸一口气，呼的一吹，草屋就倒了。老大赶紧跑到老二的木屋。大灰狼又来到木屋前，用力一吹，木屋也倒了。两只小猪吓得跑到老三的砖房里。大灰狼来到砖房前，使劲吹，可是砖房纹丝不动。他爬上屋顶想从烟囱进去，结果掉进了烧开的锅里，烫得嗷嗷叫，再也不敢来了。三只小猪从此明白，勤劳才能带来安全。',
  },
  {
    id: 102, title: '龟兔赛跑', type: 'story', duration: '4:30',
    content: '森林里，兔子总是嘲笑乌龟走得慢。一天，乌龟不服气，提出要和兔子赛跑。兔子哈哈大笑，说：你这么慢，怎么可能赢我？比赛开始了，兔子一下子就跑出去很远，回头看乌龟还在起点慢慢爬。兔子心想，我睡一觉再跑也来得及，就在树下睡着了。乌龟虽然走得慢，但一步也不停，一直往前走。等兔子醒来的时候，乌龟已经快到终点了。兔子拼命追赶，但已经来不及了，乌龟赢得了比赛。这个故事告诉我们，坚持到底就是胜利。',
  },
  {
    id: 103, title: '愚公移山', type: 'story', duration: '6:00',
    content: '很久很久以前，有一位老人叫愚公，他家门前有两座大山，挡住了出行的路。愚公下定决心，要把这两座山移走。他带着家人，每天挖山不停。有个叫智叟的老头笑话他说：你这么大年纪了，怎么可能搬走这两座大山？愚公说：我死了有儿子，儿子死了还有孙子，子子孙孙无穷尽，山又不会长高，怎么会搬不走呢？智叟无话可说。愚公的精神感动了天帝，天帝派了两个大力神，把两座大山背走了。从此，愚公家门前一片平坦。这个故事告诉我们，只要有决心，再大的困难也能克服。',
  },
  {
    id: 104, title: '孔融让梨', type: 'story', duration: '3:30',
    content: '古时候有个叫孔融的孩子，他四岁的时候就非常懂事。有一天，家里来了一筐梨，父亲让孩子们自己挑。孔融不挑大的，专门拿了一个最小的梨。父亲问他为什么拿小的，孔融说：我年纪小，应该吃小的，大的留给哥哥们吃。父亲又问：那你弟弟呢？孔融说：我比弟弟大，应该让着弟弟。父亲听了非常高兴，夸孔融是个懂事的好孩子。从此，孔融让梨的故事就流传了下来，告诉我们做人要懂得谦让。',
  },
];

function getMusicList() {
  return { music: musicList, stories: storyList };
}

function getStoryContent(id) {
  const story = storyList.find(s => s.id === id);
  return story || null;
}

module.exports = { getWeather, getMusicList, getStoryContent };
