---
name: hd-notes-skills
description: |
  话袋笔记 - 通过话袋 OpenAPI 新建、更新和搜索个人笔记。

  当以下情况时使用此 Skill：
  (1) 用户要保存内容到笔记：「记一下」「存到笔记」「保存」「收藏」
  (2) 用户要更新内容到笔记：「更新一下」「更新笔记」「补充到这条」
  (3) 用户要搜索或查看笔记：「搜一下」「找找笔记」「打开某条笔记」「笔记详情」
  (4) 用户要配置话袋笔记：「配置话袋」「连接话袋笔记」「授权话袋」「怎么填 Key」
version: 1.1.0
homepage: https://clawhub.ai/monkeydb/hd-notes-skills
user-invocable: true
metadata:
  openclaw:
    emoji: "📝"
    primaryEnv: HUADAI_API_KEY
    requires:
      env:
        - HUADAI_API_KEY
    envVars:
      - name: HUADAI_API_KEY
        required: true
        description: 话袋开放平台 API Key（请求头 Authorization）
    baseUrl: "https://openapi.ihuadai.cn/open/api/v1"
    homepage: "https://clawhub.ai/monkeydb/hd-notes-skills"
    repository: "https://github.com/monkeyDB/hd-notes-skills"
---

# 话袋笔记 Skill

## Agent 必读约束

