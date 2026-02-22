import requests
import json

# 1. 配置信息
API_URL = "http://127.0.0.1:8000/finance/api/agent/transaction/"
TOKEN = "ba42dd8babe509c7ed11601e130f59f982f74aa6 " # 注意：Token 后面有个空格

def simulate_ai_agent(user_command):
    print(f"🤖 Agent 收到指令: '{user_command}'")
    
    # 2. 模拟 LLM (Llama 3.1) 的解析结果
    # 实际开发时，这里会调用 Ollama 的 API
    # 假设 LLM 将 "I spent 15 pounds on a burger" 解析为：
    mock_llm_data = {
        "amount": "15.00",
        "currency": "GBP",
        "category": "Food",
        "type": "Expense",
        "note": f"Natural Language Input: {user_command}",
        "date": "2026-02-04T12:00:00Z"
    }

    # 3. 通过 API 发送到 Django
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=mock_llm_data, headers=headers)
        if response.status_code == 200:
            print("✅ 记账成功！后端返回:", response.json())
        else:
            print(f"❌ 记账失败，错误码: {response.status_code}, 原因: {response.text}")
    except Exception as e:
        print(f"⚠️ 连接服务器失败: {e}")

if __name__ == "__main__":
    simulate_ai_agent("I spent 15 pounds on a burger today")