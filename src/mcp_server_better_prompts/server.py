"""Better Prompts MCP Server implementation."""

import os
import json
import re
from typing import Any, List, Dict, Optional, Tuple
from urllib.parse import urlparse
import asyncio

import httpx
import markdownify
import readabilipy.simple_json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认配置
DEFAULT_USER_AGENT = "Better-Prompts-MCP/1.0 (+https://github.com/better-prompts/mcp)"


class ExtractRequest(BaseModel):
    """萃取请求参数"""
    content: str = Field(description="要萃取的文本内容或URL链接")


class EnhanceRequest(BaseModel):
    """提示增强请求参数"""
    user_input: str = Field(description="用户的原始提示词")
    top_k: int = Field(default=3, description="从知识库检索的方法论数量")


def is_url(text: str) -> bool:
    """判断文本是否为URL"""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_content_from_html(html: str) -> str:
    """从HTML中提取内容并转换为Markdown格式"""
    try:
        ret = readabilipy.simple_json.simple_json_from_html_string(
            html, use_readability=True
        )
        if not ret["content"]:
            return "<error>页面内容提取失败</error>"
        content = markdownify.markdownify(
            ret["content"],
            heading_style=markdownify.ATX,
        )
        return content
    except Exception as e:
        return f"<error>HTML处理失败: {str(e)}</error>"


async def fetch_url_content(url: str) -> str:
    """获取URL内容"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                timeout=300,
            )
            if response.status_code >= 400:
                raise McpError(ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"获取URL失败 {url} - 状态码 {response.status_code}",
                ))
            
            page_raw = response.text
            content_type = response.headers.get("content-type", "")
            is_page_html = (
                "<html" in page_raw[:100] or "text/html" in content_type or not content_type
            )
            
            if is_page_html:
                return extract_content_from_html(page_raw)
            else:
                return page_raw
                
        except httpx.HTTPError as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR, 
                message=f"获取URL失败 {url}: {str(e)}"
            ))


async def call_llm_api(system_prompt: str, user_prompt: str) -> str:
    """调用大模型API"""
    api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    api_key = os.getenv("LLM_API_KEY")
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key:
        raise McpError(ErrorData(
            code=INTERNAL_ERROR,
            message="未配置LLM_API_KEY环境变量"
        ))
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"调用大模型API失败: {str(e)}"
            ))


class KnowledgeBase:
    """知识库抽象基类"""
    
    async def store_methodology(self, methodology: str) -> Dict[str, Any]:
        """存储方法论到知识库"""
        raise NotImplementedError
    
    async def search_methodologies(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """从知识库检索方法论"""
        raise NotImplementedError


class LocalKnowledgeBase(KnowledgeBase):
    """本地知识库实现 (Milvus Lite + Ollama)"""
    
    def __init__(self):
        self.collection_name = "methodologies"
        self.embedding_model = None
        self.milvus_client = None
        
    async def _init_embedding_model(self):
        """初始化嵌入模型"""
        if self.embedding_model is None:
            try:
                # 使用Ollama的nomic-embed-text模型
                import requests
                # 测试Ollama连接
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code != 200:
                    raise Exception("Ollama服务未启动")
                
                # 使用sentence-transformers包装Ollama模型
                from sentence_transformers import SentenceTransformer
                
                # 检查是否有nomic-embed-text模型
                models = response.json().get("models", [])
                if not any("nomic-embed-text" in model.get("name", "") for model in models):
                    raise Exception("未找到nomic-embed-text模型，请运行: ollama pull nomic-embed-text")
                
                self.embedding_model = "ollama_nomic"
            except Exception as e:
                raise McpError(ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"初始化嵌入模型失败: {str(e)}"
                ))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={
                        "model": "nomic-embed-text",
                        "prompt": text
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                return result["embedding"]
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"获取嵌入向量失败: {str(e)}"
            ))
    
    async def _init_milvus(self):
        """初始化Milvus连接"""
        if self.milvus_client is None:
            try:
                from pymilvus import MilvusClient
                
                # 使用Milvus Lite
                self.milvus_client = MilvusClient("milvus_lite.db")
                
                # 检查集合是否存在，不存在则创建
                if not self.milvus_client.has_collection(self.collection_name):
                    # 使用简化的集合创建方式
                    self.milvus_client.create_collection(
                        collection_name=self.collection_name,
                        dimension=768,  # nomic-embed-text 的向量维度
                        metric_type="COSINE",
                        auto_id=True
                    )
            except Exception as e:
                raise McpError(ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"初始化Milvus失败: {str(e)}"
                ))
    
    async def store_methodology(self, methodology: str) -> Dict[str, Any]:
        """存储方法论到本地知识库"""
        await self._init_embedding_model()
        await self._init_milvus()
        
        try:
            # 解析方法论JSON
            methodology_data = json.loads(methodology)
            
            results = []
            for item in methodology_data:
                title = item.get("title", "")
                content = item.get("methodology", "")
                
                # 获取嵌入向量
                embedding = await self._get_embedding(content)
                
                # 插入数据 - 使用简化格式
                data = [{
                    "vector": embedding,
                    "content": content,
                    "title": title
                }]
                
                res = self.milvus_client.insert(
                    collection_name=self.collection_name,
                    data=data
                )
                
                results.append({
                    "title": title,
                    "id": res["ids"][0],
                    "status": "success"
                })
            
            return {"stored_count": len(results), "results": results}
            
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"存储方法论失败: {str(e)}"
            ))
    
    async def search_methodologies(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """从本地知识库检索方法论"""
        await self._init_embedding_model()
        await self._init_milvus()
        
        try:
            # 获取查询嵌入向量
            query_embedding = await self._get_embedding(query)
            
            # 搜索
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k,
                output_fields=["content", "title"]
            )
            
            methodologies = []
            for hit in results[0]:
                methodologies.append({
                    "title": hit.get("title", ""),
                    "content": hit.get("content", ""),
                    "score": hit.get("distance", 0)
                })
            
            return methodologies
            
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"检索方法论失败: {str(e)}"
            ))


class CloudKnowledgeBase(KnowledgeBase):
    """云端知识库实现 (Dify API)"""
    
    def __init__(self):
        self.base_url = os.getenv("DIFY_BASE_URL", "http://dify.dulicode.com/v1")
        self.api_key = os.getenv("DIFY_API_KEY")
        self.dataset_id = os.getenv("DIFY_DATASET_ID")
        self.document_id = os.getenv("DIFY_DOCUMENT_ID")
        
        if not all([self.api_key, self.dataset_id, self.document_id]):
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message="未配置完整的Dify参数: DIFY_API_KEY, DIFY_DATASET_ID, DIFY_DOCUMENT_ID"
            ))
    
    async def store_methodology(self, methodology: str) -> Dict[str, Any]:
        """存储方法论到云端知识库"""
        try:
            # 解析方法论JSON
            methodology_data = json.loads(methodology)
            
            segments = []
            for item in methodology_data:
                segments.append({
                    "content": item.get("methodology", ""),
                    "keywords": [item.get("title", "")]
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/datasets/{self.dataset_id}/documents/{self.document_id}/segments",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"segments": segments},
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "stored_count": len(result.get("data", [])),
                    "results": result.get("data", [])
                }
                
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"存储到云端知识库失败: {str(e)}"
            ))
    
    async def search_methodologies(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """从云端知识库检索方法论"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/datasets/{self.dataset_id}/retrieve",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "retrieval_model": {
                            "search_method": "semantic_search",
                            "top_k": top_k
                        }
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                methodologies = []
                for record in result.get("records", []):
                    segment = record.get("segment", {})
                    methodologies.append({
                        "title": ", ".join(segment.get("keywords", [])),
                        "content": segment.get("content", ""),
                        "score": record.get("score", 0)
                    })
                
                return methodologies
                
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"从云端知识库检索失败: {str(e)}"
            ))


