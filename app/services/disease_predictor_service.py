# app/services/disease_predictor_service.py
from typing import List, Dict, Any

class DiseasePredictorService:
    def __init__(self):
        # 定义病害爆发的“专家规则”
        # 这是一个可扩展的知识库
        self.disease_rules = {
            "Phytophthora_blight": {
                "name": "疫霉病 (Phytophthora Blight)",
                "conditions": lambda day: day["temp_max"] > 25 and day["humidity_mean"] > 85 and day["precipitation"] > 5,
                "message": "炎热、高湿且有显著降雨，是疫霉病爆发的极高风险条件。"
            },
            "Pepper__Anthracnose": {
                "name": "炭疽病 (Anthracnose)",
                "conditions": lambda day: 24 < day["temp_max"] < 32 and day["humidity_mean"] > 90,
                "message": "温暖、极高湿度的天气有利于炭疽病的孢子传播和侵染。"
            },
            # 可以为其他病害添加更多规则...
        }

    def predict_daily_risk(self, forecast: List[Dict[str, Any]], disease_key: str) -> List[Dict[str, Any]]:
        """
        根据未来天气预报，逐日评估指定病害的爆发风险。
        """
        if disease_key not in self.disease_rules:
            raise ValueError(f"未知的病害密钥: {disease_key}。无法进行风险预测。")
        
        rule = self.disease_rules[disease_key]
        daily_predictions = []

        for day in forecast:
            risk_score = 0
            # 基础分
            if day["humidity_mean"] > 80: risk_score += 1
            if day["temp_max"] > 28: risk_score += 1
            if day["precipitation"] > 1: risk_score += 1

            # 如果满足“专家规则”的爆发条件，则分数大幅增加
            if rule["conditions"](day):
                risk_score += 3
            
            # 映射到风险等级
            if risk_score >= 4:
                risk_level = "High"
            elif risk_score >= 2:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            daily_predictions.append({
                "date": day["date"],
                "risk_level": risk_level,
                "risk_score": risk_score,
                "reason": rule["message"] if risk_level == "High" else "天气条件温和。"
            })
        
        return daily_predictions

# 创建全局实例
disease_predictor_service = DiseasePredictorService()