import requests
import json

def test_step_guidance():
    """测试step_guidance API端点"""
    url = "http://127.0.0.1:5000/api/step_guidance"
    
    # 测试数据
    test_data = {
        "project_id": "calculator",
        "step_num": 1
    }
    
    try:
        print("🧪 测试step_guidance API...")
        print(f"📡 请求URL: {url}")
        print(f"📦 请求数据: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API调用成功!")
            response_data = response.json()
            print(f"📝 响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器，请确保Flask应用正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    test_step_guidance() 