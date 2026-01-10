"""
記事生成のメインロジック
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from theme_manager import ThemeManager
from wordpress_client import WordPressClient
from unsplash_client import UnsplashClient
from image_manager import ImageManager


class ArticleGenerator:
    """Gemini APIを使った記事生成クラス"""

    def __init__(self, api_key: str, model: str = "models/gemini-2.5-flash"):
        """
        Args:
            api_key: Google AI APIキー
            model: 使用するGeminiモデル
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

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

        # Gemini APIで記事生成
        response = self.model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.8,
                'max_output_tokens': 5000,
            }
        )

        # レスポンスから記事本文を抽出
        article_content = response.text

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
        prompt = f"""あなたは「音脳ラボ」というDTM/宅録専門ブログのベテラン編集者です。
以下のテーマで、初心者〜中級者向けの実践的かつ独自性のある記事を書いてください。

# 記事テーマ
{theme['title']}

# 読者が抱える悩み
{theme['target_pain']}

# 記事の方向性
{theme['approach']}

# 執筆の核心原則
1. **独自性**: 他サイトの言い換えは厳禁。あなた自身の経験と洞察に基づいた切り口を提示すること
2. **本質理解**: スペック羅列ではなく「なぜそうなるのか」のメカニズムを深掘りする
3. **実践重視**: 読者が今日から実践できる具体的なアクションを必ず含める
4. **失敗パターン**: 初心者が陥りやすい罠と、その回避方法を明示する
5. **判断軸の提供**: 「何を選ぶか」より「どう判断するか」の基準を示す

# 音脳ラボのトーン&マナー
- **必ず敬語を使用**（「〜です」「〜ます」「〜でしょう」）
- 親しみやすさと丁寧さのバランス（「〜ですよね」「〜なんです」など）
- 専門用語は必ず噛み砕いて説明（中学生でも理解できるレベル）
- 読者に寄り添う姿勢（「わかりますよね」「私も最初はそうでした」）
- 断定的すぎず、選択肢を示す（「絶対こうすべき」ではなく「こういう考え方もあります」）

# 避けるべき表現
❌ 「〜と言われています」（誰が言ってる？）
❌ 「一般的には〜」（具体性ゼロ）
❌ 「高品質な〜」「プロフェッショナルな〜」（抽象的すぎ）
❌ 機材スペックの羅列
❌ 「初心者向け」「おすすめ」の連呼

# 必須要素
✅ 最低1つの具体的な数値例（「リバーブは2秒」など）
✅ 失敗パターンとその理由
✅ 「今日からできること」の明示
✅ 読者の誤解を解く一文

# 記事構成（1200〜1800文字）
## 導入（150-200文字）
読者の悩みに共感し、この記事で得られることを明示

## 問題の本質（300-400文字）
なぜその問題が起きるのか、メカニズムを解説

## 判断の軸（300-400文字）
どう考えれば良いか、判断基準を提示

## 実践的アプローチ（400-500文字）
具体例と実際の設定値、失敗パターンを含む

## まとめ（100-150文字）
要点を3つ以内に凝縮し、次のアクションを提示

# 出力形式
HTML形式で出力してください。以下のタグのみ使用：
- <h2>, <h3>（見出し）
- <p>（段落）
- <strong>（強調）
- <ul>, <li>（箇条書き）

記事本文のみを出力し、タイトルは含めないでください。

# 読みやすさの重要ルール
1. **段落は短く**: 1段落は2-4文まで。長い説明は複数の<p>タグに分割すること
2. **箇条書きを活用**: 手順や要点は<ul><li>で明確に
3. **具体例は別段落**: 「例えば〜」で始まる具体例は必ず新しい<p>タグで
4. **小見出しで区切る**: 長いセクションは<h3>で細分化
5. **1文は短めに**: 接続詞で繋げすぎず、適度に文を区切る

悪い例（詰まりすぎ）：
<p>同じ「スネア」でも、叩く強さや場所によって音が全然違いますよね。リムショット（フチを叩く）、オープンリムショット、ゴーストノート（弱く叩く）など、様々な音色があります。打ち込みでも、これらの音色の違いを表現することが大切です。ほとんどのドラム音源には、ベロシティの強弱に応じて異なるサンプル（実際に録音された音）が鳴る仕組みがあるんです。</p>

良い例（読みやすい+敬語）：
<p>同じ「スネア」でも、叩く強さや場所によって音が全然違いますよね。</p>

<p>リムショット（フチを叩く）、オープンリムショット、ゴーストノート（弱く叩く）など、様々な音色があります。打ち込みでも、これらの音色の違いを表現することが大切です。</p>

<h3>ベロシティレイヤーを活用しましょう</h3>

<p>ほとんどのドラム音源には、ベロシティの強弱に応じて異なるサンプル（実際に録音された音）が鳴る仕組みがあります。これを「ベロシティレイヤー」と呼びます。</p>
"""
        return prompt


def main():
    """メイン処理"""
    # 環境変数の読み込み
    load_dotenv()

    # 必須環境変数のチェック
    required_vars = ['GEMINI_API_KEY', 'WP_SITE_URL', 'WP_USERNAME', 'WP_APP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        sys.exit(1)

    # 各クライアントの初期化
    theme_manager = ThemeManager()
    article_generator = ArticleGenerator(api_key=os.getenv('GEMINI_API_KEY'))
    wp_client = WordPressClient(
        site_url=os.getenv('WP_SITE_URL'),
        username=os.getenv('WP_USERNAME'),
        app_password=os.getenv('WP_APP_PASSWORD')
    )

    # 画像機能の初期化（Unsplashが設定されている場合のみ）
    image_manager = None
    if os.getenv('UNSPLASH_ACCESS_KEY'):
        unsplash_client = UnsplashClient(
            access_key=os.getenv('UNSPLASH_ACCESS_KEY')
        )
        image_manager = ImageManager(unsplash_client, wp_client)
        print("✓ Unsplash画像機能が有効です")
    else:
        print("⚠ Unsplash設定なし - 画像なしで投稿します")

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

    # 記事本文に画像を挿入（現在無効）
    # if image_manager:
    #     print("\n記事本文に画像を挿入中...")
    #     try:
    #         keywords = theme.get('keywords', [])
    #         article['content'] = image_manager.insert_images_into_content(
    #             content=article['content'],
    #             keywords=keywords,
    #             max_images=2
    #         )
    #     except Exception as e:
    #         print(f"⚠ 本文画像挿入エラー: {e}")
    #         print("  画像なしで続行します")

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

        # アイキャッチ画像を追加（画像機能が有効な場合）
        if image_manager:
            print("\nアイキャッチ画像を追加中...")
            try:
                keywords = theme.get('keywords', [])
                image_manager.add_featured_image_to_post(
                    post_id=post_id,
                    keywords=keywords
                )
            except Exception as e:
                print(f"⚠ 画像追加エラー: {e}")
                print("  画像なしで続行します")

        # テーマを使用済みにマーク
        theme_manager.mark_as_used(theme['id'])
        print(f"✓ テーマID {theme['id']} を使用済みにマーク")

    except Exception as e:
        print(f"エラー: WordPress投稿に失敗しました - {e}")
        sys.exit(1)

    print("\n処理が正常に完了しました！")


if __name__ == "__main__":
    main()
