# app/services/data_management_service.py
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# 导入我们自己的模块
from .knowledge_base_service import kb_service # 我们需要它来写入新知识

class DataManagementService:
    def __init__(self):
        """
        初始化数据管理服务。
        """
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.knowledge_base_path = self.base_dir / "knowledge_base"
        self.dataset_base_path = self.base_dir / "MasterDataset" # 假设我们统一使用 MasterDataset
        
        # 确保核心文件夹存在
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        os.makedirs(self.dataset_base_path / "train", exist_ok=True)
        os.makedirs(self.dataset_base_path / "valid", exist_ok=True)

        print("✅ 数据管理服务已初始化。")

    def add_new_images(self, new_images: List[Dict[str, Any]]) -> str:
        """
        将新发现的图片样本，保存到数据集文件夹中。
        :param new_images: 一个包含图片信息的列表，格式如 [{'class_name': '...', 'image_bytes': b'...', 'filename': '...'}]
        :return: 创建的新的类别名称 (文件夹名)
        """
        if not new_images:
            return None

        # 我们假设一个批次里的所有图片都属于同一个新类别
        new_class_name = new_images[0].get("class_name", "newly_discovered_disease")
        
        # 为这个新类别，在 train 文件夹里创建一个新的子文件夹
        new_class_path = self.dataset_base_path / "train" / new_class_name
        os.makedirs(new_class_path, exist_ok=True)
        
        logger.info(f"正在为新类别 '{new_class_name}' 添加 {len(new_images)} 张新图片...")
        
        for image_info in new_images:
            filename = image_info.get("filename", "new_image.jpg")
            image_bytes = image_info.get("image_bytes")
            
            if filename and image_bytes:
                save_path = new_class_path / filename
                try:
                    with open(save_path, "wb") as f:
                        f.write(image_bytes)
                    logger.success(f"   - ✅ 已保存新图片样本: {save_path}")
                except Exception as e:
                    logger.error(f"   - ❌ 保存图片 {filename} 时失败: {e}")
        
        return new_class_name

    def add_new_knowledge_entry(self, new_class_name: str, new_knowledge: Dict[str, Any]):
        """
        将新发现的知识，追加写入到我们的知识库文件中。
        """
        if not new_class_name or not new_knowledge:
            return

        # 我们将所有新发现的知识，都写入到一个专门的 a_newly_discovered.yaml 文件中
        # 这样做可以避免直接修改我们手写的 pepper.yaml，更安全
        target_yaml_path = self.knowledge_base_path / "a_newly_discovered.yaml"
        
        logger.info(f"正在将新知识 '{new_class_name}' 写入到 {target_yaml_path}...")
        
        # 读取现有的新知识文件（如果存在）
        existing_data = {}
        if target_yaml_path.is_file():
            with open(target_yaml_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = yaml.safe_load(f) or {}
                except yaml.YAMLError as e:
                    logger.error(f"读取现有新知识文件时出错: {e}")

        # 将新知识条目添加进去
        existing_data[new_class_name] = new_knowledge
        
        # 将更新后的内容，写回文件
        try:
            with open(target_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)
            logger.success(f"   - ✅ 新知识已成功写入知识库。")
            
            # --- 关键：刷新内存中的知识库 ---
            # 这样，下一次请求就能立刻使用这个新知识了
            kb_service.reload_knowledge_base()

        except Exception as e:
            logger.error(f"   - ❌ 写入新知识时失败: {e}")
            
# 创建一个全局实例
data_management_service = DataManagementService()