# ====================================================================
#  app/models/disease_classifier.py (Final & Complete Version)
# ====================================================================
import torch
import torch.nn as nn
from pathlib import Path
import json
from loguru import logger
from typing import Dict, Optional

# 导入我们的数据结构
# 假设 schemas 文件夹位于 app/ 目录下
from ..schemas.diagnosis import PredictionResult

# 导入需要用到的模型结构
from torchvision.models import efficientnet_b0, efficientnet_b2, convnext_tiny

class DiseaseClassifier:
    def __init__(self, model_path: Path, labels_path: Path, architecture: str = 'b0'):
        """
        初始化分类器，加载自研模型。
        
        Args:
            model_path (Path): 训练好的模型权重文件 (.pth) 的路径。
            labels_path (Path): 类别标签的JSON文件路径。
            architecture (str): 训练时使用的模型架构 ('b0', 'b2', 'convnext_tiny')。
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"DiseaseClassifier is using device: {self.device}")
        
        try:
            # 1. 加载标签文件
            with open(labels_path, 'r', encoding='utf-8') as f:
                # 将json的key从字符串 '0', '1'... 转为整数 0, 1...
                self.labels = {int(k): v for k, v in json.load(f).items()}
            self.num_classes = len(self.labels)
            # 创建一个反向映射，便于 get_class_index 函数调用，提高效率
            self.class_to_idx = {name: idx for idx, name in self.labels.items()}
            logger.info(f"Loaded {self.num_classes} classes from labels file.")

            # 2. 根据指定的架构，构建一个“空白”的模型结构
            logger.info(f"Building a new '{architecture}' model structure...")
            if architecture == 'b0':
                self.model = efficientnet_b0(weights=None, num_classes=self.num_classes)
            elif architecture == 'b2':
                self.model = efficientnet_b2(weights=None, num_classes=self.num_classes)
            elif architecture == 'convnext_tiny':
                self.model = convnext_tiny(weights=None, num_classes=self.num_classes)
            else:
                raise ValueError(f"Unsupported model architecture: '{architecture}'. Choose 'b0', 'b2', or 'convnext_tiny'.")

            # 3. 加载你亲手训练的权重
            logger.info(f"Loading your trained model weights from: {model_path}")
            # 使用 weights_only=True 是更安全和推荐的做法
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
            
            self.model.to(self.device)
            self.model.eval() # 切换到评估模式
            logger.success("DiseaseClassifier initialized successfully.")

        except Exception as e:
            logger.error(f"Error loading the model: {e}", exc_info=True)
            raise RuntimeError(f"加载自研模型时出错: {e}")

    def predict(self, image_tensor: torch.Tensor) -> PredictionResult:
        """
        对输入的图像张量执行预测。
        """
        with torch.no_grad():
            # 确保输入张量在正确的设备上
            image_tensor = image_tensor.to(self.device)
            
            # 模型推理
            outputs = self.model(image_tensor)
            
            # 计算概率
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            # 获取最高概率的预测结果
            confidence_tensor, predicted_idx_tensor = torch.max(probabilities, 0)
            
            top_prediction = PredictionResult(
                disease=self.labels.get(predicted_idx_tensor.item(), "Unknown Disease"),
                confidence=confidence_tensor.item()
            )
            
            # 打印 Top-k 概率分布以供调试
            k = min(self.num_classes, 5)
            topk_prob, topk_indices = torch.topk(probabilities, k)
            
            logger.info(f"--- Probability Distribution (Top {k}) ---")
            for i in range(topk_prob.size(0)):
                idx = topk_indices[i].item()
                label = self.labels.get(idx, f"Unknown_Class_{idx}")
                prob = topk_prob[i].item()
                logger.info(f"  - {label:<40}: {prob:.2%}")
            logger.info("---------------------------------------")
            
            return top_prediction

    def get_class_index(self, class_name: str) -> Optional[int]:
        """根据类别名称，高效地反向查找它对应的数字索引。"""
        return self.class_to_idx.get(class_name)

# ====================================================================
#  全局实例初始化
#  请确保这里的配置与您的模型完全匹配
# ====================================================================

try:
    # 获取项目根目录的绝对路径
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # --- ↓↓↓ 关键配置：请根据您最终训练好的模型进行修改！↓↓↓ ---
    
    # 您的模型文件名
    MODEL_FILENAME = "FINAL_PEPPER_MODEL_b0.pth"
    
    # 您的标签文件名
    LABELS_FILENAME = "final_pepper_labels.json"
    
    # 【【【关键修复】】】
    # 根据您的错误日志，您训练时使用的模型架构很可能是 'b2' 而不是 'b0'
    # 请将这里改为您训练时使用的真实架构
    MODEL_ARCH = "b2" 
    
    # --- ↑↑↑ 配置结束 ↑↑↑ ---

    MODEL_PATH = BASE_DIR / "models_store" / MODEL_FILENAME
    LABELS_PATH = BASE_DIR / "models_store" / LABELS_FILENAME

    # 在创建实例前进行文件存在性检查
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
    if not LABELS_PATH.is_file():
        raise FileNotFoundError(f"Labels file not found at: {LABELS_PATH}")

    # 创建一个全局分类器实例，供 app/main.py 等模块导入
    classifier = DiseaseClassifier(model_path=MODEL_PATH, labels_path=LABELS_PATH, architecture=MODEL_ARCH)

except Exception as e:
    logger.critical(f"Failed to initialize the global classifier: {e}")
    # 在无法加载模型时，创建一个虚拟的分类器或直接退出
    # 这里我们选择抛出异常，让应用启动失败，这是最安全的做法
    raise RuntimeError(f"Could not initialize DiseaseClassifier: {e}")