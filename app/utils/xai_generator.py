# xai_generator.py
import os
import numpy as np
import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image
from PIL import Image
from pathlib import Path
import cv2

class XaiGenerator:
    def __init__(self, model: torch.nn.Module, target_layers: list):
        """
        初始化XAI生成器。
        :param model: 训练好的PyTorch模型。
        :param target_layers: 模型中用于生成Grad-CAM的目标卷积层。
        """
        self.model = model
        # --- ↓↓↓ 移除 use_cuda 参数 ↓↓↓ ---
        self.cam = GradCAM(model=model, target_layers=target_layers)
        # --- ↑↑↑ 修改结束 ↑↑↑ ---

    def _preprocess_image_for_xai(self, image_bytes: bytes):
        """
        为XAI准备图像：将其转换为适合可视化的RGB numpy数组。
        注意：这个预处理和送入模型的预处理不同，它不进行标准化。
        """
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        # 调整大小以匹配模型的输入尺寸，但不进行标准化
        resized_img = image.resize((224, 224))
        rgb_img = np.array(resized_img, dtype=np.float32) / 255
        return rgb_img

    def generate_heatmap(self, image_tensor: torch.Tensor, image_bytes: bytes, target_category: int) -> np.ndarray:
        """
        生成Grad-CAM热力图并将其叠加在原始图片上。
        :param image_tensor: 经过完整预处理（包括标准化）后，送入模型的Tensor。
        :param image_bytes: 原始的图片字节流。
        :param target_category: 模型预测出的目标类别索引。
        :return: 返回一个叠加了热力图的RGB图像（numpy数组, 0-255范围）。
        """
        # 定义目标：我们想知道模型为什么会预测出这个 specific category
        targets = [ClassifierOutputTarget(target_category)]

        # 生成灰度CAM图
        grayscale_cam = self.cam(input_tensor=image_tensor, targets=targets)
        
        # Grad-CAM可能会为batch中的每个图像生成一个CAM，我们只取第一个
        grayscale_cam = grayscale_cam[0, :]

        # 准备原始图像以供可视化
        rgb_img_for_viz = self._preprocess_image_for_xai(image_bytes)
        
        # 将CAM叠加到原始RGB图像上
        visualization = show_cam_on_image(rgb_img_for_viz, grayscale_cam, use_rgb=True)
        
        return visualization

# --- 全局实例初始化 ---
# 我们需要导入我们的分类器来获取模型本身
from ..models.disease_classifier import classifier
import io

# 找到模型的最后一个卷积层。这是Grad-CAM最常用的目标层。
# 对于ConvNeXt-Tiny, 最后一个阶段的最后一个block是 `features[-1][-1]`
# 对于EfficientNet, 通常是 `features[-1]`
target_model = classifier.model
target_layers = []

# 动态寻找目标层
if hasattr(target_model, 'features') and isinstance(target_model.features, torch.nn.Sequential):
    # 这适用于EfficientNet和ConvNeXt
    # 我们选择最后一个包含卷积的模块
    # 对于 ConvNeXt, 最后一个 block 是一个不错的选择
    # 对于 EfficientNet, 最后一个 MBConv block 是个好选择
    # -1 通常是 a pooling layer or the final conv head, let's try -2 or a specific block
    # For ConvNeXt-tiny, the last block is `features[-1][-1]` which is a CNBlock. Let's target its layer_scale
    if "convnext" in target_model.__class__.__name__.lower():
        # 选择最后一个stage的最后一个block
        target_layers = [target_model.features[-1][-1]] 
    elif "efficientnet" in target_model.__class__.__name__.lower():
        # 选择最后一个MBConv块
         target_layers = [target_model.features[-1]]
    else:
        print("警告: 未知的模型架构，无法自动确定XAI目标层。")

xai_generator = None
if target_layers:
    print(f"XAI (Grad-CAM) 目标层已确定: {target_layers[0].__class__.__name__}")
    xai_generator = XaiGenerator(model=target_model, target_layers=target_layers)
else:
    print("警告: XAI模块初始化失败，因为无法找到合适的目标层。")

def save_xai_image(image_array: np.ndarray, filename: str) -> Path:
    """
    将numpy数组格式的热力图保存为图片文件。
    """
    # 确保静态文件夹存在
    static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "xai_images"
    os.makedirs(static_dir, exist_ok=True)

    output_path = static_dir / f"{filename}.jpg"
    
    # 将 BGR (OpenCV's default) 转换为 RGB (PIL's default)
    # The visualization is already RGB, so convert to BGR for cv2.imwrite
    image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    cv2.imwrite(str(output_path), image_bgr)
    print(f"✅ XAI热力图已保存至: {output_path}")
    return output_path