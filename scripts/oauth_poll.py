#!/usr/bin/env python3
"""
话袋笔记：OAuth 设备码（Device Flow）脚本（申请设备码 + 轮询换取 API Key）

话袋开放接口以 `references/api-details.md` / `config.md` 为准：
- 请求头 **`USER_UUID`**：在话袋侧对应用户的 **`unique_id`**，用于对用户做唯一标识与归属；在群聊等多人场景下，Skill 只处理与已配置 **`HUADAI_USER_UUID`** 一致的用户，从而保证**私密性**。
- 请求头 **`Authorization: <api_key>`**：**API Key 用于身份校验与鉴权登录**（验证调用方是否为合法授权用户）。

请勿将 OAuth 兑换用的「授权轮询码」与 **`USER_UUID` / `unique_id`** 混用；本地配置使用 **`HUADAI_USER_UUID`**（值与 **`unique_id`** 一致）。

本脚本支持两种用法（方案 A：清晰分层，不混用）：

1) **仅轮询**：你已经拿到了「授权轮询码」（device code），用它轮询 `/oauth/token` 兑换 **`api_key`**。
2) **一键流程**：自动调用 `/oauth/device/code` 申请设备码，打印 `verification_uri` + `user_code` 给用户完成授权，然后后台轮询 `/oauth/token` 直到拿到 **`api_key`**。

成功时均输出 `data` JSON（含 `api_key`，并保留服务端返回的 `unique_id/user_uuid` 以写入 `HUADAI_USER_UUID`）。
其中 HTTP 请求体里的 `grant_type` 取值为 OAuth 2.0 Device Flow 的固定字面量（与话袋侧 `USER_UUID`/`unique_id` 含义无关；本 Skill 不做设备绑定，也不需要 `Device-Id`）。

与 `api-details.md` 一致：成功响应多为 { "code": 200, "data": { ... } }；亦兼容 { "success": true, "data": { ... } }。

用法:
    export HUADAI_BASE_URL="https://<your-domain>/open/api/v1"   # 必填，不含末尾斜杠
    # 方式 A：一键申请设备码并轮询
    python oauth_poll.py --start

    # 方式 B：仅轮询（你已从 /oauth/device/code 拿到 code）
    python oauth_poll.py <auth_code>

环境变量:
    HUADAI_BASE_URL  - 话袋 OpenAPI 根地址（必填）
    HUADAI_CLIENT_ID - 应用 ID（必填，OAuth 流程使用；与 user_uuid/unique_id 无关）

参数:
    auth_code  - 授权轮询码（由 POST /open/api/v1/oauth/device/code 返回；用于兑换凭证，**不是** USER_UUID）

返回:
    成功: stdout 输出 `data` 的 JSON。请将其中的 **`api_key`** 写入 `HUADAI_API_KEY`（鉴权登录）；
          若包含 **`unique_id`** 或与之一致的 **`user_uuid`**，写入 **`HUADAI_USER_UUID`**，对应请求头 **`USER_UUID`**（多人聊天中的用户边界）。
    失败: stderr 说明，非零退出码

退出码:
    0 - 授权成功
    1 - 参数/环境错误
    2 - 用户拒绝授权
    3 - 授权码已过期
    4 - 授权码已被使用
    5 - 未知错误
    6 - 轮询超时

示例:
    export HUADAI_BASE_URL="https://api.example.com/open/api/v1"
    # 一键流程
    result=$(python oauth_poll.py --start)
    # 或仅轮询
    # result=$(python oauth_poll.py "abc123...")
    api_key=$(echo "$result" | jq -r '.api_key')
    # unique_id 与 USER_UUID 对应；部分响应可能字段名为 user_uuid
    user_uuid=$(echo "$result" | jq -r '.unique_id // .user_uuid // empty')
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

INTERVAL = 5
MAX_ATTEMPTS = 120  # 5s * 120 = 10 分钟


def _base_url() -> str:
    base = (os.environ.get("HUADAI_BASE_URL") or "").strip().rstrip("/")
    if not base:
        print(
            "缺少环境变量 HUADAI_BASE_URL（话袋 OpenAPI 根地址，例如 https://openapi.ihuadai.cn）",
            file=sys.stderr,
        )
        sys.exit(1)
    return base


def _token_url() -> str:
    return f"{_base_url()}/oauth/token"


def _device_code_url() -> str:
    return f"{_base_url()}/oauth/device/code"


def _is_success_payload(data: dict) -> bool:
    """话袋统一结构 code=200；兼容网关 success=true。成功以 data.api_key 为准（换取后的 Key 用于后续鉴权）。"""
    inner = data.get("data") or {}
    if not isinstance(inner, dict):
        return False
    if inner.get("api_key"):
        if data.get("code") == 200:
            return True
        if data.get("success") is True:
            return True
    return False


def _extract_status_msg(data: dict) -> str:
    inner = data.get("data")
    if isinstance(inner, dict):
        m = inner.get("msg")
        if isinstance(m, str) and m:
            return m
    return ""


def _request_json(url: str, payload: bytes, headers: dict) -> dict:
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _maybe_client_id() -> str:
    return (os.environ.get("HUADAI_CLIENT_ID") or "").strip()

def _client_id() -> str:
    cid = _maybe_client_id()
    if not cid:
        print(
            "缺少环境变量 HUADAI_CLIENT_ID（OAuth 流程所需的应用 ID，例如 cli_xxx）",
            file=sys.stderr,
        )
        sys.exit(1)
    return cid


def request_device_code(api_url: str) -> dict:
    """
    申请设备码（device code）。
    兼容两种服务端实现：
    - 不需要 client_id：发送 {}
    - 需要 client_id：若设置了 HUADAI_CLIENT_ID，则发送 {"client_id": "..."}
    """
    body_dict = {"client_id": _client_id()}

    body = json.dumps(body_dict).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    try:
        data = _request_json(api_url, body, headers)
    except urllib.error.URLError as e:
        print(f"网络错误: {e}", file=sys.stderr)
        sys.exit(5)
    except json.JSONDecodeError as e:
        print(f"响应非 JSON: {e}", file=sys.stderr)
        sys.exit(5)

    # 统一结构：{code,message,data:{code,verification_uri,user_code,...}}
    # 兼容结构：{success:true,data:{...}}
    inner = data.get("data") if isinstance(data, dict) else None
    if not isinstance(inner, dict):
        print(f"未知响应: {data}", file=sys.stderr)
        sys.exit(5)

    if data.get("code") == 200 or data.get("success") is True:
        if inner.get("code") and inner.get("verification_uri") and inner.get("user_code"):
            return inner

    # 统一结构失败时可能只有 code/message
    if data.get("message"):
        print(f"接口错误: {data.get('code')} {data.get('message')}", file=sys.stderr)
        sys.exit(5)

    print(f"未知响应: {data}", file=sys.stderr)
    sys.exit(5)


def poll_token(auth_code: str, api_url: str) -> dict:
    # grant_type 为 OAuth 2.0 Device Flow 在 token 端点的固定取值；本 Skill 不做设备绑定、不需要 Device-Id。
    # 话袋用户唯一标识见请求头 USER_UUID（值同 unique_id，见 HUADAI_USER_UUID）。
    body_dict = {"grant_type": "device_code", "client_id": _client_id(), "code": auth_code}

    body = json.dumps(body_dict).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    for _attempt in range(MAX_ATTEMPTS):
        try:
            data = _request_json(api_url, body, headers)
        except urllib.error.URLError as e:
            print(f"网络错误: {e}", file=sys.stderr)
            time.sleep(INTERVAL)
            continue
        except json.JSONDecodeError as e:
            print(f"响应非 JSON: {e}", file=sys.stderr)
            time.sleep(INTERVAL)
            continue

        if _is_success_payload(data):
            return data["data"]

        msg = _extract_status_msg(data)
        if not msg and data.get("message"):
            # 统一结构失败时可能仅在 message 描述
            print(f"接口错误: {data.get('code')} {data.get('message')}", file=sys.stderr)
            sys.exit(5)

        if msg == "authorization_pending":
            time.sleep(INTERVAL)
            continue
        if msg == "rejected":
            print("用户拒绝了授权", file=sys.stderr)
            sys.exit(2)
        if msg == "expired_token":
            print("授权码已过期，请重新发起", file=sys.stderr)
            sys.exit(3)
        if msg == "already_consumed":
            print("授权码已被使用", file=sys.stderr)
            sys.exit(4)

        print(f"未知响应: {data}", file=sys.stderr)
        sys.exit(5)

    print("轮询超时（10分钟），请重新发起授权", file=sys.stderr)
    sys.exit(6)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"用法: HUADAI_BASE_URL=https://... {sys.argv[0]} --start | <auth_code>",
            file=sys.stderr,
        )
        sys.exit(1)

    arg1 = sys.argv[1].strip()

    if arg1 in ("--start", "start"):
        device = request_device_code(_device_code_url())
        verification_uri = device.get("verification_uri")
        user_code = device.get("user_code")
        auth_code = device.get("code")

        # 授权提示输出到 stderr，避免污染 stdout 的最终 JSON
        print("请点击链接完成授权：", file=sys.stderr)
        print(verification_uri, file=sys.stderr)
        print(f"请核对确认码：{user_code}", file=sys.stderr)
        print("授权完成后脚本会自动轮询换取 API Key…", file=sys.stderr)
    else:
        auth_code = arg1

    api_url = _token_url()
    result = poll_token(auth_code, api_url)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
