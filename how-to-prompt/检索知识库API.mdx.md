<div>
  ### 鉴权

  Service API 使用 `API-Key` 进行鉴权。

  建议开发者把 `API-Key` 放在后端存储，而非分享或者放在客户端存储，以免 `API-Key` 泄露，导致财产损失。

  所有 API 请求都应在 **`Authorization`** HTTP Header 中包含您的 `API-Key`，如下所示：

  <CodeGroup title="Code">
    ```javascript
      Authorization: Bearer {API_KEY}

    ```
  </CodeGroup>

  所有请求的 base_url 为"http://dify.dulicode.com/v1"
  
</div>

<Heading
  url='/datasets/{dataset_id}/retrieve'
  method='POST'
  title='检索知识库'
  name='#dataset_retrieval'
/>
<Row>
  <Col>
    ### Path
    <Properties>
      <Property name='dataset_id' type='string' key='dataset_id'>
        知识库 ID
      </Property>
    </Properties>

    ### Request Body
    <Properties>
      <Property name='query' type='string' key='query'>
        检索关键词
      </Property>
      <Property name='retrieval_model' type='object' key='retrieval_model'>
        检索参数（选填，如不填，按照默认方式召回）
        - <code>search_method</code> (text) 检索方法：以下四个关键字之一，必填
          - <code>keyword_search</code> 关键字检索
          - <code>semantic_search</code> 语义检索
          - <code>full_text_search</code> 全文检索
          - <code>hybrid_search</code> 混合检索
        - <code>reranking_enable</code> (bool) 是否启用 Reranking，非必填，如果检索模式为 semantic_search 模式或者 hybrid_search 则传值
        - <code>reranking_mode</code> (object) Rerank 模型配置，非必填，如果启用了 reranking 则传值
            - <code>reranking_provider_name</code> (string) Rerank 模型提供商
            - <code>reranking_model_name</code> (string) Rerank 模型名称
        - <code>weights</code> (float) 混合检索模式下语意检索的权重设置
        - <code>top_k</code> (integer) 返回结果数量，非必填
        - <code>score_threshold_enabled</code> (bool) 是否开启 score 阈值
        - <code>score_threshold</code> (float) Score 阈值
        - <code>metadata_filtering_conditions</code> (object) 元数据过滤条件
          - <code>logical_operator</code> (string) 逻辑运算符: <code>and</code> | <code>or</code>
          - <code>conditions</code> (array[object]) 条件列表
            - <code>name</code> (string) 元数据字段名
            - <code>comparison_operator</code> (string) 比较运算符，可选值:
              - 字符串比较:
                - <code>contains</code>: 包含
                - <code>not contains</code>: 不包含
                - <code>start with</code>: 以...开头
                - <code>end with</code>: 以...结尾
                - <code>is</code>: 等于
                - <code>is not</code>: 不等于
                - <code>empty</code>: 为空
                - <code>not empty</code>: 不为空
              - 数值比较:
                - <code>=</code>: 等于
                - <code>≠</code>: 不等于
                - <code>></code>: 大于
                - <code> < </code>: 小于
                - <code>≥</code>: 大于等于
                - <code>≤</code>: 小于等于
              - 时间比较:
                - <code>before</code>: 早于
                - <code>after</code>: 晚于
            - <code>value</code> (string|number|null) 比较值
      </Property>
      <Property name='external_retrieval_model' type='object' key='external_retrieval_model'>
          未启用字段
      </Property>
    </Properties>
  </Col>
  <Col sticky>
    <CodeGroup
      title="Request"
      tag="POST"
      label="/datasets/{dataset_id}/retrieve"
      targetCode={`curl --location --request POST '${props.apiBaseUrl}/datasets/{dataset_id}/retrieve' \\\n--header 'Authorization: Bearer {api_key}'\\\n--header 'Content-Type: application/json'\\\n--data-raw '{
    "query": "test",
    "retrieval_model": {
        "search_method": "keyword_search",
        "reranking_enable": false,
        "reranking_mode": null,
        "reranking_model": {
            "reranking_provider_name": "",
            "reranking_model_name": ""
        },
        "weights": null,
        "top_k": 1,
        "score_threshold_enabled": false,
        "score_threshold": null,
        "metadata_filtering_conditions": {
            "logical_operator": "and",
            "conditions": [
                {
                    "name": "document_name",
                    "comparison_operator": "contains",
                    "value": "test"
                }
            ]
        }
    }
}'`}
    >
    ```bash {{ title: 'cURL' }}
    curl --location --request POST '${props.apiBaseUrl}/datasets/{dataset_id}/retrieve' \
    --header 'Authorization: Bearer {api_key}' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "query": "test",
        "retrieval_model": {
            "search_method": "keyword_search",
            "reranking_enable": false,
            "reranking_mode": null,
            "reranking_model": {
                "reranking_provider_name": "",
                "reranking_model_name": ""
            },
            "weights": null,
            "top_k": 2,
            "score_threshold_enabled": false,
            "score_threshold": null
        }
    }'
    ```
    </CodeGroup>
    <CodeGroup title="Response">
    ```json {{ title: 'Response' }}
    {
      "query": {
        "content": "test"
      },
      "records": [
        {
          "segment": {
            "id": "7fa6f24f-8679-48b3-bc9d-bdf28d73f218",
            "position": 1,
            "document_id": "a8c6c36f-9f5d-4d7a-8472-f5d7b75d71d2",
            "content": "Operation guide",
            "answer": null,
            "word_count": 847,
            "tokens": 280,
            "keywords": [
              "install",
              "java",
              "base",
              "scripts",
              "jdk",
              "manual",
              "internal",
              "opens",
              "add",
              "vmoptions"
            ],
            "index_node_id": "39dd8443-d960-45a8-bb46-7275ad7fbc8e",
            "index_node_hash": "0189157697b3c6a418ccf8264a09699f25858975578f3467c76d6bfc94df1d73",
            "hit_count": 0,
            "enabled": true,
            "disabled_at": null,
            "disabled_by": null,
            "status": "completed",
            "created_by": "dbcb1ab5-90c8-41a7-8b78-73b235eb6f6f",
            "created_at": 1728734540,
            "indexing_at": 1728734552,
            "completed_at": 1728734584,
            "error": null,
            "stopped_at": null,
            "document": {
              "id": "a8c6c36f-9f5d-4d7a-8472-f5d7b75d71d2",
              "data_source_type": "upload_file",
              "name": "readme.txt",
            }
          },
          "score": 3.730463140527718e-05,
          "tsne_position": null
        }
      ]
    }
    ```
    </CodeGroup>
  </Col>
</Row>