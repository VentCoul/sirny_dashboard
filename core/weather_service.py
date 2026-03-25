import requests
import pandas as pd
from datetime import datetime, timedelta

def get_weather_history(city="Kyiv", days=30):
    """
    Fetches historical weather data using Open-Meteo (free, no API key required).
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Open-Meteo Archive API
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 50.45,  # Kyiv
        "longitude": 30.52,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "daily": "temperature_2m_max",
        "timezone": "Europe/Berlin"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp_max": data["daily"]["temperature_2m_max"]
        })
        return df
    except Exception as e:
        print(f"Weather API error: {e}")
        return pd.DataFrame()

def get_weather_forecast(city="Kyiv"):
    """
    Fetches weather forecast for today and tomorrow.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 50.45,
        "longitude": 30.52,
        "daily": "temperature_2m_max,weathercode",
        "timezone": "Europe/Berlin",
        "forecast_days": 2
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "today_temp": data["daily"]["temperature_2m_max"][0],
            "tomorrow_temp": data["daily"]["temperature_2m_max"][1],
            "today_code": data["daily"]["weathercode"][0]
        }
    except Exception as e:
        print(f"Forecast API error: {e}")
        return None

if __name__ == "__main__":
    print("Archive:")
    print(get_weather_history().head())
    print("\nForecast:")
    print(get_weather_forecast())
