# 对话示例

完整对话示范，覆盖所有笔记操作场景。

---

## 示例 1：新建笔记

**用户**：「记一下，明天下午 3 点开会讨论 Q3 规划」

**Agent**：

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

**响应**：

```json
{ "code": 200, "data": { "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b" } }
```

**Agent 回复**：「已保存。」

---

## 示例 2：搜索笔记

**用户**：「帮我找一下关于 Q3 规划的笔记」

**Agent**：

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

**Agent 回复**：

```
找到 2 条相关笔记：

1. 明天下午3点开会讨论Q3规划  `01jarxm7...xa2b`  7月21日
2. Q3 OKR 初稿：用户增长20%  `01jarxm5...mc7d`  7月18日
```

---

## 示例 3：搜索后更新笔记

**用户**：「把 Q3 规划那条开会笔记更新一下，时间改成后天下午 2 点」

**Agent**：

```
第 1 步 — 搜索确认目标：
GET /open/api/v1/search?query=Q3规划开会&page=1&size=10

响应中匹配到：unique_id = "01jarxm7vndstx68m7qpr1ws5w5xa2b"
```

**Agent 回复**：「是要更新『明天下午3点开会讨论Q3规划』这条笔记吗？」

**用户**：「对」

**Agent**：

```
第 2 步 — 执行更新：
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "后天下午2点开会讨论Q3规划\n",
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

**响应**：`{ "code": 200 }`

**Agent 回复**：「已更新。」

---

## 示例 4：搜索无结果

**用户**：「找一下关于西藏旅行的笔记」

**Agent**：

```
GET /open/api/v1/search?query=西藏旅行&page=1&size=10
```

**响应**：

```json
{ "code": 200, "data": { "total": 0, "data": [] } }
```

**Agent 回复**：「未找到关于『西藏旅行』的笔记。」

---

## 示例 5：获取笔记详情

**用户**：「帮我把 01jarxm7vndstx68m7qpr1ws5w5xa2b 这条笔记的完整内容展示出来」

**Agent**：

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

**Agent 回复**：展示笔记标题、正文、创建时间、更新时间等。

---

## 示例 6：搜索多条结果，让用户选择后再更新

**用户**：「更新一下关于开会的那条笔记」

**Agent**：

```
GET /open/api/v1/search?query=开会&page=1&size=10
```

**响应**：返回 5 条包含"开会"的笔记。

**Agent 回复**：

```
找到 5 条包含『开会』的笔记，你想更新哪一条？

1. 明天下午3点开会讨论Q3规划  `01jarxm7...xa2b`
2. 周会纪要 7/18            `01jarxm4...kd3e`
3. 项目启动会纪要            `01jarxm3...fp8q`

请告诉我是第几条。
```

**用户**：「第 1 条」

**Agent 回复**：「要更新成什么内容？」

**用户**：「改成线上会议」

**Agent**：

```
POST /open/api/v1/block/update-block

{
  "unique_id": "01jarxm7vndstx68m7qpr1ws5w5xa2b",
  "type": 1,
  "content": "线上会议\n",
  "status": 1,
  "is_collect": 0,
  "is_todo": 0
}
```

**Agent 回复**：「已更新。」
