import cv2
import math
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
import warnings
import os

warnings.simplefilter("ignore", UserWarning)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.environ.get("EMOTION_MODEL_DIR", os.path.join(BASE_DIR, "models"))
MODEL_PATH = os.path.join(MODEL_DIR, "FER_static_ResNet50_AffectNet.pt")
LSTM_MODEL_PATH = os.path.join(MODEL_DIR, "FER_dinamic_LSTM_Aff-Wild2.pt")

EMOTION_DICT = {
    0: 'neutral',
    1: 'happy',
    2: 'sad',
    3: 'surprised',
    4: 'fearful',
    5: 'disgusted',
    6: 'angry'
}

class Bottleneck(nn.Module):
    expansion = 4
    def __init__(self, in_channels, out_channels, i_downsample=None, stride=1):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, padding=0, bias=False)
        self.batch_norm1 = nn.BatchNorm2d(out_channels, eps=0.001, momentum=0.99)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding='same', bias=False)
        self.batch_norm2 = nn.BatchNorm2d(out_channels, eps=0.001, momentum=0.99)
        self.conv3 = nn.Conv2d(out_channels, out_channels * self.expansion, kernel_size=1, stride=1, padding=0, bias=False)
        self.batch_norm3 = nn.BatchNorm2d(out_channels * self.expansion, eps=0.001, momentum=0.99)
        self.i_downsample = i_downsample
        self.stride = stride
        self.relu = nn.ReLU()

    def forward(self, x):
        identity = x.clone()
        x = self.relu(self.batch_norm1(self.conv1(x)))
        x = self.relu(self.batch_norm2(self.conv2(x)))
        x = self.conv3(x)
        x = self.batch_norm3(x)
        if self.i_downsample is not None:
            identity = self.i_downsample(identity)
        x += identity
        x = self.relu(x)
        return x

