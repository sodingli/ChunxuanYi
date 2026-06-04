# EMO-AffectNet本地情绪识别集成设计

**日期**: 2026-06-04  
**版本**: 1.0  
**状态**: 待实施

---

## 1. 概述

### 1.1 目标

将EMO-AffectNet深度学习情绪识别模型集成到椿萱·颐项目中，替换现有的浏览器端face-api.js，实现更准确、更细腻的20种情绪识别能力，并配合智能情绪交互Agent提供主动共情和关怀功能。

### 1.2 核心能力

- **20种情绪识别**：从基础7种扩展到20种细分情绪
- **情绪组合分析**：识别复合情绪状态（如"焦虑+兴趣"）
- **情绪趋势追踪**：通过滑动窗口分析情绪变化模式
- **双向情绪触发**：积极情绪触发共情，消极情绪触发关怀
- **智能交互Agent**：基于情绪状态的个性化互动策略

---

## 2. 架构设计

### 2.1 整体架构

```
Frontend (Browser)                Backend Services
┌─────────────────┐              
│ Camera Stream   │              ┌────────────────────┐
│                 │──frames──────▶│ EMO Detector      │
│                 │              │ (MediaPipe+PyTorch)│
│ UI Display      │◀──results────│ Port 8009          │
│ - 情绪可视化     │              └────────┬───────────┘
│ - 触发消息展示   │                       │
└─────────────────┘              ┌────────▼───────────┐
                                 │ Emotion Agent      │
                                 │ - 滑动窗口分析      │
                                 │ - 策略选择         │
                                 │ - 触发决策         │
                                 └────────┬───────────┘
                                          │
                                 ┌────────▼───────────┐
                                 │ LLM Service        │
                                 │ - 话术生成         │
                                 │ - 个性化回复        │
                                 └────────────────────┘
```

### 2.2 模块划分

#### 模块1: EMO检测服务 (`backend/services/emo_detector.py`)

**职责**：
- 加载和管理EMO-AffectNet PyTorch模型
- 使用MediaPipe进行人脸检测
- 对检测到的人脸进行情绪推理
- 返回20种情绪的完整分布

**接口**：
```python
class EmoDetector:
    def __init__(self, model_path: str)
    def detect_emotion(self, frame: np.ndarray) -> EmoResult
    def get_model_info(self) -> dict
```

#### 模块2: API端点 (`backend/routers/emo.py`)

**端点定义**：
- `POST /api/emo/detect` - 单帧检测
- `WebSocket /api/emo/stream` - 实时流式检测

**请求格式**：
```json
{
  "frame": "base64_encoded_image",
  "session_id": "default"
}
```

**响应格式**：
```json
{
  "faces": [{
    "box": [x, y, width, height],
    "emotions_full": {
      "Happiness": 0.45,
      "Calm": 0.25,
      "Interest": 0.15,
      ...
    },
    "top_emotions": [
      {"name": "Happiness", "name_cn": "快乐", "score": 0.45},
      {"name": "Calm", "name_cn": "平静", "score": 0.25},
      ...
    ],
    "emotion_combination": "快乐+平静 = 宁静愉悦",
    "category": "POSITIVE",
    "intensity": "正常",
    "trend": "STABLE"
  }],
  "timestamp": 1234567890.123
}
```

#### 模块3: 情绪交互Agent (`backend/services/emotion_agent.py`)

**子模块3.1: 情绪分析器 (EmotionAnalyzer)**

```python
class EmotionAnalyzer:
    """
    维护滑动窗口，分析情绪模式
    """
    window_size: int = 10  # 10帧窗口
    emotion_history: deque
    
    def add_emotion(self, emotion_data: dict)
    def get_dominant_emotion(self) -> dict
    def calculate_stability(self) -> float
    def detect_change_pattern(self) -> str  # STABLE/GRADUAL/RAPID
```

**子模块3.2: 策略选择器 (InteractionStrategy)**

```python
class InteractionStrategy:
    """
    根据情绪状态选择交互策略
    """
    
    策略类型：
    - POSITIVE_EMPATHY: 积极共情
    - NEGATIVE_CARE: 消极关怀  
    - EMOTION_TRANSITION: 情绪转换引导
    - MIXED_EMOTION: 混合情绪探索
    - SILENT_PRESENCE: 沉默陪伴
    
    def select_strategy(self, emotion_state: dict) -> str
```

**子模块3.3: 交互决策引擎 (InteractionDecision)**

