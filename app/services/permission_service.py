from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app import database, crud

# --- 套餐配置 ---
PLAN_CONFIG = {
    'free': {
        'public': {'api_limit': 10, 'limit_duration_hours': 1, 'can_chat': False, 'can_post': False, 'can_shop': False, 'can_comment': False, 'can_like_share': False},
        'business': {'api_limit': 10, 'limit_duration_hours': 1, 'can_chat': False, 'can_post': False, 'can_shop': True, 'can_comment': False, 'can_like_share': False}
    },
    'tier_10': {
        'public': {'api_limit': 50, 'limit_duration_hours': 8, 'can_chat': True, 'can_post': False, 'can_shop': True, 'can_comment': False, 'can_like_share': True},
        'business': None 
    },
    'tier_15': { # <--- 新增 RM15 套餐
        'public': {'api_limit': 100, 'limit_duration_hours': 6, 'can_chat': True, 'can_post': True, 'can_shop': True, 'can_comment': True, 'can_like_share': True},
    }
}

def get_user_permissions(user: database.User):
    """根据用户角色和订阅套餐，返回权限配置"""
    tier = user.subscription_tier
    user_type = user.user_type
    
    config = PLAN_CONFIG.get(tier, {}).get(user_type)
    if not config:
        # 默认回退到 free public 用户的权限
        return PLAN_CONFIG['free']['public']
    return config

def check_api_limit(db: Session, user: database.User):
    """检查用户是否超出了AI诊断API的使用次数限制"""
    permissions = get_user_permissions(user)
    
    limit_count = permissions['api_limit']
    duration_hours = permissions['limit_duration_hours']
    
    # 查询在指定时间窗口内的使用次数
    time_window_start = datetime.utcnow() - timedelta(hours=duration_hours)
    usage_count = db.query(database.ApiUsageLog).filter(
        database.ApiUsageLog.user_id == user.id,
        database.ApiUsageLog.endpoint == '/diagnose',
        database.ApiUsageLog.timestamp >= time_window_start
    ).count()

    if usage_count >= limit_count:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"API limit of {limit_count} requests per {duration_hours} hours reached. Please try again later."
        )
    return True

# 我们还需要一个函数来记录API使用
def log_api_usage(db: Session, user_id: int, endpoint: str):
    log_entry = database.ApiUsageLog(user_id=user_id, endpoint=endpoint)
    db.add(log_entry)
    db.commit()