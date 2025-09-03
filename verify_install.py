#!/usr/bin/env python3
"""
验证 Better Prompts MCP 服务安装是否成功
"""

def test_imports():
    """测试关键模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        import mcp
        print("✅ MCP SDK 导入成功")
    except ImportError as e:
        print(f"❌ MCP SDK 导入失败: {e}")
        return False
    
    try:
        import httpx
        print("✅ httpx 导入成功")
    except ImportError as e:
        print(f"❌ httpx 导入失败: {e}")
        return False
    
    try:
        import pymilvus
        print("✅ pymilvus 导入成功")
    except ImportError as e:
        print(f"❌ pymilvus 导入失败: {e}")
        return False
    
    try:
        import readabilipy
        print("✅ readabilipy 导入成功")
    except ImportError as e:
        print(f"❌ readabilipy 导入失败: {e}")
        return False
    
    try:
        import markdownify
        print("✅ markdownify 导入成功")
    except ImportError as e:
        print(f"❌ markdownify 导入失败: {e}")
        return False
    
    try:
        from mcp_server_better_prompts import server
        print("✅ Better Prompts 服务模块导入成功")
    except ImportError as e:
        print(f"❌ Better Prompts 服务模块导入失败: {e}")
        return False
    
    return True

def test_service_functions():
    """测试服务基础功能"""
    print("\n🧪 测试服务基础功能...")
    
    try:
        from mcp_server_better_prompts.server import is_url
        
        # 测试 URL 检测
        assert is_url("https://example.com") == True
        assert is_url("普通文本") == False
        print("✅ URL 检测功能正常")
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False
    
    return True

def main():
    """主验证函数"""
    print("🚀 Better Prompts MCP 服务安装验证")
    print("=" * 50)
    
    # 测试导入
    import_success = test_imports()
    
    # 测试基础功能
    function_success = test_service_functions()
    
    print("\n" + "=" * 50)
    
    if import_success and function_success:
        print("🎉 安装验证成功！")
        print("\n📋 下一步:")
        print("1. 配置环境变量 (复制 env_example.txt 为 .env)")
        print("2. 配置 Claude Desktop")
        print("3. 重启 Claude Desktop")
        print("4. 开始使用萃取和增强功能！")
        return True
    else:
        print("❌ 安装验证失败，请检查依赖安装")
        return False

if __name__ == "__main__":
    main()
