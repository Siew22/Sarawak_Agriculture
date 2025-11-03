# app/services/knowledge_discovery_service.py (最终的、LAVIS已禁用版)

import torch
from PIL import Image
import io
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

# 导入我们自己的模块
from ..models.recommendation_generator import report_generator_v3 as report_generator
from ..services.knowledge_base_service import kb_service
import requests
from bs4 import BeautifulSoup

# --- ↓↓↓ 关键修复：彻底禁用 LAVIS 相关的导入！↓↓↓ ---
# from lavis.models import load_model_and_preprocess
LAVIS_AVAILABLE = False
# --- ↑↑↑ 修复结束 ↑↑↑ ---


class KnowledgeDiscoveryService:
    def __init__(self):
        """
        初始化知识发现服务。
        图像描述模型已被禁用，以解决依赖冲突。
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.captioning_model = None
        self.vis_processors = None
        
        # --- ↓↓↓ 关键修复：彻底禁用 LAVIS 模型的加载！↓↓↓ ---
        # if LAVIS_AVAILABLE:
        #     try:
        #         print(">>> 正在加载知识发现核心：图像描述模型 (BLIP)...")
        #         self.captioning_model, self.vis_processors, _ = load_model_and_preprocess(
        #             name="blip_caption", model_type="base_coco", is_eval=True, device=self.device
        #         )
        #         print("✅ 图像描述模型加载完成。")
        #     except Exception as e:
        #         print(f"❌ 加载图像描述模型失败: {e}. 知识发现服务将受限。")
        # --- ↑↑↑ 修复结束 ↑↑↑ ---
        print("✅ 知识发现服务已初始化 (图像描述功能已禁用)。")


    def _generate_keywords_from_image(self, image_bytes: bytes) -> str:
        """步骤1：从图像生成描述性关键词 (当前为简化版)"""
        # --- ↓↓↓ 关键修复：使用备用方案 ↓↓↓ ---
        if not self.captioning_model:
            logger.warning("图像描述模型不可用，使用通用关键词进行网络搜索。")
            return "pepper plant leaf disease" # 返回一个通用的、高质量的关键词
        # --- ↑↑↑ 修复结束 ↑↑↑ ---
        
        # (下面的代码暂时不会被执行)
        try:
            raw_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = self.vis_processors["eval"](raw_image).unsqueeze(0).to(self.device)
            captions = self.captioning_model.generate({"image": image})
            logger.info(f"   - AI图像描述: '{captions[0]}'")
            return f"{captions[0]} on pepper plant"
        except Exception as e:
            logger.error(f"   - ❌ 从图像生成关键词时失败: {e}")
            return "pepper plant leaf disease"

    async def discover(self, image_bytes: bytes, lang: str) -> Tuple[Optional[Dict], Optional[List]]:
        """主函数：执行完整的知识发现流程。"""
        # (这个函数的主体逻辑不需要修改，因为它现在会自动使用上面的备用方案)
        keywords = self._generate_keywords_from_image(image_bytes)
        summaries = report_generator.web_search_and_summarize(keywords, lang)
        
        if not summaries:
            logger.warning("网络探索失败：未能找到相关的、有价值的信息。")
            return None, None

        new_knowledge = {
            "name": {lang: keywords.split(' on ')[0].capitalize()},
            "summary": {lang: ". ".join(summaries)},
            "symptoms": [{lang: s} for s in summaries],
            "treatments": [
                {
                    "title": {lang: "网络参考建议"},
                    "steps": [{lang: "由于这是新发现的状况，建议将此报告与本地农业专家确认，以获取最精准的防治方案。"}]
                }
            ]
        }
        new_class_name = keywords.replace(" ", "_").replace(",", "")[:30]
        new_images = [{"class_name": new_class_name, "image_bytes": image_bytes, "filename": f"{new_class_name}_source.jpg"}]

        logger.success(f"✅ 探索成功！已构建新的知识草稿，并准备了 {len(new_images)} 张新图片样本。")
        return new_knowledge, new_images

# 创建一个全局实例
knowledge_discovery_service = KnowledgeDiscoveryService()