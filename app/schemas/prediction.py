# app/schemas/prediction.py
from pydantic import BaseModel, Field
from typing import List, Dict

class DailyRisk(BaseModel):
    date: str
    risk_level: str = Field(..., description="风险等级 (Low, Medium, High)")
    risk_score: int
    reason: str

class RiskPredictionResponse(BaseModel):
    disease_name: str
    location: Dict[str, float]
    daily_risks: List[DailyRisk]