def get_knowledge_base() -> KnowledgeBase:
    """根据环境变量获取知识库实例"""
    storage_type = os.getenv("KNOWLEDGE_STORAGE", "local").lower()
    
    if storage_type == "cloud":
        return CloudKnowledgeBase()
    else:
        return LocalKnowledgeBase()


async def extract_methodology_from_content(content: str) -> str:
    """从内容中萃取方法论"""
    system_prompt = """接下来扮演一个课程设计师，你的任务是从我提供文章内容中萃取方法论。
你萃取的方法论必须是可操作、可执行的，它应该能让学员使用你萃取的方法论开展创作。
一个参考的格式如下（输出时不包含代码块标识符）：
```
## 使用心理账户理论写文案
### 基本原理
//总结这个方法论的原理，让学员透彻理解背景
- 人们心里对钱的使用有不同的标准,会将开支划分为不同的心理账户。
- 5大心理账户:生活必需、家庭建设、个人发展、情感维系、享乐休闲。
- 通过让顾客从一个不愿意花钱的账户,转移到一个乐于消费的账户,就能促成购买。
### 应用方法
//方法论应用的思考方式或具体步骤
- 明确不同心理账户的预算界限：生活必需品的预算一般低于情感类账户的预算
- 明确不同心理账户的重要性：生活必须开支是生活的基本保障，其中的预算无法被迁移为其他账户。
- 引导消费者转移心理账户：在文案中暗示产品属性,转移至预算更高的账户
……
### 细节和示例
//给出使用这个方法论需要注意的细节，给出一些从文章中提取的示例（如果没有示例则留空）
```
**注意**
1. 如果提供的文章无法提取方法论，则回复"你提供的文章不包含可萃取的方法论"
2. 如果文章中包含多套方法论，则分别提取后输出多个方法论。
以 JSON 格式输出，结构如下：
[{
"title":"方法论的名称",
"description":"方法论的使用场景",
"methodology":"提取的方法论内容"
}]"""
    
    user_prompt = f"待萃取方法论的文章：\n<content>\n{content}\n</content>"
    
    return await call_llm_api(system_prompt, user_prompt)


