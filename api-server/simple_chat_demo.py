#!/usr/bin/env python3
"""
简单的聊天演示脚本
展示如何使用修复后的 API 服务器进行聊天
"""

import requests
import json

def chat_with_api(message: str, model: str = "sample_dify") -> dict:
    """发送聊天请求到 API 服务器"""
    url = "http://localhost:8000/v1/chat/completions"
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": message}
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"请求失败: {response.status_code}",
                "detail": response.text
            }
            
    except Exception as e:
        return {
            "error": f"请求异常: {e}"
        }

def main():
    """主函数"""
    print("🤖 AI-DT API 聊天演示")
    print("=" * 40)
    print("输入 'quit' 或 'exit' 退出程序")
    print("=" * 40)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("👋 再见！")
                break
                
            if not user_input:
                continue
            
            print("🤔 思考中...")
            
            # 发送请求
            response = chat_with_api(user_input)
            
            if "error" in response:
                print(f"❌ 错误: {response['error']}")
                if "detail" in response:
                    print(f"   详情: {response['detail']}")
            else:
                # 提取回复内容
                if response.get('choices') and len(response['choices']) > 0:
                    content = response['choices'][0]['message']['content']
                    print(f"\n🤖 AI: {content}")
                    
                    # 显示token使用情况
                    if response.get('usage'):
                        usage = response['usage']
                        print(f"\n📊 Token使用: {usage.get('prompt_tokens')} + {usage.get('completion_tokens')} = {usage.get('total_tokens')}")
                else:
                    print("❌ 未收到有效回复")
                    
        except KeyboardInterrupt:
            print("\n\n👋 程序被中断，再见！")
            break
        except Exception as e:
            print(f"❌ 程序异常: {e}")

if __name__ == "__main__":
    main()