class Conv2dSame(torch.nn.Conv2d):
    def calc_same_pad(self, i: int, k: int, s: int, d: int) -> int:
        return max((math.ceil(i / s) - 1) * s + (k - 1) * d + 1 - i, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        ih, iw = x.size()[-2:]
        pad_h = self.calc_same_pad(i=ih, k=self.kernel_size[0], s=self.stride[0], d=self.dilation[0])
        pad_w = self.calc_same_pad(i=iw, k=self.kernel_size[1], s=self.stride[1], d=self.dilation[1])
        if pad_h > 0 or pad_w > 0:
            x = F.pad(x, [pad_w // 2, pad_w - pad_w // 2, pad_h // 2, pad_h - pad_h // 2])
        return F.conv2d(x, self.weight, self.bias, self.stride, self.padding, self.dilation, self.groups)

class ResNet(nn.Module):
    def __init__(self, ResBlock, layer_list, num_classes, num_channels=3):
        super(ResNet, self).__init__()
        self.in_channels = 64
        self.conv_layer_s2_same = Conv2dSame(num_channels, 64, 7, stride=2, groups=1, bias=False)
        self.batch_norm1 = nn.BatchNorm2d(64, eps=0.001, momentum=0.99)
        self.relu = nn.ReLU()
        self.max_pool = nn.MaxPool2d(kernel_size=3, stride=2)
        self.layer1 = self._make_layer(ResBlock, layer_list[0], planes=64, stride=1)
        self.layer2 = self._make_layer(ResBlock, layer_list[1], planes=128, stride=2)
        self.layer3 = self._make_layer(ResBlock, layer_list[2], planes=256, stride=2)
        self.layer4 = self._make_layer(ResBlock, layer_list[3], planes=512, stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(512 * ResBlock.expansion, 512)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(512, num_classes)

    def extract_features(self, x):
        x = self.relu(self.batch_norm1(self.conv_layer_s2_same(x)))
        x = self.max_pool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = x.reshape(x.shape[0], -1)
        x = self.fc1(x)
        return x

    def forward(self, x):
        x = self.extract_features(x)
        x = self.relu1(x)
        x = self.fc2(x)
        return x

    def _make_layer(self, ResBlock, blocks, planes, stride=1):
        ii_downsample = None
        layers = []
        if stride != 1 or self.in_channels != planes * ResBlock.expansion:
            ii_downsample = nn.Sequential(
                nn.Conv2d(self.in_channels, planes * ResBlock.expansion, kernel_size=1, stride=stride, bias=False, padding=0),
                nn.BatchNorm2d(planes * ResBlock.expansion, eps=0.001, momentum=0.99)
            )
        layers.append(ResBlock(self.in_channels, planes, i_downsample=ii_downsample, stride=stride))
        self.in_channels = planes * ResBlock.expansion
        for i in range(blocks - 1):
            layers.append(ResBlock(self.in_channels, planes))
        return nn.Sequential(*layers)

def ResNet50(num_classes, channels=3):
    return ResNet(Bottleneck, [3, 4, 6, 3], num_classes, channels)

class LSTMPyTorch(nn.Module):
    def __init__(self):
        super(LSTMPyTorch, self).__init__()
        self.lstm1 = nn.LSTM(input_size=512, hidden_size=512, batch_first=True, bidirectional=False)
        self.lstm2 = nn.LSTM(input_size=512, hidden_size=256, batch_first=True, bidirectional=False)
        self.fc = nn.Linear(256, 7)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        x = self.fc(x[:, -1, :])
        x = self.softmax(x)
        return x


def pth_processing(pil_img):
    """ElenaRyumina 原版预处理：224x224 NEAREST + BGR均值减法"""
    w, h = pil_img.size
    if w > h:
        pil_img = pil_img.resize((int(w * 224 / h), 224), Image.NEAREST)
    else:
        pil_img = pil_img.resize((224, int(h * 224 / w)), Image.NEAREST)

    # 中心裁剪 224x224
    w, h = pil_img.size
    left = (w - 224) / 2
    top = (h - 224) / 2
    pil_img = pil_img.crop((left, top, left + 224, top + 224))

    x = transforms.PILToTensor()(pil_img).to(torch.float32)
    x = torch.flip(x, dims=(0,))  # RGB -> BGR
    x[0, :, :] -= 91.4953
    x[1, :, :] -= 103.8827
    x[2, :, :] -= 131.0912
    return torch.unsqueeze(x, 0)


class LocalEmotionDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        self.backbone_model = ResNet50(7, channels=3)
        self.backbone_model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu'))
        self.backbone_model.eval()

        self.lstm_model = LSTMPyTorch()
        self.lstm_model.load_state_dict(torch.load(LSTM_MODEL_PATH, map_location='cpu'))
        self.lstm_model.eval()

        self.lstm_features = []
        self.max_features = 10

    def detect_emotion(self, frame):
        if frame is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        if len(faces) > 0:
            x, y, w, h = faces[0]
            startX, startY = max(0, x), max(0, y)
            endX = min(frame.shape[1], x + w)
            endY = min(frame.shape[0], y + h)
            cur_face = rgb[startY:endY, startX:endX]
            if cur_face.size == 0:
                return None
            cur_face_pil = Image.fromarray(cur_face)
            cur_face_tensor = pth_processing(cur_face_pil)
            features = F.relu(self.backbone_model.extract_features(cur_face_tensor)).detach().numpy()

            if len(self.lstm_features) == 0:
                self.lstm_features = [features] * self.max_features
            else:
                self.lstm_features = self.lstm_features[1:] + [features]

            lstm_f = torch.from_numpy(np.vstack(self.lstm_features))
            lstm_f = torch.unsqueeze(lstm_f, 0)
            output = self.lstm_model(lstm_f).detach().numpy()

            emotion_idx = np.argmax(output)
            emotion = EMOTION_DICT[emotion_idx]
            confidence = output[0][emotion_idx]
            return {
                "emotion": emotion,
                "emotion_cn": self._get_emotion_chinese(emotion),
                "confidence": float(confidence),
                "timestamp": time.time()
            }
        return None

    def process_video_frame(self, frame):
        return self.detect_emotion(frame)

    def _get_emotion_chinese(self, emotion):
        emotion_map = {
            'neutral': '中性', 'happy': '开心', 'sad': '悲伤',
            'surprised': '惊讶', 'fearful': '恐惧', 'disgusted': '厌恶', 'angry': '愤怒'
        }
        return emotion_map.get(emotion, '中性')


local_emotion_detector = None
if os.path.exists(MODEL_PATH) and os.path.exists(LSTM_MODEL_PATH):
    try:
        local_emotion_detector = LocalEmotionDetector()
        print(f"本地情绪模型加载成功（{MODEL_DIR}）")
    except Exception as e:
        print(f"本地情绪模型加载失败: {e}")
else:
    print(f"本地情绪模型权重不存在，请确认 {MODEL_DIR} 下有模型文件")