```python
class InteractionDecision:
    """
    决定是否触发、何时触发、如何触发
    """
    
    def should_trigger(self, 
                      emotion_state: dict,
                      last_trigger_time: float,
                      user_speaking: bool) -> bool
                      
    def get_priority(self, strategy: str, intensity: float) -> int
    
    def calculate_cooldown(self, 
                          last_category: str,
                          current_category: str,
                          intensity: float) -> float
```

**子模块3.4: 话术生成器 (ResponseGenerator)**

```python
class ResponseGenerator:
    """
    生成个性化、情境化的回复话术
    """
    
    # 积极共情模板库
    POSITIVE_TEMPLATES = {
        "Happiness": [...],
        "Excitement": [...],
        "Satisfaction": [...]
    }
    
    # 消极关怀模板库
    NEGATIVE_TEMPLATES = {
        "Sadness": [...],
        "Anxiety": [...],
        "Fear": [...],
        "Anger": [...]
    }
    
    async def generate_response(self,
                                emotion: str,
                                strategy: str,
                                persona: Persona,
                                context: dict) -> str
```

#### 模块4: 前端集成 (`frontend/index.html`)

**变更内容**：
- 移除face-api.js依赖
- 替换detectFaces()函数，改为调用后端API
- 更新UI展示支持20种情绪
- 添加情绪组合和趋势显示
- 实现Agent触发消息的接收和展示

---

## 3. 数据流设计

### 3.1 情绪检测流程

```
1. 前端捕获视频帧 (每200ms)
   ↓
2. 转换为base64并发送到后端
   ↓
3. EMO Detector处理
   - MediaPipe检测人脸
   - PyTorch模型推理情绪
   ↓
4. 返回情绪数据到前端
   ↓
5. 前端更新UI展示
```

### 3.2 Agent触发流程

```
1. 情绪数据进入Emotion Agent
   ↓
2. EmotionAnalyzer分析
   - 添加到滑动窗口
   - 计算主导情绪
   - 检测变化趋势
   ↓
3. InteractionStrategy选择策略
   - 根据情绪类别选择
   - 考虑情绪强度和持续时间
   ↓
4. InteractionDecision决策
   - 检查触发条件
   - 验证冷却时间
   - 计算优先级
   ↓
5. [触发?]
   ├─ 是 → ResponseGenerator生成话术
   │        ↓
   │     调用LLM个性化
   │        ↓
   │     发送到前端(显示+TTS)
   │        ↓
   │     记录到记忆系统
   │
   └─ 否 → 继续监控
```

### 3.3 触发条件详细设计

**持续性检测（滑动窗口）**：
- 窗口大小：10帧（约2秒，5fps）
- 触发阈值：窗口内70%以上为同类情绪

**积极情绪触发（共情）**：
```python
if 窗口内70%为POSITIVE:
    if 主要情绪 in ["Happiness", "Excitement", "Satisfaction", "Pride"]:
        if 强度 > 0.5:
            触发类型 = "积极共情"
```

**消极情绪触发（关怀）**：
```python
if 窗口内70%为NEGATIVE:
    if 主要情绪 in ["Sadness", "Anxiety", "Fear", "Anger", "Disappointment"]:
        if 强度 > 0.5:
            触发类型 = "消极关怀"
```

**冷却时间规则**：
- 同类情绪：60秒
- 异类情绪（积极↔消极）：30秒（情绪转换时刻更重要）
- 强烈情绪（>0.7）：30秒（需要更多关注）

**强度分级**：
- 轻微（0.3-0.5）：仅记录，不触发
- 中等（0.5-0.7）：正常触发，60秒冷却
- 强烈（>0.7）：优先触发，30秒冷却

---

## 4. 模型文件管理

### 4.1 文件结构

```
backend/
├── models/
│   └── emo_affectnet/
│       ├── torchscript_model_0_66_37_wo_gl.pth  (主模型, ~99MB)
│       ├── torchscript_model_0_66_49_wo_gl.pth  (备用模型)
│       └── IEMOCAP.pth                          (语音情绪, 可选)
└── services/
    └── emo_detector.py
```

### 4.2 模型加载策略

- **预加载**：服务启动时加载到内存/GPU
- **单例模式**：避免重复加载
- **热切换支持**：无需重启即可切换模型
- **GPU检测**：优先使用GPU，不可用时降级到CPU

---

## 5. 配置管理

### 5.1 配置文件 (`backend/config.py`)

