import torch
import torch.nn as nn
from pathlib import Path
import json
from loguru import logger
from typing import Dict, Optional

# 导入我们的数据结构
from ..schemas.diagnosis import PredictionResult
# 导入需要用到的模型结构
from torchvision.models import efficientnet_b0, efficientnet_b2, convnext_tiny

class DiseaseClassifier:
    def __init__(self, model_path: Path, labels_path: Path, architecture: str = 'b0'):
        """
        初始化分类器，加载自研模型。
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"DiseaseClassifier正在使用设备: {self.device}")
        
        try:
            # 1. 加载标签文件
            with open(labels_path, 'r', encoding='utf-8') as f:
                # 将json的key从字符串 '0', '1'... 转为整数 0, 1...
                self.labels = {int(k): v for k, v in json.load(f).items()}
            self.num_classes = len(self.labels)
            # 创建一个反向映射，便于 get_class_index 函数调用，提高效率
            self.class_to_idx = {name: idx for idx, name in self.labels.items()}
            print(f"从标签文件加载了 {self.num_classes} 个类别。")

            # 2. 根据指定的架构，构建一个“空白”的模型结构
            print(f"正在构建一个全新的 '{architecture}' 模型结构...")
            if architecture == 'b0':
                self.model = efficientnet_b0(weights='IMAGENET1K_V1', num_classes=self.num_classes)
            elif architecture == 'b2':
                self.model = efficientnet_b2(weights=None, num_classes=self.num_classes)
            elif architecture == 'convnext_tiny':
                self.model = convnext_tiny(weights=None, num_classes=self.num_classes)
            else:
                raise ValueError(f"不支持的模型架构: '{architecture}'。请选择 'b0', 'b2', 或 'convnext_tiny'。")

            # 3. 加载你亲手训练的权重
            print(f"正在加载你的自研模型权重从: {model_path}")
            # 使用 weights_only=True 是更安全和推荐的做法
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
            
            self.model.to(self.device)
            self.model.eval() # 切换到评估模式

        except Exception as e:
            raise RuntimeError(f"加载自研模型时出错: {e}")

    def predict(self, image_tensor) -> PredictionResult:
        """
        执行预测，只返回最终的 PredictionResult 对象。
        """
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            confidence_tensor, predicted_idx_tensor = torch.max(probabilities, 0)
            
            top_prediction = PredictionResult(
                disease=self.labels.get(predicted_idx_tensor.item(), "未知病害"),
                confidence=confidence_tensor.item()
            )
            
            # --- 将 Top-k 概率分布的打印移到这里，保持 predict 函数的纯粹性 ---
            k = min(self.num_classes, 5)
            topk_prob, topk_indices = torch.topk(probabilities, k)
            
            logger.info("--- 概率分布 (Top {}) ---", k)
            for i in range(topk_prob.size(0)):
                idx = topk_indices[i].item()
                label = self.labels.get(idx, f"未知类别_{idx}")
                prob = topk_prob[i].item()
                logger.info("  - {:<40}: {:.2%}", label, prob) # 使用loguru的格式化，更美观
            logger.info("-----------------------------")
            
            return top_prediction

    def get_class_index(self, class_name: str) -> Optional[int]:
        """根据类别名称，高效地反向查找它对应的数字索引。"""
        return self.class_to_idx.get(class_name)

# --- 全局实例初始化 (请确保这里的配置与你的模型匹配) ---

# 获取项目根目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- ↓↓↓ 关键修复：使用你真实的、训练好的文件名！↓↓↓ ---
MODEL_FILENAME = "FINAL_PEPPER_MODEL_b0.pth"
LABELS_FILENAME = "final_pepper_labels.json"
MODEL_ARCH = "b0" # 这个模型是 'b0' 架构
# --- ↑↑↑ 修复结束 ↑↑↑ ---

MODEL_PATH = BASE_DIR / "models_store" / MODEL_FILENAME
LABELS_PATH = BASE_DIR / "models_store" / LABELS_FILENAME

# 在创建实例前，进行一次最终的、信息更丰富的文件存在性检查
if not MODEL_PATH.is_file() or not LABELS_PATH.is_file():
    # --- ↓↓↓ 关键修复：使用详细的错误信息字符串 ↓↓↓ ---
    raise FileNotFoundError(
        f"\n❌ 无法找到必要的模型或标签文件！\n"
        f"   - 尝试加载模型: {MODEL_PATH}\n"
        f"   - 尝试加载标签: {LABELS_PATH}\n"
        f"   请仔细检查 `app/models/disease_classifier.py` 文件底部的配置，"
        f"确保它们与 `models_store` 文件夹中实际的文件名完全匹配。"
    )

# 创建一个全局分类器实例，供 app/main.py 等模块导入
classifier = DiseaseClassifier(model_path=MODEL_PATH, labels_path=LABELS_PATH, architecture=MODEL_ARCH)