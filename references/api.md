# API 参考

**Base URL**：`https://openapi.ihuadai.cn/open/api/v1`
**鉴权**：请求头 `Authorization: <HUADAI_API_KEY>`

所有业务 API 都返回统一 JSON。成功以 `code=200` 为准。

## 搜索笔记

```http
GET https://openapi.ihuadai.cn/open/api/v1/search?query={关键词}&page=1&size=10
Authorization: <HUADAI_API_KEY>
```

curl 示例：

```bash
curl -sS -G "https://openapi.ihuadai.cn/open/api/v1/search" \
  --data-urlencode "query=早起看书" \
  --data-urlencode "page=1" \
  --data-urlencode "size=10" \
  -H "Authorization: $HUADAI_API_KEY"
```

### 搜索响应结构

成功时返回 `code=200`，核心数据在 `data` 字段中：

```json
{
  "code": 200,
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "data": [
      {
        "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
        "type": 1,
        "content": [{ "insert": "笔记正文内容..." }],
        "create_time": 1720000000,
        "update_time": 1720086400,
        "is_collect": 0,
        "is_todo": 0,
        "status": 1
      }
    ]
  }
}
```

**关键字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | int | 匹配总数 |
| `data[].unique_id` | string | 笔记唯一标识，用于更新和查详情 |
| `data[].type` | int | 笔记类型：1=文本、2=图片、3=语音、4=视频 |
| `data[].content` | array | Quill Delta ops 数组，从中提取 `insert` 拼接为文本摘要 |
| `data[].create_time` | int | Unix 秒时间戳 |
| `data[].update_time` | int | 最后更新时间（Unix 秒） |
| `data[].status` | int | 状态：1=正常 |

**提取内容摘要**：`content` 是 Quill Delta 数组，遍历每个 op，取 `insert` 字段拼接即可得到纯文本。

执行要求：

- 无结果时明确回复「未找到」。
- 更新笔记前，优先通过搜索结果确认目标 `unique_id`。
- 不要猜测或生成已有笔记的 `unique_id`。

## 获取笔记详情

```http
GET https://openapi.ihuadai.cn/open/api/v1/block/{unique_id}
Authorization: <HUADAI_API_KEY>
```

curl 示例：

```bash
curl -sS "https://openapi.ihuadai.cn/open/api/v1/block/01jarxm7vndstx68m7qpr1ws5w5xa2b" \
  -H "Authorization: $HUADAI_API_KEY"
```

返回单条笔记的完整信息，包括 `content`、`attachment`、`children`（追记/子笔记）等字段。

执行要求：

- 在用户明确要求查看某条笔记详情，或更新前需要确认完整内容时调用。
- `unique_id` 必须来自搜索结果或用户明确提供。

## 新建笔记

```http
POST https://openapi.ihuadai.cn/open/api/v1/block/upload-block
Authorization: <HUADAI_API_KEY>
Content-Type: application/json
```

公共字段：`type:1` `status:1` `is_collect:0` `is_todo:0` `create_time` 为当前 Unix 秒。`unique_id` 由服务端自动生成，**不要传**。

`content` 支持两种格式：

**Markdown 字符串**（纯文本、加粗、斜体、表格）：

```
"正文 **加粗**\n"
"| 列1 | 列2 |\n|------|------|\n| A | B |\n"
```

**Quill Delta 数组**（含链接时使用）：

```
[{"insert":"文字"},{"insert":"链接","attributes":{"type":"link","link":"https://..."}},{"insert":"\n"}]
```

完整请求示例：

```json
{
  "type": 1,
  "content": "正文\n",
  "create_time": 1717142400,
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

curl 示例：

```bash
curl -sS -X POST "https://openapi.ihuadai.cn/open/api/v1/block/upload-block" \
  -H "Authorization: $HUADAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":1,"content":"正文\n","create_time":1717142400,"status":1,"is_collect":0,"is_todo":0}'
