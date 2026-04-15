# 保存笔记（Save）

## 何时使用

- 用户明确要把内容“记下来/存到笔记/收藏/保存”
- 用户发来链接或图片，希望保存为笔记

## 接口（本页覆盖）

本页以话袋后端原生接口为准：统一使用 `/v1` 前缀。

- `POST /open/api/v1/block/upload-block`：新建 Block 笔记
- `POST /open/api/v1/block/update-content`：更新 Block 笔记（内容/属性）
- `POST /open/api/v1/note/note-save-transactions`：新建/更新长笔记（事务）

## 通用请求头（必须）

见 `references/config.md`：

- `USER_UUID: <user_uuid>`
- `Authorization: <api_key>`
- `Content-Type: application/json`（仅 POST 且 body 为 JSON 时需要）

---

## 新建笔记

```
POST {BASE_URL}/block/upload-block
Content-Type: application/json
```

请求体（字段详解见 `references/api-details.md#新建笔记block`）：

```json
{
  "unique_id": "b_xxx",
  "type": 1,
  "content": [],
  "attr": {},
  "create_time": 1741190400
}
```

返回说明：
- 同步完成：返回 `code=200`

---

## 更新笔记（Block）

```
POST {BASE_URL}/block/update-content
Content-Type: application/json
```

请求体：

```json
{
  "unique_id": "b_xxx",
  "type": 1,
  "content": [],
  "attr": {}
}
```

返回说明：
- 同步完成：返回 `code=200`

---

## 新建/更新长笔记（事务）

```
POST {BASE_URL}/note/note-save-transactions
Content-Type: application/json
```

请求体结构见 `references/api-details.md#新建更新长笔记事务`。

---

## 成功判定（必须）

- 必须以 API 返回 `code=200` 为准；未拿到明确成功响应前，禁止回复“已保存”

## 常见错误

见 `references/api-details.md`：

- `400000`：参数/业务校验失败
- `400003`：无权限
- `400018`：笔记不存在（部分场景会返回业务 message）
- `500000`：系统错误

