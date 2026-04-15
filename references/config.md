# 配置（必须先完成）

本文档以 `references/api-details.md` 为准：话袋对外 OpenAPI 统一使用 **`/open/api/v1/...`** 前缀，并通过 **`USER_UUID + API Key`** 做调用方鉴权。

## 你需要准备什么

### 1) 必需请求头（所有 OpenAPI 接口）

- `USER_UUID: <user_uuid>`：用户唯一标识（与话袋用户 **`unique_id`** 一致；必填，用于归属与多人场景下的身份边界）
- `Authorization: <api_key>`：API Key（必填，用于身份校验与对外接口鉴权登录）

建议同时携带：

- `X-Request-Id: <uuid>`：请求追踪/审计（强烈建议；写操作建议每次唯一）
- `Content-Type: application/json`：仅在 POST 且有 JSON body 时需要

> 说明：当前 Skill 第一版不使用 `token` 登录态；采用对外 `Authorization: <api_key>` 形式（与 Get笔记的 API Key 形态一致，但 header 集合不同） i。

### 2) 建议通过环境变量注入（推荐）

- `HUADAI_USER_UUID`（必填）：对应请求头 `USER_UUID`，取值与话袋用户 **`unique_id`** 一致
- `HUADAI_API_KEY`（必填）：对应请求头 `Authorization`，用于鉴权登录
- `HUADAI_BASE_URL`（必填）：话袋 OpenAPI 根地址（例如 `https://api.example.com/open/api/v1`，不含末尾斜杠）
- `HUADAI_CLIENT_ID`（可选覆盖，仅 OAuth）：OAuth Device Flow 的应用标识（用于申请设备码与轮询换取 `HUADAI_API_KEY`；详见 `references/oauth.md`）

## Scope（权限）约定

对外接口建议按 scope 进行权限控制与审计（即使当前服务端实现未完全落地，也建议在 Skill 文档里先按此约定写清楚）。

| Scope | 说明 |
|---|---|
| `notes.write` | 新建/更新笔记（Block/长笔记） |
| `notes.delete` | 删除/回收笔记（Block/长笔记） |
| `notes.search` | 搜索笔记 |

## 配置原则（必须遵守）

- 不要在聊天里回显 `USER_UUID`
- 不要在聊天里回显 `Authorization` / `api_key`
- 缺少 `USER_UUID` 或 `HUADAI_API_KEY` 时，Skill 必须拒绝执行任何读写请求，并引导用户完成配置
- 一切“已保存/已删除/已找到”的结论必须来自 API 响应（以 `code=200` 为准）

```json
{
  "skills": {
    "entries": {
      "huadai-notes-skill": {
        "env": {
          "HUADAI_USER_UUID": "uu_****",
          "HUADAI_API_KEY": "hk_live_****",
          "HUADAI_BASE_URL": "https://openapi.ihuadai.cn/open/api/v1"
        }
      }
    }
  }
}
```

