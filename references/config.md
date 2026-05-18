# 配置（必须先完成）

本文档以 [话袋笔记 API 详细参考](api-details.md) 为准：话袋对外 OpenAPI 统一使用 **`/open/api/v1/...`** 前缀，并通过 **API Key** 做调用方鉴权。

## 你需要准备什么

### 1) 必需请求头（所有 OpenAPI 接口）

- `Authorization: <api_key>`：API Key（必填，用于身份校验与对外接口鉴权登录）

建议同时携带：

- `X-Request-Id: <uuid>`：请求追踪/审计（强烈建议；写操作建议每次唯一）
- `Content-Type: application/json`：仅在 POST 且有 JSON body 时需要

> 说明：当前 Skill 采用对外 `Authorization: <api_key>` 形式.

### 2) 建议通过环境变量注入（推荐）

- `HUADAI_API_KEY`（必填）：对应请求头 `Authorization`，用于鉴权登录
- `HUADAI_BASE_URL`（必填）：话袋 OpenAPI 根地址（例如 `https://openapi.ihuadai.cn/open/api/v1`
- `HUADAI_CLIENT_ID`（可选覆盖，仅 OAuth）：OAuth Device Flow 的应用标识（用于申请设备码与轮询换取 `HUADAI_API_KEY`；详见 [OAuth 授权配置（话袋笔记）](oauth.md)）

## 配置原则（必须遵守）

- 不要在聊天里回显 `Authorization` / `api_key`
- 缺少 `HUADAI_API_KEY` 时，Skill 必须拒绝执行任何读写请求，并引导用户完成配置
- 一切“已保存/已删除/已找到”的结论必须来自 API 响应（以 `code=200` 为准）

```json
{
  "skills": {
    "entries": {
      "huadai-notes-skill": {
        "env": {
          "HUADAI_API_KEY": "hk_live_****",
          "HUADAI_BASE_URL": "https://openapi.ihuadai.cn/open/api/v1"
        }
      }
    }
  }
}
```
