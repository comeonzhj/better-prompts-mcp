# 向文档添加块

> 向特定文档添加一个或多个新块（段落）。这对于手动添加精心策划的内容很有用。

## OpenAPI

````yaml zh-hans/openapi_knowledge.json post /datasets/{dataset_id}/documents/{document_id}/segments
paths:
  path: /datasets/{dataset_id}/documents/{document_id}/segments
  method: post
  servers:
    - url: '{apiBaseUrl}'
      description: 知识库 API 的基础 URL。
      variables:
        apiBaseUrl:
          type: string
          description: API 的实际基础 URL
          default: http://dify.dulicode.com/v1
  request:
    security:
      - title: ApiKeyAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                API-Key 鉴权。所有 API 请求都应在 `Authorization` HTTP Header 中包含您的
                API-Key，格式为 `Bearer {API_KEY}`。**强烈建议开发者把 API-Key
                放在后端存储，而非分享或者放在客户端存储，以免 API-Key 泄露，导致财产损失。**
          cookie: {}
    parameters:
      path:
        dataset_id:
          schema:
            - type: string
              required: true
              description: 知识库的 ID。
              format: uuid
        document_id:
          schema:
            - type: string
              required: true
              description: 文档的 ID。
              format: uuid
      query: {}
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              segments:
                allOf:
                  - type: array
                    items:
                      type: object
                      required:
                        - content
                      properties:
                        content:
                          type: string
                          description: 块的文本内容（Q&A 模式中为问题）。
                        answer:
                          type: string
                          description: 答案内容，如果文档处于 Q&A 模式则必需。
                        keywords:
                          type: array
                          description: 与块关联的关键词。
                          items:
                            type: string
            required: true
            refIdentifier: '#/components/schemas/CreateSegmentsRequest'
        examples:
          example:
            value:
              segments:
                - content: <string>
                  answer: <string>
                  keywords:
                    - <string>
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              data:
                allOf:
                  - type: array
                    items:
                      $ref: '#/components/schemas/Segment'
              doc_form:
                allOf:
                  - type: string
            refIdentifier: '#/components/schemas/SegmentListResponse'
        examples:
          example:
            value:
              data:
                - id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  position: 123
                  document_id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  content: <string>
                  answer: <string>
                  word_count: 123
                  tokens: 123
                  keywords:
                    - <string>
                  index_node_id: <string>
                  index_node_hash: <string>
                  hit_count: 123
                  enabled: true
                  disabled_at: 123
                  disabled_by: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  status: <string>
                  created_by: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  created_at: 123
                  indexing_at: 123
                  completed_at: 123
                  error: <string>
                  stopped_at: 123
              doc_form: <string>
        description: 新创建的段落列表。
  deprecated: false
  type: path
components:
  schemas:
    Segment:
      type: object
      properties:
        id:
          type: string
          format: uuid
        position:
          type: integer
        document_id:
          type: string
          format: uuid
        content:
          type: string
        answer:
          type: string
          nullable: true
        word_count:
          type: integer
        tokens:
          type: integer
        keywords:
          type: array
          items:
            type: string
        index_node_id:
          type: string
        index_node_hash:
          type: string
        hit_count:
          type: integer
        enabled:
          type: boolean
        disabled_at:
          type: integer
          format: int64
          nullable: true
        disabled_by:
          type: string
          format: uuid
          nullable: true
        status:
          type: string
        created_by:
          type: string
          format: uuid
        created_at:
          type: integer
          format: int64
        indexing_at:
          type: integer
          format: int64
        completed_at:
          type: integer
          format: int64
        error:
          type: string
          nullable: true
        stopped_at:
          type: integer
          format: int64
          nullable: true

````