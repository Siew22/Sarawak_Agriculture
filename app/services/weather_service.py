# app/services/weather_service.py (最终修复版本 v4 - 完整代码)

# 【【【 诊断标记已升级到 v4 】】】
print(">>> 正在加载 weather_service.py 版本 v4！已修正天气API的URL。 <<<")

import httpx
from typing import Dict, Any, List, Optional

class WeatherService:
    def __init__(self):
        # 【【【 核心修复：修正了这里的 URL，移除了多余的'-' 】】】
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    async def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        根据经纬度从Open-Meteo获取当前天气数据。
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m",
            "timezone": "auto"
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current", {})
                temperature = current.get("temperature_2m")
                humidity = current.get("relative_humidity_2m")

                if temperature is None or humidity is None:
                    raise ValueError("API返回的数据不完整")

                return {"temperature": temperature, "humidity": humidity}

        except Exception as e:
            print(f"!!! 获取当前天气时出错: {e}. 返回默认值。")
            return {"temperature": 28.0, "humidity": 75.0}

    async def get_7_day_forecast(self, latitude: float, longitude: float) -> Optional[List[Dict[str, Any]]]:
        """
        获取未来7天的每日天气预报。
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum",
            "timezone": "auto",
            "forecast_days": 7
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json().get("daily", {})
                
                required_keys = ["time", "temperature_2m_max", "temperature_2m_min", "relative_humidity_2m_mean", "precipitation_sum"]
                if not data or not all(k in data for k in required_keys):
                    print("!!! 天气预报API数据不完整")
                    return None

                forecast_list = []
                for i in range(len(data["time"])):
                    forecast_list.append({
                        "date": data["time"][i],
                        "temp_max": data["temperature_2m_max"][i],
                        "temp_min": data["temperature_2m_min"][i],
                        "humidity_mean": data["relative_humidity_2m_mean"][i],
                        "precipitation": data["precipitation_sum"][i]
                    })
                return forecast_list
        except Exception as e:
            print(f"!!! 获取7天天气预报时出错: {e}")
            return None

# 创建一个全局实例
weather_service = WeatherService()