## 话袋笔记 API 详细参考（HTTP /open/api/v1）

话袋 HTTP API 路由入口见：`app/http/api/route/route.go`


| 话袋 code | message | 含义/说明 |
|---:|---|---|
| 200 | 请求成功 | 成功 |
| 400000 | 客户端请求错误 | 参数/业务校验失败 |
| 400001 | 未授权/未登录 | token 缺失或失效（部分逻辑会走 HTTP 400） |
| 400003 | 无权限 | 一般配合 HTTP 403 |
| 400018 | 笔记未找到 | 资源不存在 |
| 500000 | 系统错误 | 内部错误/依赖错误 |


## 目录

1. [统一鉴权与请求头](#统一鉴权与请求头)
2. [统一响应结构](#统一响应结构)
3. [错误码表（code）](#错误码表code)
4. [新建笔记（Block）](#新建笔记block)
5. [更新笔记（Block）](#更新笔记block)
6. [删除笔记（Block）](#删除笔记block)
7. [搜索笔记（全文检索）](#搜索笔记全文检索)
8. [新建/更新长笔记（事务）](#新建更新长笔记事务)

---

## 统一鉴权与请求头

- **`USER_UUID`**：与话袋用户 **`unique_id`** 一致，用于对用户做唯一标识与数据归属；在 Skill 等多端场景中可配合配置用于多人聊天下的身份边界与私密性。
- **`Authorization`（API Key）**：用于调用方**身份校验与鉴权登录**，证明请求来自已授权用户。

- **必填 Headers（所有受保护接口）**
  - `USER_UUID: <user_uuid>`：用户唯一标识（同 `unique_id`）
  - `Authorization: <api_key>`：API Key（鉴权登录）
  - `X-Request-Id: <uuid>`：请求追踪（建议；写操作强烈建议）
  - `Content-Type: application/json`：POST/PUT 一般需要

> 对外 OpenAPI 统一使用 `/open/api/v1/...` 

---

## 统一响应结构

### 成功

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {}
}
```

### 失败

失败一般为 HTTP 400/403/500，Body 仍保持统一结构：

```json
{
  "code": 400000,
  "message": "客户端请求错误",
  "data": {}
}
```

其中 `data` 可能不存在或为空对象，视具体接口而定。

---

## 错误码表（code）

话袋错误码采用「分段码」：

- `200`：成功
- `400000+`：客户端/权限/资源类错误
- `500000+`：服务端错误
- `1`：通用失败（少数场景）

下面为 **与笔记/搜索强相关** 的常用错误码（完整列表请以服务端 `package/respond` 为准）：

| code | 含义 | 典型场景 |
|------|------|----------|
| 200 | 请求成功 | 成功返回 |
| 400000 | 客户端请求错误 | 参数校验失败、业务校验失败等 |
| 400001 | 未授权/未登录 | `token` 缺失或无效（常见 message：“请先登录/用户未登录”） |
| 400003 | 无权限 | 无访问权限、禁止访问等（通常会返回 HTTP 403） |
| 400018 | 笔记未找到 | 资源不存在（如 block 不存在） |
| 500000 | 系统错误 | 依赖异常、内部错误 |

> 说明：HTTP 状态码与 `code` 并非一一对应（例如未登录在部分逻辑里会走 HTTP 400 + `400001` 类 code）。

---

## 新建笔记（Block）

### 接口

- **方法/路径**：`POST /open/api/v1/block/upload-block`

### 请求体（核心字段）

请求体为 `Blocks`（字段较多，以下为与“新建笔记”强相关的最小子集；

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `unique_id` | string | 是 | 笔记唯一ID（客户端生成或由上游分配） |
| `type` | int | 是 | 笔记类型（枚举） |
| `content` | array | 否 | 笔记内容（结构化 JSON） |
| `attr` | object | 否 | 扩展属性 |
| `create_time` | uint64 | 是 | 创建时间（秒级时间戳） |
| `parent_id` | string | 否 | 父笔记 unique_id（子笔记/追记） |
| `folder_id` | uint32 | 否 | 文件夹ID |
| `is_collect` | int | 否 | 是否收藏（0/1） |
| `is_todo` | int | 否 | 是否待办（0/1） |
| `status` | int | 否 | 状态（正常/回收站等） |
| `attachment` | array | 否 | 附件列表（上传后的 file_id/path 等） |
| `block_tags` | array | 否 | 标签变更列表（含 action） |
| `quotes` | array | 否 | 引用列表 |

### 响应

成功返回 `code=200`，`data` 通常为一个轻量对象（用于首条创建时的画像提示等，具体以服务端返回为准）。

---

## 更新笔记（Block）

> 第一版仅保留一个“更新”入口,用 `update-block`。

### 接口（推荐：更新内容/属性）

- **方法/路径**：`POST /open/api/v1/block/update-content`

### 请求体（核心字段）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `unique_id` | string | 是 | 笔记唯一ID |
| `type` | int | 是 | 笔记类型（枚举） |
| `content` | array | 否 | 内容（不传则不改） |
| `attr` | object | 否 | 属性（不传则不改） |
| `number_of_words` | int64 | 否 | 字数（可不传，由服务端计算） |
| `block_tags` | array | 否 | 标签变更列表（含 action） |
| `quotes` | array | 否 | 引用列表 |
| `skin` | object | 否 | 皮肤 |

## 搜索笔记（全文检索）

### 接口

- **方法/路径**：`GET /open/api/v1/search`

### Query 参数（常用）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 否 | 搜索关键词（可为空） |
| `page` | int | 否 | 页码，默认 1 |
| `size` | int | 否 | 每页数量，默认 10，最大 100 |
| `search_type` | string | 否 | `keyword` / `script` / `custom`（默认 `custom`） |
| `sort_by` | string | 否 | `_score` / `create_time` / `update_time` |
| `sort_order` | string | 否 | `asc` / `desc` |
| `enable_highlight` | bool | 否 | 是否高亮 |

### 响应（概览）

`data` 为分页对象，包含 `total/page/size/total_pages` 以及 `data[]` 列表；列表项通常包含 `unique_id` 。



## 使用示例（curl）

```bash
# 1. 新建笔记
curl -sS -X POST 'https://openapi.ihuadai.cn/open/api/v1/block/upload-block' \
  -H 'USER_UUID: {user_uuid}' \    
  -H 'Authorization: {api_key}' \
  -H 'X-Request-Id: {uuid}' \
  -H 'Content-Type: application/json' \
  -d '{
    "unique_id": "unique_id", #笔记的unique_id，标识笔记
    "type": 1,
    "content": [
      { "insert": "hello from openapi\n", "attributes": { "type": "text" } }
    ],
    "is_collect": 0,
    "is_todo": 0,
    "status": 1,
    "create_time": 1713148800
  }'

# 2. 更新笔记（内容/属性）
curl -sS -X POST 'https://openapi.ihuadai.cn/open/api/v1/block/update-content' \
  -H 'USER_UUID: {user_uuid}' \  
  -H 'Authorization: {api_key}' \
  -H 'X-Request-Id: {uuid}' \
  -H 'Content-Type: application/json' \
  -d '{
    "unique_id": "",
    "type": 1,
    "content": [
      { "insert": "updated content\n", "attributes": { "type": "text" } }
    ],
    "number_of_words": 0
  }'

# 3. 搜索笔记 
curl -sS -X GET 'https://openapi.ihuadai.cn/open/api/v1/search?query=hello&page=1&size=10' \
  -H 'Version: 9.9.9' \
  -H 'Source: wechat-mini-program' \
  -H 'Device-Id: openclaw-test' \
  -H 'USER_UUID: {user_uuid}' \
  -H 'Authorization: {api_key}'
```

注：
用户的 unique_id：放在请求头 USER_UUID 里（也就是 HUADAI_USER_UUID），用于标识“谁在调用、数据归属到哪个用户”。
笔记的 unique_id：放在请求体字段 unique_id 里，用于标识“这条笔记本身的 ID”（创建时你生成一个；更新时用它来定位要更新哪条笔记）。 