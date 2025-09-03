# Better Prompts MCP

一个自动帮助用户从文章中萃取理论、存储到向量数据库、根据用户输入自动从知识库中调用方法论、构建更增强提示词的 MCP 服务。

## 🌟 功能特性

### 萃取工具 (extract_methodology)
- 📝 支持文本内容和 URL 链接输入
- 🌐 自动提取网页正文内容
- 🤖 使用 AI 从内容中萃取可操作的方法论
- 💾 支持本地和云端两种存储方式

### 提示增强工具 (enhance_prompt)
- 🔍 从知识库检索相关方法论（默认前3个）
- ✨ 结合方法论生成增强的提示词
- 📚 提供更专业、更具指导性的提示内容

### 双模式知识库
- **本地存储**: Milvus Lite + Ollama 嵌入模型
- **云端存储**: Dify 知识库 API

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Claude Desktop (或其他支持 MCP 的客户端)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/comeonzhj/better-prompts-mcp.git
   cd better-prompts-mcp
   ```

2. **安装依赖**
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **配置环境变量**
   ```bash
   cp env_example.txt .env
   # 编辑 .env 文件配置您的参数
   ```

4. **本地存储配置（可选）**
   ```bash
   # 安装并启动 Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama serve
   
   # 安装嵌入模型
   ollama pull nomic-embed-text
   ```

5. **配置 Claude Desktop**
   
   编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：
   ```json
   {
     "mcpServers": {
       "better_prompts": {
         "command": "uv",
         "args": [
           "--directory",
           "/绝对路径/到/better-prompts-mcp",
           "run",
           "python",
           "-m",
           "mcp_server_better_prompts"
         ],
         "env": {
           "KNOWLEDGE_STORAGE": "local",
           "LLM_API_BASE": "https://api.openai.com/v1",
           "LLM_API_KEY": "your_api_key_here",
           "LLM_MODEL_NAME": "gpt-3.5-turbo"
         }
       }
     }
   }
   ```

6. **重启 Claude Desktop**

## 📖 使用方法

### 萃取方法论

#### 从文本萃取
```
请帮我萃取以下内容中的方法论：

[粘贴您要萃取的文本内容]
```

#### 从 URL 萃取
```
请帮我萃取这个网页中的方法论：
https://example.com/article
```

### 增强提示词

```
请帮我优化这个提示词：

我想写一篇关于产品营销的文案
```

系统会自动：
1. 从知识库检索相关的营销方法论
2. 结合方法论生成增强的提示词
3. 返回更专业、更具指导性的提示内容

## ⚙️ 配置说明

### 环境变量

#### 基础配置
```bash
# 知识库存储方式: local/cloud
KNOWLEDGE_STORAGE=local

# 大模型 API 配置
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL_NAME=gpt-3.5-turbo
```

#### 云端存储配置（可选）
```bash
DIFY_BASE_URL=http://dify.dulicode.com/v1
DIFY_API_KEY=your_dify_api_key
DIFY_DATASET_ID=your_dataset_id
DIFY_DOCUMENT_ID=your_document_id
```

## 🏗️ 技术架构

- **MCP 协议**: 基于标准 MCP 协议实现
- **向量数据库**: Milvus Lite (本地) / Dify API (云端)
- **嵌入模型**: Ollama nomic-embed-text
- **内容提取**: readabilipy + markdownify
- **大模型**: 支持 OpenAI 兼容的 API

## 🔧 故障排除

### 常见问题

1. **Milvus 向量数据库错误**
   - 重新安装服务：`uv pip install -e . --force-reinstall`

2. **Ollama 连接失败**
   - 确保服务已启动：`ollama serve`
   - 确认模型已安装：`ollama list | grep nomic-embed-text`

3. **API 调用失败**
   - 检查 API 密钥配置
   - 确认网络连接正常

## 🧪 验证安装

运行验证脚本：
```bash
python verify_install.py
```

## 📁 项目结构

```
better-prompts-mcp/
├── pyproject.toml                    # 项目配置
├── env_example.txt                   # 环境变量示例
├── claude_desktop_config_example.json # Claude 配置示例
├── 使用说明.md                       # 详细使用说明
├── verify_install.py                 # 安装验证脚本
└── src/
    └── mcp_server_better_prompts/
        ├── __init__.py
        ├── __main__.py
        └── server.py                 # 主服务实现
```

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

## 📄 许可证

MIT License

## 🙏 致谢

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- [Milvus](https://milvus.io/)
- [Ollama](https://ollama.ai/)
- [Dify](https://dify.ai/)