```

执行要求：

- `unique_id` **不要传**，由服务端自动生成。
- 普通文本笔记使用 `type=1`。
- `create_time` 使用当前 Unix 秒。
- 只有响应 `code=200` 后，才能回复「已保存」。

## 更新笔记

```http
POST https://openapi.ihuadai.cn/open/api/v1/block/update-block
Authorization: <HUADAI_API_KEY>
Content-Type: application/json
```

推荐请求体。`unique_id` 必须来自搜索结果或用户明确提供，`content` 传更新后的完整 Markdown 正文：

```json
{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "更新后的完整正文\n",
  "status": 1
}
```

> `is_collect` 和 `is_todo` 不要传，服务端会保留原有状态。

兼容请求体：

```json
{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": [
    {
      "insert": "更新后的完整正文\n"
    }
  ],
  "status": 1
}
```

curl 示例：

```bash
curl -sS -X POST "https://openapi.ihuadai.cn/open/api/v1/block/update-block" \
  -H "Authorization: $HUADAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"unique_id":"01jarxm7vndstx68m7qpr1ws5w5xa2b","type":1,"content":"更新后的完整正文\n","status":1}'
```

执行要求：

- 更新前必须确认目标 `unique_id`。
- `type` 必传，传原笔记类型（通常为 `1`）。
- 如果用户只描述「刚才那条」或「相关那条」，先搜索并确认。
- 请求体应包含更新后的完整正文，避免把增量补充误当成完整内容。
- 只有响应 `code=200` 后，才能回复「已更新」。

## 错误码

| code | 含义 | 处理方式 |
|------|------|----------|
| 200 | 成功 | 写操作可回复已保存/已更新 |
| 400001 | Key 无效 | 引导用户重新创建 API Key 或走 OAuth 授权流程 |
| 400003 | 无权限 | 告知无权限访问该资源 |
| 400018 | 笔记不存在 | 提示重新搜索确认目标笔记 |
| 400024 | 需有效会员 | 引导用户在话袋开通对应权益 |
| 500000 | 系统错误 | 提示稍后重试 |

## OAuth 授权

本 Skill 支持 OAuth Device Flow（RFC 8628），用于自动获取 token。相关端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/oauth/device/code` | 获取设备码和用户验证码 |
| POST | `/oauth/token` | 轮询获取 access_token |
| GET | `/oauth/authorize` | 用户确认授权页面 |
| POST | `/oauth/device/approve` | 确认设备授权（需应用登录 token） |

可使用 `scripts/oauth.sh` 自动化上述流程，无需手动调用这些端点。

## 安全要求

- 不在对话中输出 `HUADAI_API_KEY`。
- 不把 API Key 写入笔记正文。
- 不在 API 调用失败时声称成功。
- 不编造搜索结果、笔记 ID、笔记内容。

---

# 对话示例

## 示例 1：新建笔记

**用户**：「记一下，明天下午 3 点开会讨论 Q3 规划」

```
POST /open/api/v1/block/upload-block

{
  "type": 1,
  "content": "明天下午3点开会讨论Q3规划\n",
  "create_time": 1717142400,
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

**响应**：`{ "code": 200, "message": "成功" }`

「已保存。」

---

## 示例 2：新建含表格的笔记

**用户**：「记一下这周的排期：周一需求评审，周二开发，周三测试」

```
POST /open/api/v1/block/upload-block

