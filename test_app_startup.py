#!/usr/bin/env python3
"""
应用启动测试脚本
用于验证所有组件是否正常初始化
"""

import sys
import traceback

def test_app_startup():
    """测试应用能否正常启动"""
    try:
        print("🔍 开始测试应用组件...")
        
        # 测试数据库管理器
        print("1️⃣ 测试数据库管理器...")
        from models_neon import DatabaseManager
        db = DatabaseManager()
        print("   ✅ 数据库管理器初始化成功")
        
        # 测试认证中间件导入
        print("2️⃣ 测试认证中间件...")
        from auth_middleware import init_auth_middleware, require_auth, optional_auth
        print("   ✅ 认证中间件导入成功")
        
        # 测试Flask应用
        print("3️⃣ 测试Flask应用...")
        from flask import Flask
        test_app = Flask(__name__)
        print("   ✅ Flask应用创建成功")
        
        # 测试完整应用导入
        print("4️⃣ 测试完整应用导入...")
        try:
            # 只导入，不运行
            import app
            print("   ✅ 应用模块导入成功")
        except Exception as e:
            print(f"   ❌ 应用导入失败: {e}")
            print("   🔍 错误详情:")
            traceback.print_exc()
            return False
        
        print("\n🎉 所有测试通过！应用组件正常")
        print("✨ 应用已准备就绪，可以正常启动")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("🔍 错误详情:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 PyLearn 应用启动测试")
    print("=" * 50)
    
    success = test_app_startup()
    
    print("=" * 50)
    if success:
        print("✅ 测试结果: 成功")
        print("💡 可以运行: python app.py")
        sys.exit(0)
    else:
        print("❌ 测试结果: 失败")
        print("💡 请检查上面的错误信息")
        sys.exit(1) 