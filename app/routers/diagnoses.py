# app/routers/diagnoses.py (新建)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import database, crud
from app.dependencies import get_current_user # 从 main.py 导入依赖
from app.schemas.diagnosis import DiagnosisHistory # 假设您有一个对应的 Pydantic Schema

router = APIRouter(prefix="/diagnoses", tags=["Diagnoses"])

@router.get("/me", response_model=List[DiagnosisHistory])
def read_user_diagnosis_history(
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    return crud.get_diagnosis_history_by_user(db=db, user_id=current_user.id)