{
  "type": 1,
  "content": "| 日期 | 事项 |\n|------|------|\n| 周一 | 需求评审 |\n| 周二 | 开发 |\n| 周三 | 测试 |\n",
  "create_time": 1717142400,
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

> 表格用 Markdown 语法，`|` 分隔列，`\n` 换行。

「已保存。」

---

## 示例 3：新建含链接的笔记

**用户**：「记一下，参考文档 https://example.com/doc」

```
POST /open/api/v1/block/upload-block

{
  "type": 1,
  "content": [
    {"insert": "参考文档："},
    {"insert": "点击查看", "attributes": {"type": "link", "link": "https://example.com/doc"}},
    {"insert": "\n"}
  ],
  "create_time": 1717142400,
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

> 含链接时 content 使用 Quill Delta 数组格式，`type: "link"` 配合 `link` 属性。纯文本可继续使用 Markdown 字符串。

「已保存。」

---

## 示例 4：搜索笔记

**用户**：「帮我找一下关于 Q3 规划的笔记」

```
GET /open/api/v1/search?query=Q3规划&page=1&size=10
```

**响应**：

```json
{
  "code": 200,
  "data": {
    "total": 2,
    "data": [
      {
        "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
        "type": 1,
        "content": [{ "insert": "明天下午3点开会讨论Q3规划\n" }],
        "create_time": 1717142400,
        "update_time": 1717142400
      },
      {
        "unique_id": "01jarxm5abcd1234efgh56789ijk3mc7d",
        "type": 1,
        "content": [{ "insert": "Q3 OKR 初稿：用户增长20%\n" }],
        "create_time": 1716883200,
        "update_time": 1717056000
      }
    ]
  }
}
```
找到 2 条相关笔记：

1. 明天下午3点开会讨论Q3规划  `01jarxm7...xa2b`  7月21日
2. Q3 OKR 初稿：用户增长20%  `01jarxm5...mc7d`  7月18日

---

## 示例 5：搜索后更新笔记

**用户**：「把 Q3 规划那条开会笔记更新一下，时间改成后天下午 2 点」

```
第 1 步 — 搜索确认目标：
GET /open/api/v1/search?query=Q3规划开会&page=1&size=10

响应中匹配到：unique_id = "01jarxm7vndstx68m7qpr1ws5w5xa2b"
```

「是要更新『明天下午3点开会讨论Q3规划』这条笔记吗？」

**用户**：「对」

```
第 2 步 — 执行更新：
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "后天下午2点开会讨论Q3规划\n",
  "status": 1
}
```

**响应**：`{ "code": 200 }`

「已更新。」

---

## 示例 6：搜索多条结果，让用户选择后再更新

**用户**：「更新一下关于开会的那条笔记」

```
GET /open/api/v1/search?query=开会&page=1&size=10
```

**响应**：返回 5 条包含"开会"的笔记。

```
找到 5 条包含『开会』的笔记，你想更新哪一条？

1. 明天下午3点开会讨论Q3规划  `01jarxm7...xa2b`
2. 周会纪要 7/18            `01jarxm4...kd3e`
3. 项目启动会纪要            `01jarxm3...fp8q`

请告诉我是第几条。
```

**用户**：「第 1 条」

「要更新成什么内容？」

**用户**：「改成线上会议」

```
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "线上会议\n",
  "status": 1
}
```

「已更新。」

---

## 示例 7：搜索无结果

**用户**：「找一下关于西藏旅行的笔记」

```
GET /open/api/v1/search?query=西藏旅行&page=1&size=10
```

**响应**：

```json
{ "code": 200, "data": { "total": 0, "data": [] } }
```

「未找到关于『西藏旅行』的笔记。」

---

## 示例 8：获取笔记详情

**用户**：「帮我把 01jarxm7vndstx68m7qpr1ws5w5xa2b 这条笔记的完整内容展示出来」

```
GET /open/api/v1/block/01jarxm7vndstx68m7qpr1ws5w5xa2b
```

**响应**：

```json
{
  "code": 200,
  "data": {
    "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
    "type": 1,
    "content": [{ "insert": "明天下午3点开会讨论Q3规划\n" }],
    "create_time": 1717142400,
    "update_time": 1717142400,
    "is_collect": 0,
    "is_todo": 0,
    "status": 1
  }
}
```

展示笔记标题、正文、创建时间、更新时间等。

---

## 示例 9：收藏笔记

**用户**：「收藏这条笔记 01jarxm7vndstx68m7qpr1ws5w5xa2b」

```
第 1 步 — 获取完整内容：
GET /open/api/v1/block/01jarxm7vndstx68m7qpr1ws5w5xa2b

第 2 步 — 带完整正文更新（is_collect=1）：
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "明天下午3点开会讨论Q3规划\n",
  "status": 1,
  "is_collect": 1
}
```

**响应**：`{ "code": 200 }`

「已收藏。」

---

## 示例 10：标为待办

**用户**：「这条笔记加个待办」

```
第 1 步 — 获取完整内容：
GET /open/api/v1/block/01jarxm7vndstx68m7qpr1ws5w5xa2b

第 2 步 — 带完整正文更新（is_todo=1）：
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "明天下午3点开会讨论Q3规划\n",
  "status": 1,
  "is_todo": 1
}
```

「已标为待办。」
