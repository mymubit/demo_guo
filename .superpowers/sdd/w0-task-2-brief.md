### Task 2: OpenAPI 契约（项目列表 + 命令信封）

**Files:**
- Create: `docs/contracts/v3/openapi.yaml`

**Interfaces:**
- Consumes: Task 1 命令字典
- Produces: 可被人工与测试引用的路径/Schema

- [ ] **Step 1: 创建最小 OpenAPI**

`docs/contracts/v3/openapi.yaml` 内容如下（可原样落盘，后续里程碑只追加 path，不改已有字段语义）：

```yaml
openapi: 3.0.3
info:
  title: ScriptForge Product API v3
  version: 3.0.0
servers:
  - url: /api/v3
paths:
  /projects/:
    get:
      operationId: listProjects
      summary: 项目列表
      security:
        - bearerAuth: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProjectList"
    post:
      operationId: createProject
      summary: 创建项目
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateProjectRequest"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProject"
  /projects/{project_id}/:
    get:
      operationId: getProject
      summary: 项目详情
      security:
        - bearerAuth: []
      parameters:
        - $ref: "#/components/parameters/ProjectId"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProject"
  /billing/plans/:
    get:
      operationId: listBillingPlans
      summary: 套餐文案（只读壳）
      security:
        - bearerAuth: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeBillingPlans"
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  parameters:
    ProjectId:
      name: project_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  schemas:
    Envelope:
      type: object
      required: [code, message, data]
      properties:
        code: { type: integer }
        message: { type: string }
        data: {}
    ProjectStage:
      type: string
      enum: [topic, blueprint, episodes, writing, quality, delivery]
    ProjectSummary:
      type: object
      required: [id, title, entry_type, stage, updated_at]
      properties:
        id: { type: string, format: uuid }
        title: { type: string }
        entry_type: { type: string, enum: [original, adapt] }
        stage: { $ref: "#/components/schemas/ProjectStage" }
        progress_percent: { type: integer, minimum: 0, maximum: 100 }
        updated_at: { type: string, format: date-time }
    CreateProjectRequest:
      type: object
      required: [title, entry_type]
      properties:
        title: { type: string, minLength: 1, maxLength: 200 }
        entry_type: { type: string, enum: [original, adapt] }
    EnvelopeProjectList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data:
              type: object
              required: [items]
              properties:
                items:
                  type: array
                  items: { $ref: "#/components/schemas/ProjectSummary" }
    EnvelopeProject:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data: { $ref: "#/components/schemas/ProjectSummary" }
    BillingPlan:
      type: object
      required: [id, name, price_label, features]
      properties:
        id: { type: string }
        name: { type: string }
        price_label: { type: string }
        features:
          type: array
          items: { type: string }
    EnvelopeBillingPlans:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data:
              type: object
              required: [items]
              properties:
                items:
                  type: array
                  items: { $ref: "#/components/schemas/BillingPlan" }
```

- [ ] **Step 2: 人工核对**

确认 path 以 `/projects/` 风格带尾斜杠（对齐 Django），与 Spec §4.1 前缀一致。

---