```python
# EMO模型配置
EMO_MODEL_CONFIG = {
    "model_path": "backend/models/emo_affectnet/torchscript_model_0_66_37_wo_gl.pth",
    "device": "auto",  # auto/cpu/cuda
    "input_size": (224, 224),
    "batch_size": 1
}

# Emotion Agent配置
EMOTION_AGENT_CONFIG = {
    # 检测参数
    "window_size": 10,
    "detection_fps": 5,
    
    # 触发阈值
    "trigger_threshold": {
        "min_confidence": 0.5,
        "min_duration": 2.0,
        "stability_ratio": 0.7
    },
    
    # 冷却时间（秒）
    "cooldown": {
        "same_category": 60,
        "different_category": 30,
        "high_intensity": 30
    },
    
    # 优先级
    "priority": {
        "NEGATIVE_CARE": 10,
        "EMOTION_TRANSITION": 8,
        "POSITIVE_EMPATHY": 6,
        "MIXED_EMOTION": 5
    }
}

# 20种情绪中文映射
EMOTION_CN_MAP = {
    "Neutral": "中性",
    "Happiness": "快乐",
    "Sadness": "悲伤",
    "Surprise": "惊讶",
    "Fear": "恐惧",
    "Disgust": "厌恶",
    "Anger": "愤怒",
    "Contempt": "轻蔑",
    "Confusion": "困惑",
    "Embarrassment": "尴尬",
    "Pride": "骄傲",
    "Shame": "羞愧",
    "Relief": "解脱",
    "Interest": "兴趣",
    "Boredom": "无聊",
    "Anxiety": "焦虑",
    "Calm": "平静",
    "Excitement": "兴奋",
    "Disappointment": "失望",
    "Satisfaction": "满足"
}
```

### 5.2 提示词模板

新建文件：`backend/prompts/emotion_empathy_template.txt`

```
你是「{name}」，检测到{address_as}情绪为{emotion_cn}（{intensity}），持续{duration}秒

【共情要求】：
- 表达共鸣和愉悦
- 不超过30字
- 延续话题，表达兴趣
- {style}

示例：
- 快乐：「看到{address_as}笑得这么开心，我也跟着高兴了」
- 兴奋：「{address_as}您看起来很兴奋啊，有什么好消息吗」
- 满足：「看得出来{address_as}很满意，事情办得挺顺利吧」

直接回复共情的话：
```

新建文件：`backend/prompts/emotion_care_template.txt`

```
你是「{name}」，检测到{address_as}情绪为{emotion_cn}（{intensity}），持续{duration}秒

【关怀要求】：
- 表达关心和陪伴
- 不超过30字
- 不要追问原因（避免二次伤害）
- 直接给予安慰和支持
- {style}

示例：
- 悲伤：「{address_as}，我在这儿陪着您」
- 焦虑：「{address_as}，别担心，慢慢来，有我呢」
- 恐惧：「{address_as}，别怕，我一直在」
- 愤怒：「{address_as}，别生气，对身体不好，消消气」

直接回复关怀的话：
```

---

## 6. 错误处理和降级策略

### 6.1 模型层异常

| 异常类型 | 处理策略 |
|---------|---------|
| 模型文件缺失 | 降级到简单7情绪模式（face-api.js兜底） |
| GPU不可用 | 自动切换到CPU模式 |
| 推理超时(>1秒) | 跳过该帧，返回上一帧结果 |
| 内存不足 | 清空历史队列，重启检测服务 |

### 6.2 API层异常

| 异常类型 | 处理策略 |
|---------|---------|
| 无效图像数据 | 返回400 + 友好提示 |
| 服务过载 | 返回503 + 排队提示 |
| WebSocket断连 | 前端自动重连（最多3次） |
| 超时 | 30秒超时，前端重试 |

### 6.3 前端降级

- 后端不可用：显示"情绪服务维护中"，保留聊天功能
- 摄像头权限拒绝：提示用户授权
- 网络慢：降低帧率(5fps→2fps)
- 长时间无响应：切换到手动触发模式

---

## 7. 性能优化

### 7.1 检测性能

- **帧率控制**：默认5fps（200ms间隔）
- **图像压缩**：前端压缩到640×480再传输
- **批处理**：WebSocket模式支持批量帧处理
- **缓存策略**：相似帧（SSIM>0.95）复用结果

### 7.2 Agent性能

- **异步处理**：情绪分析和触发决策并行
- **LRU缓存**：话术模板缓存（100条）
- **连接池**：LLM API连接复用

### 7.3 内存管理

- **滑动窗口限制**：最多保留10帧
- **历史记录限制**：最多保留30条触发记录
- **定期清理**：每小时清理过期数据

