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