async def enhance_prompt_with_methodology(user_input: str, methodologies: List[Dict[str, Any]]) -> str:
    """使用方法论增强提示词"""
    system_prompt = """扮演一名提示词工程师，根据我接下来为你提供的需求、相关方法论和示例，创建一个可以满足需求的提示词。
## 创作方法
1. 分析需求：理解或挖掘需求的背景和目标，尽可能详细的提供在提示词中，但不要意向编造需求中未描述的信息；
2. 方法论挑选：我会为你提供 0-3个与用户需求相关的方法论，你可以选择其中 1 个或整合多个，放在提示词中。如果接下来的信息中不包含方法论，使用你的自有知识，选择合适的理论增强提示。
## 提示词框架
在创建提示词时，参考以下框架：
````
# 扮演角色：
为 AI 定义角色，让它由通用的"助理"，变成更擅长处理具体工作的定向角色，可以使用职业来描述定义。
## 做什么：
向 AI 尽可能详细的描述任务的背景信息，明确诉求，如果用户输入不包含诉求则根据信息挖掘分析。
## 怎么做：
使用完成这项任务的成熟方法论来引导模型，可以确保 AI 按照预期的方法完成任务，几个tips：
1）如果能给出完成任务的步骤，并要求 AI 输出过程指标，效果会非常棒；
2）方法论中应该包含理论介绍和具体操作细节；
3）如果有示例，保留它们。

## 结果要求：
为 AI 列出输出的要求，包括格式、结构等。
另一个重要的提示：为了防止 AI 胡编乱造，有些时候可以在要求为 AI 留出路，类似"如果你无法执行这个任务，可以回复XXX"。
````
## 输出要求
按以下JSON 格式输出
{
"prompt":"增强的提示词，确保具备更强的引导性"
}"""
    
    # 构建方法论字符串
    methodology_text = ""
    if methodologies:
        methodology_text = "\n".join([
            f"方法论{i+1}: {method['title']}\n{method['content']}\n"
            for i, method in enumerate(methodologies)
        ])
    
    user_prompt = f"""用户需求：
<user_query>
{user_input}
</user_query>
可选方法论支持
<methodology>
{methodology_text}
</methodology>"""
    
    return await call_llm_api(system_prompt, user_prompt)


async def serve() -> None:
    """运行Better Prompts MCP服务器"""
    server = Server("better-prompts")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="extract_methodology",
                description="""从文本或URL中萃取方法论并存储到知识库。

这个工具可以：
1. 接收文本内容或URL链接
2. 如果是URL，会自动提取网页正文内容
3. 使用AI大模型从内容中萃取可操作的方法论
4. 将萃取的方法论存储到配置的知识库中（本地或云端）
5. 返回萃取结果和存储状态""",
                inputSchema=ExtractRequest.model_json_schema(),
            ),
            Tool(
                name="enhance_prompt",
                description="""根据用户输入从知识库检索相关方法论并生成增强的提示词。

这个工具可以：
1. 接收用户的原始提示词
2. 从知识库中检索最相关的方法论（默认前3个）
3. 结合检索到的方法论使用AI生成增强的提示词
4. 返回更专业、更具指导性的提示内容""",
                inputSchema=EnhanceRequest.model_json_schema(),
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        if name == "extract_methodology":
            try:
                args = ExtractRequest(**arguments)
            except ValueError as e:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
            
            # 获取内容
            content = args.content.strip()
            if is_url(content):
                # 是URL，提取网页内容
                content = await fetch_url_content(content)
            
            # 萃取方法论
            methodology = await extract_methodology_from_content(content)
            
            # 存储到知识库
            kb = get_knowledge_base()
            storage_result = await kb.store_methodology(methodology)
            
            result_text = f"""萃取完成！

萃取的方法论：
{methodology}

存储结果：
- 存储方式: {'云端 (Dify)' if isinstance(kb, CloudKnowledgeBase) else '本地 (Milvus Lite)'}
- 存储数量: {storage_result['stored_count']}
- 状态: 成功"""
            
            return [TextContent(type="text", text=result_text)]
        
        elif name == "enhance_prompt":
            try:
                args = EnhanceRequest(**arguments)
            except ValueError as e:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
            
            # 从知识库检索相关方法论
            kb = get_knowledge_base()
            methodologies = await kb.search_methodologies(args.user_input, args.top_k)
            
            # 生成增强提示词
            enhanced_prompt = await enhance_prompt_with_methodology(args.user_input, methodologies)
            
            result_text = f"""提示词增强完成！

检索到的相关方法论数量: {len(methodologies)}
检索方式: {'云端 (Dify)' if isinstance(kb, CloudKnowledgeBase) else '本地 (Milvus Lite)'}

增强后的提示词：
{enhanced_prompt}"""
            
            return [TextContent(type="text", text=result_text)]
        
        else:
            raise McpError(ErrorData(
                code=INVALID_PARAMS,
                message=f"未知的工具: {name}"
            ))
    
    # 创建服务器初始化选项
    options = server.create_initialization_options()
    
    # 运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


async def main():
    """服务入口点"""
    await serve()


if __name__ == "__main__":
    asyncio.run(main())