- **唯一 Base URL**：`https://openapi.ihuadai.cn/open/api/v1`。禁止使用其他域名，禁止重复拼接 `/open/api/v1`。
- **鉴权方式**：业务 API 仅使用请求头 `Authorization: <HUADAI_API_KEY>`。
- **API Key 来源**：用户需先在 [话袋开放平台](https://ihuadai.cn/desktop/openai) 创建 API Key。如果用户未配置，优先引导走 OAuth 授权流程（见下方「OAuth 授权」章节）。
- **数据真实性**：所有笔记内容、搜索结果、笔记 ID 都必须来自 API 响应。禁止编造「已保存」「已找到」「已更新」。
- **写操作确认**：只有 API 返回 `code=200` 后，才能回复用户已保存或已更新。
- **更新笔记约束**：`unique_id` 必须来自搜索结果或用户明确提供，禁止猜测或生成已有笔记 ID。
- **密钥安全**：不要在对话中要求用户粘贴 API Key，不要回显、记录、总结或展示 `HUADAI_API_KEY`。

## 快速开始：OAuth 授权（推荐）

如果你还没有配置 `HUADAI_API_KEY`，可以引导用户走 OAuth 设备授权流程（零门槛，不需要复制粘贴 Key）：

```
用户说：「帮我授权话袋笔记」

Agent 执行：
./scripts/oauth.sh
```

脚本自动完成设备码获取、用户授权、token 轮询全流程。OAuth 失败时引导用户：
- 打开 https://ihuadai.cn/desktop/openai 创建 API Key
- 设置环境变量：`export HUADAI_API_KEY=<你的Key>`

## 文档索引

| 文档 | 内容 | 何时读取 |
|------|------|----------|
| [API 参考](references/api.md) | 请求/响应格式、curl 示例、错误码、端到端对话示例 | 需要构造 API 调用或参考完整对话时 |

## 路由表

| 用户说（示例） | 操作 | 执行 |
|--------------|------|------|
| 「授权话袋」「连接话袋笔记」 | OAuth | 执行 `./scripts/oauth.sh` |
| 「配置话袋」「怎么填 Key」 | Config | 引导用户创建 API Key |
| 「记一下」「保存」`/huadai upload` | 新建笔记 | `POST /block/upload-block` |
| 「更新笔记」「补充到这条」`/huadai update` | 更新笔记 | 先搜索确认 → `POST /block/update-block` |
| 「搜一下」「找找笔记」`/huadai search` | 搜索笔记 | `GET /search` |
| 「收藏这条」「收藏一下」 | 收藏笔记 | 先搜索获取完整内容 → `POST /block/update-block`，传 `"is_collect": 1` |
| 「标为待办」「加个待办」 | 标待办 | 先搜索获取完整内容 → `POST /block/update-block`，传 `"is_todo": 1` |
| 「打开这条笔记」「笔记详情」 | 查看详情 | `GET /block/:unique_id` |

完整 URL = `https://openapi.ihuadai.cn/open/api/v1` + 路径。接口详情见 [API 参考](references/api.md)。

## 执行规则

### 搜索笔记

- 调用 `GET /search?query=<关键词>&page=1&size=10`。
- 无结果时明确回复「未找到」，不要编造类似笔记。
- 从响应中提取关键信息展示给用户：
  - `unique_id` — 笔记唯一标识（更新/查详情时需要）
  - `content` — Quill Delta 数组，提取 `insert` 字段拼接为纯文本摘要
  - `create_time` / `update_time` — Unix 时间戳，可转为可读时间
  - `type` — 笔记类型
- 展示结果时优先给标题/摘要/`unique_id`，方便用户选择要更新哪条。
- 如果结果超过一页（`total > size`），提示用户缩小搜索范围或翻页。

### 获取笔记详情

- 调用 `GET /block/:unique_id` 查看笔记完整内容。
- 仅在用户明确要求查看某条笔记详情，或需要获取完整内容用于更新时使用。

### 新建笔记

- **不要传 `unique_id` 字段**（或传空字符串 `""`），由服务端自动生成与手动操作一致的笔记 ID。
- 普通文本笔记使用 `type=1`。
- `content` 支持两种格式：
  - **Markdown 字符串**：纯文本、加粗、斜体、表格等。如 `"正文 **加粗**\n"` 或 `"\| 列1 \| 列2 \|\n\|..."`
  - **Quill Delta 数组**：含链接时使用。如 `[{"insert":"点击","attributes":{"type":"link","link":"https://..."}},...]`
- `create_time` 使用当前 Unix 秒。
- `status=1` 表示正常笔记。
- `is_collect=0` 表示非收藏笔记（`0`=否 `1`=是）。
- `is_todo=0` 表示非待办笔记（`0`=否 `1`=是）。

### 更新笔记

- 更新前必须确认目标 `unique_id`。
- 如果用户没有提供明确 `unique_id`，先搜索，再让用户确认或选择最匹配的一条。
- `type` 传原笔记类型（通常为 `1`）。`content` 传更新后的完整 Markdown 字符串。
- 不要只发送「追加内容」并假装已合并，除非 API 请求体确实包含最终要保存的内容。
- 改正文时**不要传 `is_collect` 和 `is_todo`**，服务端会保留原有状态。收藏/取消收藏时传 `"is_collect": 1/0`，标待办/取消待办时传 `"is_todo": 1/0`，**同时必须带上完整正文**。

## 示例速查

更多完整对话示例见 [API 参考](references/api.md)。

### 新建笔记

公共字段：`type:1` `status:1` `is_collect:0` `is_todo:0` `create_time` 为当前 Unix 秒，`unique_id` 不传。

content 示例：

```
纯文本 →  "明天下午3点开会\n"
含表格 →  "| 日期 | 事项 |\n|------|------|\n| 周一 | 评审 |\n"
含链接 →  [{"insert":"参考："},{"insert":"点击","attributes":{"type":"link","link":"https://..."}},{"insert":"\n"}]
```

### 更新笔记

用户：「把开会那条笔记改成后天下午2点」

```
1. GET /search?query=开会  →  找到匹配笔记
2. 向用户确认：「是要更新『明天下午3点开会』这条吗？」
3. 用户确认 → POST /block/update-block  { "unique_id": "01j...", "type": 1, "content": "后天下午2点开会\n", "status": 1 }
```

## 脚本调用指引

本 Skill 提供了 `scripts/` 目录下的辅助脚本。在环境中配置了 `HUADAI_API_KEY` 后，可以直接执行：

```bash
# OAuth 授权（用户未配置 Key 时首选）
./scripts/oauth.sh

# 搜索笔记
./scripts/search.sh "关键词"

# 新建笔记
./scripts/upload.sh "笔记内容（Markdown）"

# 更新笔记
./scripts/update.sh <unique_id> "新内容"
```

脚本已处理参数校验和错误处理，可直接调用。

## 通用错误处理

| code | 处理方式 |
|------|----------|
| 200 | 成功。写操作可回复已保存/已更新 |
| 400001 | API Key 无效，引导用户重新创建或走 OAuth 授权 |
| 400003 | 无权限访问该资源 |
| 400018 | 笔记不存在，提示重新搜索确认 |
| 400024 | 需要有效会员，引导用户在话袋开通对应权益 |
| 500000 | 服务异常，提示稍后重试 |

## 安全规则

- 不输出 API Key。
- 不保存 API Key 到笔记正文。
- 不在未调用 API 或 API 未成功时声称操作完成。
- 不猜测已有笔记 ID、用户身份、隐藏内容。
- 不泄露搜索结果以外的任何用户数据。
