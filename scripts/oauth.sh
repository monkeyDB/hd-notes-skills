#!/usr/bin/env bash
# ============================================================
# 话袋笔记 Skill · OAuth 设备授权
# OAuth Device Flow (RFC 8628)
#
# 用法:
#   ./oauth.sh [client_id]
#
# 流程:
#   1. 调用 /oauth/device/code 获取设备码和用户码
#   2. 引导用户打开验证页面，输入用户码确认授权
#   3. 轮询 /oauth/token 等待用户授权完成
#   4. 输出 access_token，提示用户配置到环境变量
#
# 依赖:
#   - curl
# ============================================================
set -euo pipefail

BASE_URL="${HUADAI_BASE_URL:-https://test-openapi.ihuadai.cn/open/api/v1}"

# --- 步聚 1：获取设备码 ---
echo "📡 正在请求设备授权码..."
DEVICE_RESP=$(curl -sS -X POST "$BASE_URL/oauth/device/code" \
  -H "Content-Type: application/json" 2>&1)

DEVICE_CODE=$(echo "$DEVICE_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("device_code",""))' 2>/dev/null || echo "")
USER_CODE=$(echo "$DEVICE_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("user_code",""))' 2>/dev/null || echo "")
VERIFICATION_URI=$(echo "$DEVICE_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("verification_uri","https://test.ihuadai.cn/desktop/openai"))' 2>/dev/null || echo "https://test.ihuadai.cn/desktop/openai")
INTERVAL=$(echo "$DEVICE_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("interval",5))' 2>/dev/null || echo "5")

if [ -z "$DEVICE_CODE" ]; then
  echo "❌ 获取设备码失败，请检查网络或稍后重试。"
  echo "   后端响应: $DEVICE_RESP"
  echo ""
  echo "   你也可以手动配置 API Key："
  echo "   1. 打开 https://test.ihuadai.cn/desktop/openai"
  echo "   2. 创建 API Key"
  echo "   3. 设置环境变量: export HUADAI_API_KEY=<你的Key>"
  exit 1
fi

# --- 步聚 2：引导用户授权 ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔑 请在浏览器中打开以下链接完成授权："
echo ""
echo "     $VERIFICATION_URI"
echo ""
echo "  验证码: $USER_CODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ 等待授权完成..."

# --- 步聚 3：轮询 token ---
MAX_WAIT=180  # 最多等 3 分钟
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  sleep "$INTERVAL"
  ELAPSED=$((ELAPSED + INTERVAL))

  TOKEN_RESP=$(curl -sS -X POST "$BASE_URL/oauth/token" \
    -H "Content-Type: application/json" \
    -d "{\"device_code\":\"$DEVICE_CODE\"}" 2>&1)

  TOKEN_CODE=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("code",-1))' 2>/dev/null || echo "-1")

  if [ "$TOKEN_CODE" = "200" ]; then
    ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("access_token",""))' 2>/dev/null || echo "")
    REFRESH_TOKEN=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("refresh_token",""))' 2>/dev/null || echo "")
    EXPIRES_IN=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("expires_in",""))' 2>/dev/null || echo "")

    echo ""
    echo "✅ 授权成功！"
    echo ""
    echo "  请将以下内容添加到你的环境变量配置中："
    echo ""
    echo "  export HUADAI_API_KEY=\"$ACCESS_TOKEN\""
    echo ""
    if [ -n "$REFRESH_TOKEN" ] && [ "$REFRESH_TOKEN" != "null" ]; then
      echo "  export HUADAI_REFRESH_TOKEN=\"$REFRESH_TOKEN\""
      echo ""
    fi
    echo "  方式 1（临时生效）: 在终端直接执行上面的 export 命令"
    echo "  方式 2（永久生效）: 写入 ~/.bashrc 或 ~/.zshrc"
    exit 0
  fi

  # 用户尚未确认，继续等待
  echo "    ...等待中（已等待 ${ELAPSED}s）"
done

echo ""
echo "⏰ 授权超时。请重新运行 ./scripts/oauth.sh 获取新的验证码。"
echo ""
echo "   也可以手动配置 API Key："
echo "   1. 打开 https://test.ihuadai.cn/desktop/openai"
echo "   2. 创建 API Key"
echo "   3. 执行: export HUADAI_API_KEY=<你的Key>"
exit 1
