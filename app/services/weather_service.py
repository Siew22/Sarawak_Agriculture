# app/services/weather_service.py
import httpx
from typing import Dict, Any, List, Optional

class WeatherService:
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    # --- ↓↓↓ 将这个方法重新添加回来 ↓↓↓ ---
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
                
                current_weather = data.get("current", {})
                temperature = current_weather.get("temperature_2m")
                humidity = current_weather.get("relative_humidity_2m")

                if temperature is None or humidity is None:
                    raise ValueError("天气API返回的数据不完整")

                return {"temperature": temperature, "humidity": humidity}

        except httpx.HTTPStatusError as e:
            print(f"天气API请求失败: {e.response.status_code} - {e.response.text}")
            raise ConnectionError("无法连接到天气服务")
        except Exception as e:
            print(f"获取天气数据时发生未知错误: {e}")
            raise ConnectionError("获取天气数据时出错")
    # --- ↑↑↑ 添加结束 ↑↑↑ ---


    async def get_7_day_forecast(self, latitude: float, longitude: float) -> Optional[List[Dict[str, Any]]]:
        """
        获取未来7天的每日天气预报 (最高温、最低温、总降雨量、平均湿度)。
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
                
                if not data or not all(k in data for k in ["time", "temperature_2m_max", "precipitation_sum", "relative_humidity_2m_mean"]):
                    print("天气预报API返回的数据不完整或格式错误")
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
            print(f"获取7天天气预报时出错: {e}")
            return None

# 创建一个全局实例
weather_service = WeatherService()