# 音脳ラボ｜自動更新システム

DTM/宅録専門ブログ「音脳ラボ」の自動記事生成・投稿システム

## 🎯 目的

品質を保ちながら、更新頻度と網羅性を自動化で補強し、検索流入とSNS流入を安定的に積み上げる。

## 🧠 基本思想

- **完全自動量産はしない**
- AIは「編集部アシスタント」
- 人間は「最終判断と専門性の付加」
- まずは下書き自動生成 → 問題なければ段階的に自動公開

## 🛠 技術スタック

- **実行環境**: GitHub Actions（毎日1回cron実行）
- **言語**: Python 3.9+
- **AI**: Anthropic Claude API
- **連携**: WordPress REST API

## 📁 プロジェクト構成

```
onnou-auto-updater/
├── .github/
│   └── workflows/
│       └── daily-post.yml        # GitHub Actions設定
├── src/
│   ├── article_generator.py      # 記事生成ロジック
│   ├── wordpress_client.py       # WordPress連携
│   └── theme_manager.py          # テーマ管理
├── data/
│   └── themes.json               # 記事テーマリスト
├── .env.example                  # 環境変数テンプレート
├── requirements.txt              # Python依存パッケージ
└── README.md
```

## 🚀 セットアップ

### 1. リポジトリのクローン

```bash
git clone <your-repo-url>
cd onnou-auto-updater
```

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、必要な値を設定：

```bash
cp .env.example .env
```

### 3. GitHub Secretsの設定

以下のシークレットをGitHubリポジトリに設定：

- `CLAUDE_API_KEY`: Anthropic Claude APIキー
- `WP_SITE_URL`: WordPressサイトのURL（例: https://example.com）
- `WP_USERNAME`: WordPressユーザー名
- `WP_APP_PASSWORD`: WordPressアプリケーションパスワード

### 4. 記事テーマの設定

`data/themes.json` に記事テーマを追加

## 📝 使い方

### ローカルでのテスト実行

```bash
pip install -r requirements.txt
python src/article_generator.py
```

### GitHub Actionsでの自動実行

デフォルトで毎日午前9時（JST）に自動実行されます。

### Xサーバーのcronから確実に実行する方法（推奨）

GitHub Actionsのスケジュール実行は不安定なため、Xサーバーのcronから確実にトリガーする方法を推奨します。

#### 1. GitHub Personal Access Tokenの作成

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token」→ 「Generate new token (classic)」
3. スコープで `workflow` にチェック
4. トークンをコピーして保存

#### 2. Xサーバーに配置

`trigger-workflow.sh` をXサーバーにアップロード（例：`/home/youraccount/scripts/`）

#### 3. 実行権限を付与

```bash
chmod +x /home/youraccount/scripts/trigger-workflow.sh
```

#### 4. Xサーバーのcron設定

サーバーパネル → Cron設定 で以下を設定：

**コマンド:**
```bash
export GITHUB_TOKEN="your_github_token_here"; /home/youraccount/scripts/trigger-workflow.sh
```

**実行時刻:** 毎日0時（または任意の時刻）
- 分: 0
- 時: 0
- 日: *
- 月: *
- 曜日: *

#### 5. 動作確認

設定後、以下で動作確認：
```bash
export GITHUB_TOKEN="your_token"; ./trigger-workflow.sh
```

成功すると「ワークフローのトリガーに成功しました」と表示され、GitHub Actionsが実行されます。

## 🔐 安全設計

- 最初は全て **draft（下書き）** として投稿
- `AUTO_PUBLISH` フラグで自動公開のON/OFF切替可能（将来実装）
- 下書き生成と公開ジョブは分離設計

## 📈 フェーズ計画

### フェーズ1（現在）
- GitHub Actions設定
- 記事下書き自動生成
- WordPressに下書き投稿
- 手動チェック・公開

### フェーズ2（将来）
- 画像自動挿入
- X用投稿文の自動生成
- 自動公開機能
- 記事ログ分析

## ⚠️ 注意事項

- 生成された記事は必ず人間が確認してから公開すること
- APIキーは絶対に公開リポジトリにコミットしないこと
- テーマリストは定期的に見直し・追加すること

---

## 🔧 トラブルシューティング

### GitHub Actionsのスケジュールが動かない場合

**現在の状態（2026-01-11時点）:**
- ✅ YAMLファイルのインデント修正により、GitHub Actionsのスケジュール機能が復活
- ✅ `schedule-test`で10分ごとの自動実行を確認済み
- ✅ `daily-auto-post.yml`は毎日深夜0時に自動実行される設定
- ⚠️ Xサーバーのcronは予備として設定済み（現在OFF）

**問題が発生した場合:**
1. GitHub Actionsタブで実行履歴を確認
2. 失敗している場合はログでエラー内容を確認
3. GitHubのスケジュールが不安定な場合は、Xサーバーのcronを有効化

### テーマの自動補充について

- 未使用テーマが3個以下になると、自動的に3個生成されます
- Gemini APIを使用して自動生成
- 生成されたテーマは`data/themes.json`に自動追加され、GitHubにコミットされます

### 作業履歴

**2026-01-11:**
- YAMLファイルのインデント問題を修正（`.github/workflows/daily-auto-post.yml`）
- Xサーバーcron用のトリガースクリプト作成（`trigger-workflow.sh`）
- GitHub Actionsのスケジュール機能が正常に動作することを確認
- `schedule-test`を無効化（テスト完了のため）
- 次回確認：2026-01-12朝、深夜0時の自動実行結果を確認予定
