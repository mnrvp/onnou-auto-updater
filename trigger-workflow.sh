#!/bin/bash
# GitHub Actions ワークフローを手動でトリガーするスクリプト
# Xサーバーのcronから実行することで、確実にスケジュール実行できます

# 設定
GITHUB_TOKEN="${GITHUB_TOKEN}"
REPO_OWNER="mnrvp"
REPO_NAME="onnou-auto-updater"
WORKFLOW_FILE="daily-auto-post.yml"
BRANCH="main"

# GitHub APIエンドポイント
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}/dispatches"

# ワークフローをトリガー
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "${API_URL}" \
  -d "{\"ref\":\"${BRANCH}\"}")

# レスポンスを解析
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

# 結果を出力
if [ "$http_code" = "204" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ワークフローのトリガーに成功しました"
  exit 0
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] エラー: HTTP ${http_code}"
  echo "$body"
  exit 1
fi
