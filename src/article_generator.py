"""
記事生成のメインロジック
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from theme_manager import ThemeManager
from wordpress_client import WordPressClient


class ArticleGenerator:
    """Claude APIを使った記事生成クラス"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Args:
            api_key: Anthropic APIキー
            model: 使用するClaudeモデル
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_article(self, theme: dict) -> dict:
        """
        テーマに基づいて記事を生成する

        Args:
            theme: テーマ情報の辞書

        Returns:
            生成された記事情報（title, content）
        """
        # プロンプトの構築
        prompt = self._build_prompt(theme)

        # Claude APIで記事生成
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # レスポンスから記事本文を抽出
        article_content = message.content[0].text

        return {
            'title': theme['title'],
            'content': article_content,
            'theme_id': theme['id']
        }

    def _build_prompt(self, theme: dict) -> str:
        """
        記事生成用のプロンプトを構築する

        Args:
            theme: テーマ情報

        Returns:
            プロンプト文字列
        """
        prompt = f"""あなたは「音脳ラボ」というDTM/宅録専門ブログの編集アシスタントです。
以下のテーマで、初心者〜中級者向けの実践的な記事を書いてください。

# 記事テーマ
{theme['title']}

# 読者が抱える悩み
{theme['target_pain']}

# 記事の方向性
{theme['approach']}

# 重要な制約
- 他サイトの言い換えではなく、独自の視点と構成で書くこと
- スペック羅列や表面的な解説は避け、「なぜそうなるのか」を重視
- 初心者が陥りやすい失敗パターンや判断基準を具体的に示す
- 音脳ラボの口調：やや砕けた親しみやすい語り口、専門用語は噛み砕いて説明
- 文字数：800〜1500文字程度

# 記事構成（推奨）
1. 導入（読者の悩みに共感）
2. 原因の整理（なぜその問題が起きるのか）
3. 判断ポイント（どう考えれば良いか）
4. 具体例（設定値や考え方の実例）
5. まとめ（要点の再確認と次のアクション）

# 出力形式
HTML形式で出力してください。以下のタグのみ使用：
- <h2>, <h3>（見出し）
- <p>（段落）
- <strong>（強調）
- <ul>, <li>（箇条書き）

記事本文のみを出力し、タイトルは含めないでください。
"""
        return prompt


def main():
    """メイン処理"""
    # 環境変数の読み込み
    load_dotenv()

    # 必須環境変数のチェック
    required_vars = ['CLAUDE_API_KEY', 'WP_SITE_URL', 'WP_USERNAME', 'WP_APP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        sys.exit(1)

    # 各クライアントの初期化
    theme_manager = ThemeManager()
    article_generator = ArticleGenerator(api_key=os.getenv('CLAUDE_API_KEY'))
    wp_client = WordPressClient(
        site_url=os.getenv('WP_SITE_URL'),
        username=os.getenv('WP_USERNAME'),
        app_password=os.getenv('WP_APP_PASSWORD')
    )

    # WordPress接続テスト
    print("WordPress接続をテスト中...")
    if not wp_client.test_connection():
        print("エラー: WordPressへの接続に失敗しました")
        sys.exit(1)
    print("✓ WordPress接続成功")

    # 未使用テーマの確認
    unused_count = theme_manager.get_unused_count()
    print(f"\n未使用テーマ数: {unused_count}")

    if unused_count == 0:
        print("利用可能なテーマがありません")
        sys.exit(0)

    # 次のテーマを取得
    theme = theme_manager.get_next_theme()
    print(f"\n今日のテーマ: {theme['title']}")

    # 記事生成
    print("\n記事を生成中...")
    try:
        article = article_generator.generate_article(theme)
        print("✓ 記事生成完了")
    except Exception as e:
        print(f"エラー: 記事生成に失敗しました - {e}")
        sys.exit(1)

    # WordPressに下書き投稿
    print("\nWordPressに投稿中...")
    try:
        auto_publish = os.getenv('AUTO_PUBLISH', '0') == '1'
        status = 'publish' if auto_publish else 'draft'

        result = wp_client.create_post(
            title=article['title'],
            content=article['content'],
            status=status
        )

        post_id = result['id']
        post_url = result['link']

        print(f"✓ 投稿完了")
        print(f"  投稿ID: {post_id}")
        print(f"  ステータス: {status}")
        print(f"  URL: {post_url}")

        # テーマを使用済みにマーク
        theme_manager.mark_as_used(theme['id'])
        print(f"✓ テーマID {theme['id']} を使用済みにマーク")

    except Exception as e:
        print(f"エラー: WordPress投稿に失敗しました - {e}")
        sys.exit(1)

    print("\n処理が正常に完了しました！")


if __name__ == "__main__":
    main()