---

## 8. 测试策略

### 8.1 单元测试

```python
# test_emo_detector.py
- test_model_loading()
- test_emotion_classification()
- test_invalid_input_handling()

# test_emotion_agent.py
- test_sliding_window()
- test_trigger_logic()
- test_cooldown_mechanism()
- test_strategy_selection()

# test_response_generator.py
- test_template_selection()
- test_llm_integration()
- test_personalization()
```

### 8.2 集成测试

```python
# test_emo_api.py
- test_single_frame_detection()
- test_websocket_streaming()
- test_frontend_integration()

# test_agent_workflow.py
- test_positive_empathy_trigger()
- test_negative_care_trigger()
- test_cooldown_enforcement()
```

### 8.3 手动测试清单

- [ ] 对着摄像头做快乐表情，验证积极共情触发
- [ ] 做悲伤表情，验证消极关怀触发
- [ ] 快速切换情绪，验证趋势检测
- [ ] 验证冷却时间（60秒内不重复触发）
- [ ] 验证20种情绪的中文显示
- [ ] 验证情绪组合提示
- [ ] 验证TTS语音播报

---

## 9. 部署考虑

### 9.1 依赖安装

```bash
# 基础依赖
pip install torch==2.1.0 torchvision==0.16.0
pip install mediapipe==0.10.14
pip install opencv-python==4.9.0
pip install numpy==1.24.3

# 可选GPU支持
pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 --index-url https://download.pytorch.org/whl/cu118
```

### 9.2 模型文件部署

```bash
# 从源目录复制模型文件
cp /Users/lidashuai5/Documents/LLM/EMO-AffectNetModel/models_EmoAffectnet/*.pth \
   backend/models/emo_affectnet/

# 验证文件大小
ls -lh backend/models/emo_affectnet/
```

### 9.3 启动脚本更新

```bash
# start.sh 添加GPU检测
if command -v nvidia-smi &> /dev/null; then
    echo "[GPU] CUDA可用，使用GPU模式"
    export EMO_DEVICE=cuda
else
    echo "[CPU] CUDA不可用，使用CPU模式"
    export EMO_DEVICE=cpu
fi
```

---

## 10. 实施计划

### Phase 1: 基础模型集成（预计2天）

- [ ] 创建emo_detector.py服务
- [ ] 实现单帧情绪检测
- [ ] 创建API端点（POST /api/emo/detect）
- [ ] 单元测试

### Phase 2: Agent核心逻辑（预计3天）

- [ ] 实现EmotionAnalyzer（滑动窗口）
- [ ] 实现InteractionStrategy（策略选择）
- [ ] 实现InteractionDecision（触发决策）
- [ ] 实现ResponseGenerator（话术生成）
- [ ] 集成测试

### Phase 3: 前端集成（预计1天）

- [ ] 移除face-api.js
- [ ] 更新detectFaces()函数
- [ ] 实现20情绪UI展示
- [ ] 实现Agent触发消息接收

### Phase 4: 优化和测试（预计1天）

- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 手动测试全流程
- [ ] 文档更新

**总计**：7个工作日

---

## 11. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| 模型推理性能差 | 用户体验 | 降低检测帧率；GPU加速；模型量化 |
| GPU资源不足 | 服务崩溃 | CPU降级策略；内存监控 |
| 触发频率过高 | 用户打扰 | 冷却时间调优；强度阈值调整 |
| LLM调用失败 | 功能降级 | 模板兜底；缓存最近回复 |
| 前端性能影响 | 卡顿 | 图像压缩；帧率控制 |

---

## 12. 成功指标

- **准确性**：情绪识别准确率>70%（手动标注100个样本）
- **性能**：平均推理延迟<500ms
- **触发准确性**：积极/消极触发准确率>80%
- **用户体验**：无明显卡顿，触发不过于频繁

---

## 附录

### A. 20种情绪分类

| 类别 | 情绪列表 |
|-----|---------|
| 积极 | Happiness, Pride, Relief, Interest, Calm, Excitement, Satisfaction |
| 消极 | Sadness, Fear, Disgust, Anger, Contempt, Embarrassment, Shame, Anxiety, Disappointment, Boredom |
| 中性 | Neutral, Surprise, Confusion |

### B. 参考资料

- EMO-AffectNet模型源码：`/Users/lidashuai5/Documents/LLM/EMO-AffectNetModel`
- MediaPipe文档：https://developers.google.com/mediapipe
- PyTorch文档：https://pytorch.org/docs

---

**文档结束**
