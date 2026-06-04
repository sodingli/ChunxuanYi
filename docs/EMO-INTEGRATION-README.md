# EMO-AffectNet情绪识别集成

## 概述

本项目集成了EMO-AffectNet深度学习模型，实现20种情绪识别和智能交互Agent。

## 功能特性

- **20种情绪识别**（vs face-api.js的7种）
- **情绪趋势分析**（滑动窗口10帧/2秒）
- **双向触发**：积极共情 + 消极关怀
- **智能冷却时间管理**：同类60秒，异类30秒，强烈30秒

## 安装部署

### 1. 依赖安装

```bash
pip install torch==2.1.0 torchvision==0.16.0 mediapipe==0.10.14 opencv-python==4.9.0 Pillow
```

### 2. 模型文件

确保模型文件位于：
```
backend/models/emo_affectnet/torchscript_model_0_66_37_wo_gl.pth
```

文件大小：约94MB

### 3. 启动服务

```bash
./start.sh --all
```

## API使用

### 检测端点

```bash
POST /api/emo/detect
```

**请求格式：**
```json
{
  "frame": "base64_encoded_image",
  "session_id": "default"
}
```

**响应格式：**
```json
{
  "faces": [{
    "box": [x, y, width, height],
    "primary_emotion": "Happiness",
    "emotion_cn": "快乐",
    "top_emotions": [
      {"name": "Happiness", "name_cn": "快乐", "score": 0.75},
      {"name": "Calm", "name_cn": "平静", "score": 0.15}
    ],
    "category": "POSITIVE",
    "intensity": "中等",
    "trend": "STABLE"
  }],
  "agent_message": "看到爷爷笑得这么开心，我也跟着高兴了",
  "timestamp": 1234567890.123
}
```

### 模型信息端点

```bash
GET /api/emo/model-info
```

**响应格式：**
```json
{
  "model_path": "backend/models/emo_affectnet/torchscript_model_0_66_37_wo_gl.pth",
  "device": "cpu",
  "loaded": true
}
```

## 配置

见`backend/config.py`中的：
- `EMO_MODEL_CONFIG` - 模型路径和设备配置
- `EMOTION_AGENT_CONFIG` - Agent触发阈值和冷却时间
- `EMOTION_CN_MAP` - 20种情绪中英文映射
- `EMOTION_CATEGORIES` - 情绪分类（POSITIVE/NEGATIVE/NEUTRAL）

## 测试

```bash
# 单元测试
pytest tests/test_emo_*.py -v

# 集成测试
pytest tests/test_emo_integration.py -v
```

## 性能

- **帧率**：5fps（200ms间隔）
- **平均延迟**：<500ms
- **GPU加速**：自动检测CUDA

## 20种情绪列表

| 类别 | 情绪 |
|-----|------|
| 积极 | Happiness(快乐), Pride(骄傲), Relief(解脱), Interest(兴趣), Calm(平静), Excitement(兴奋), Satisfaction(满足) |
| 消极 | Sadness(悲伤), Fear(恐惧), Disgust(厌恶), Anger(愤怒), Contempt(轻蔑), Embarrassment(尴尬), Shame(羞愧), Anxiety(焦虑), Disappointment(失望), Boredom(无聊) |
| 中性 | Neutral(中性), Surprise(惊讶), Confusion(困惑) |

## Emotion Agent

### 触发条件

**积极情绪（共情）：**
- 窗口内70%以上为POSITIVE
- 置信度 > 0.5
- 持续时间 > 2秒

**消极情绪（关怀）：**
- 窗口内70%以上为NEGATIVE
- 置信度 > 0.5
- 持续时间 > 2秒

### 策略类型

- `POSITIVE_EMPATHY` - 积极共情
- `NEGATIVE_CARE` - 消极关怀
- `EMOTION_TRANSITION` - 情绪转换引导
- `MIXED_EMOTION` - 混合情绪探索
- `SILENT_PRESENCE` - 沉默陪伴

### 冷却时间

- 同类情绪：60秒
- 异类情绪：30秒
- 强烈情绪（>0.7）：30秒

## 架构

```
Frontend → EMO API → EmoDetector (MediaPipe + PyTorch)
                  ↓
              EmotionAnalyzer (滑动窗口)
                  ↓
              InteractionStrategy (策略选择)
                  ↓
              InteractionDecision (触发决策)
                  ↓
              ResponseGenerator (话术生成)
                  ↓
              Frontend (显示 + TTS)
```

## 故障排除

### 模型加载失败
- 检查模型文件路径
- 确认文件大小约94MB
- 查看控制台日志

### GPU不可用
- 系统会自动降级到CPU模式
- 检查PyTorch CUDA安装

### API超时
- 降低前端请求帧率
- 检查后端资源占用

## 参考

- [EMO-AffectNet Model Source](https://github.com/face-analysis/emo-affectnet)
- [MediaPipe Documentation](https://developers.google.com/mediapipe)
- [PyTorch Documentation](https://pytorch.org/docs)
