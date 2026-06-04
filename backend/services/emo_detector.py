import torch
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
from torchvision import transforms
from typing import Dict, List, Optional
import time
import os


class EmoDetector:
    """EMO-AffectNet情绪检测器"""

    def __init__(self, model_path: str, device: str = "auto"):
        """
        初始化检测器

        Args:
            model_path: 模型文件路径
            device: 设备 (auto/cpu/cuda)
        """
        self.model_path = model_path

        # 设备选择
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # 加载模型
        self.model = None
        self._load_model()

        # MediaPipe人脸检测
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )

        # 图像预处理
        self.transform = transforms.Compose([
            transforms.PILToTensor(),
            transforms.Lambda(self._preprocess_input)
        ])

    def _load_model(self):
        """加载PyTorch模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        try:
            self.model = torch.jit.load(self.model_path, map_location=self.device)
            self.model.eval()
            print(f"[EMO] Model loaded on {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def _preprocess_input(self, x: torch.Tensor) -> torch.Tensor:
        """
        预处理输入图像

        Args:
            x: 输入tensor

        Returns:
            预处理后的tensor
        """
        x = x.to(torch.float32)
        x = torch.flip(x, dims=(0,))  # RGB -> BGR
        x[0, :, :] -= 91.4953
        x[1, :, :] -= 103.8827
        x[2, :, :] -= 131.0912
        return x

    def _detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        使用MediaPipe检测人脸

        Args:
            frame: 输入图像 (BGR格式)

        Returns:
            人脸列表，每个包含box坐标
        """
        # 转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        faces = []
        if results.detections:
            h, w = frame.shape[:2]
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                # 确保坐标在图像范围内
                x = max(0, x)
                y = max(0, y)
                width = min(w - x, width)
                height = min(h - y, height)

                faces.append({
                    "box": [x, y, width, height],
                    "confidence": detection.score[0]
                })

        return faces

    def _predict_emotion(self, face_img: np.ndarray) -> Dict[str, float]:
        """
        对人脸图像进行情绪推理

        Args:
            face_img: 人脸图像

        Returns:
            20种情绪的概率分布
        """
        # 转换为PIL Image并resize
        pil_img = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        pil_img = pil_img.resize((224, 224), Image.Resampling.NEAREST)

        # 预处理
        img_tensor = self.transform(pil_img)
        img_tensor = torch.unsqueeze(img_tensor, 0).to(self.device)

        # 推理
        with torch.no_grad():
            output = self.model(img_tensor)
            probabilities = torch.nn.functional.softmax(output, dim=1)
            probs = probabilities.cpu().numpy()[0]

        # 20种情绪名称（与模型输出对应）
        emotion_names = [
            "Neutral", "Happiness", "Sadness", "Surprise", "Fear",
            "Disgust", "Anger", "Contempt", "Confusion", "Embarrassment",
            "Pride", "Shame", "Relief", "Interest", "Boredom",
            "Anxiety", "Calm", "Excitement", "Disappointment", "Satisfaction"
        ]

        return {name: float(prob) for name, prob in zip(emotion_names, probs)}

    def detect_emotion(self, frame: np.ndarray) -> Optional[Dict]:
        """
        检测图像中的人脸和情绪

        Args:
            frame: 输入图像 (BGR格式)

        Returns:
            检测结果字典，包含faces列表
        """
        try:
            # 检测人脸
            faces = self._detect_faces(frame)

            result_faces = []
            for face in faces:
                x, y, w, h = face["box"]

                # 提取人脸区域
                face_img = frame[y:y+h, x:x+w]

                if face_img.size == 0:
                    continue

                # 预测情绪
                emotions = self._predict_emotion(face_img)

                result_faces.append({
                    "box": face["box"],
                    "emotions": emotions
                })

            return {
                "faces": result_faces,
                "timestamp": time.time()
            }

        except Exception as e:
            print(f"[EMO] Detection error: {e}")
            return None

    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_path": self.model_path,
            "device": self.device,
            "loaded": self.model is not None
        }

