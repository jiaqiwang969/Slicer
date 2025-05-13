# monitor_url.py
import requests
import time
import sys
from datetime import datetime

URL = "https://ai.pumpkinai.online/public/log/self/stat?key=sk-YgL2cnnuifh9AloZFa6d63111aC64e4898Ba0769077521Ac"
INTERVAL_SECONDS = 0.3

def fetch_url_status():
    """Fetches the URL and prints the status or error."""
    try:
        response = requests.get(URL, timeout=10) # Add a timeout
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"--- {timestamp} ---")
        if response.status_code == 200:
            print(f"状态码: {response.status_code}")
            # Try to print JSON response if possible, otherwise print text
            try:
                print("响应内容 (JSON):")
                print(response.json())
            except requests.exceptions.JSONDecodeError:
                print("响应内容 (Text):")
                print(response.text)
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print("响应内容:")
            print(response.text)

    except requests.exceptions.Timeout:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"--- {timestamp} ---")
        print("错误: 请求超时")
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"--- {timestamp} ---")
        print(f"错误: 请求失败 - {e}")
    except Exception as e: # Catch any other unexpected errors
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"--- {timestamp} ---")
        print(f"发生意外错误: {e}")
    print("-" * 20) # Separator for readability

if __name__ == "__main__":
    print(f"开始监控 URL: {URL}")
    print(f"每 {INTERVAL_SECONDS} 秒更新一次。按 Ctrl+C 停止。")
    try:
        while True:
            fetch_url_status()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n监控已停止。")
        sys.exit(0)


