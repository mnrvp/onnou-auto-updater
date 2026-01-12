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

    # WordPressカテゴリマッピング
    CATEGORY_MAP = {
        'DTM': 7,
        'ミキシング＆マスタリング': 8,
        '作曲・編曲': 9,
        '歌い手活動': 1
    }

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
                'max_output_tokens': 8000,  # 2000-3000文字対応
            }
        )

        # レスポンスからタイトル、説明、タグ、本文を抽出
        full_response = response.text

        import re
        # より柔軟なパターン（改行や空白を許容）
        title_match = re.search(r'\[TITLE\]\s*(.*?)\s*\[/TITLE\]', full_response, re.DOTALL)
        description_match = re.search(r'\[DESCRIPTION\]\s*(.*?)\s*\[/DESCRIPTION\]', full_response, re.DOTALL)
        tags_match = re.search(r'\[TAGS\]\s*(.*?)\s*\[/TAGS\]', full_response, re.DOTALL)
        content_match = re.search(r'\[CONTENT\]\s*(.*?)\s*\[/CONTENT\]', full_response, re.DOTALL)

        print(f"  デバッグ: TITLE抽出={bool(title_match)}, CONTENT抽出={bool(content_match)}")

        if title_match and content_match:
            article_title = title_match.group(1).strip()
            article_description = description_match.group(1).strip() if description_match else ""
            article_tags = tags_match.group(1).strip() if tags_match else ""
            article_content = content_match.group(1).strip()
            print(f"  ✓ タイトル抽出成功: {article_title[:50]}...")
        else:
            # フォーマットが正しくない場合はフォールバック
            print("  ⚠ タイトル抽出失敗、テーマタイトルを使用")
            print(f"  デバッグ: レスポンス先頭200文字: {full_response[:200]}")
            article_title = theme['title']
            article_description = ""
            article_tags = ""
            article_content = full_response

        return {
            'title': article_title,
            'description': article_description,
            'tags': article_tags,
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
✅ **最低2-3個の具体的な数値例**（「EQは100Hzで-3dB」「リバーブは2秒」など）
✅ **失敗パターンと成功パターンの対比**
✅ **「今日からできること」の明示**（ステップバイステップで）
✅ **読者の誤解を解く一文**
✅ **専門用語の深堀り説明**（なぜそうなるのか、物理・音響的な理由）
✅ **プロの現場での実例**（「実際の制作現場では〜」など）

# 記事構成（2000〜3000文字）
## 導入（200-300文字）
読者の悩みに共感し、この記事で得られることを明示。問題の重要性を強調

## 問題の本質（500-700文字）
なぜその問題が起きるのか、**音響学的・物理的メカニズム**を深掘り解説
専門用語を使いつつ、必ず噛み砕いて説明

## 判断の軸（400-600文字）
どう考えれば良いか、判断基準を提示
**失敗例と成功例を対比**して理解を深める

## 実践的アプローチ（800-1000文字）
具体例を**最低2-3個**含める
- 実際の設定値（数値を明記）
- 手順をステップバイステップで
- 失敗パターンと回避方法
- プロの現場での実例やコツ

## まとめ（150-200文字）
要点を3つ以内に凝縮し、次のアクションを提示
「今日から試せること」を具体的に

# SEO最適化タイトルの作成
まず、テーマに基づいてSEO最適化されたタイトルを生成してください。

## タイトルのパターン（以下のいずれかを選択）

**パターン1: 年号＋数字系**
- 【2026年版】〜初心者が絶対にハマるN個の落とし穴｜後悔しないための〜
- 【最新版】知らないと損するN個の〜｜プロが教える〜

**パターン2: ノウハウ系**
- 【保存版】〜で差がつくN個のテクニック｜〜が教える実践的手順
- 【完全ガイド】〜を劇的に改善するN個の方法｜初心者でもできる〜

**パターン3: 問題解決系**
- 〜できない原因はコレ！即効で改善するN個のチェックポイント
- 〜が〜しない理由とは？今すぐ試せるN個の解決策

**パターン4: 比較・選び方系**
- 〜と〜の違いとは？初心者でも分かる使い分け完全ガイド
- 【徹底比較】〜選びで失敗しないN個のポイント｜2026年最新版

## タイトル作成のルール
1. **具体的な数字を入れる（N個、N つなど）** ← **超重要：タイトルに含める数字は、記事本文で実際に説明する項目数と必ず一致させること**
2. ターゲット明確（初心者、DTMer、宅録派など）
3. ベネフィット明示（後悔しない、差がつく、劇的に改善など）
4. 強い言葉を使う（絶対に、即効、完全、徹底など）
5. 30〜40文字程度

**注意：タイトルで「5つの〜」と書いたら、本文でも必ず5つ説明すること。数字の不一致は絶対に避けること！**

# メタディスクリプションの作成
記事の内容を120文字程度で要約したメタディスクリプションを作成してください。
- 検索結果に表示される文章
- 記事の核心的な価値を伝える
- アクションを促す表現（「〜を解説」「〜がわかる」など）

# タグの自動生成
記事内容に関連するタグを5-10個生成してください。
- 具体的なキーワード（「ミックス」「EQ」「コンプレッサー」など）
- 検索されやすい用語
- カンマ区切りで出力

# 出力形式
以下の形式で**必ず守って**出力してください：

[TITLE]
SEO最適化されたタイトルをここに
[/TITLE]

[DESCRIPTION]
120文字程度のメタディスクリプション
[/DESCRIPTION]

[TAGS]
タグ1,タグ2,タグ3,タグ4,タグ5
[/TAGS]

[CONTENT]
HTML形式の記事本文（以下のタグのみ使用）：
- <h2>, <h3>（見出し）
- <p>（段落）
- <strong>（強調）
- <ul>, <li>（箇条書き）
[/CONTENT]

# 読みやすさの重要ルール
1. **段落は短く**: 1段落は2-4文まで。長い説明は複数の<p>タグに分割すること
2. **空の段落で余白を作る**: 段落と段落の間、見出しの前後、リストの前後には空の<p>&nbsp;</p>を入れて視覚的な余白を作ること
3. **箇条書きを活用**: 手順や要点は<ul><li>で明確に
4. **具体例は別段落**: 「例えば〜」で始まる具体例は必ず新しい<p>タグで
5. **小見出しで区切る**: 長いセクションは<h3>で細分化
6. **1文は短めに**: 接続詞で繋げすぎず、適度に文を区切る

悪い例（詰まりすぎ）：
<p>同じ「スネア」でも、叩く強さや場所によって音が全然違いますよね。リムショット（フチを叩く）、オープンリムショット、ゴーストノート（弱く叩く）など、様々な音色があります。打ち込みでも、これらの音色の違いを表現することが大切です。ほとんどのドラム音源には、ベロシティの強弱に応じて異なるサンプル（実際に録音された音）が鳴る仕組みがあるんです。</p>

良い例（読みやすい+余白あり）：
<p>同じ「スネア」でも、叩く強さや場所によって音が全然違いますよね。</p>

<p>&nbsp;</p>

<p>リムショット（フチを叩く）、オープンリムショット、ゴーストノート（弱く叩く）など、様々な音色があります。打ち込みでも、これらの音色の違いを表現することが大切です。</p>

<p>&nbsp;</p>

<h3>ベロシティレイヤーを活用しましょう</h3>

<p>&nbsp;</p>

<p>ほとんどのドラム音源には、ベロシティの強弱に応じて異なるサンプル（実際に録音された音）が鳴る仕組みがあります。これを「ベロシティレイヤー」と呼びます。</p>

# 出力例
[TITLE]
モノラルで音が消える原因はコレ！即効で改善する5つのチェックポイント
[/TITLE]

[DESCRIPTION]
ステレオでは問題ないのにモノラルで音が消える位相の問題を徹底解説。原因のメカニズムから具体的な確認方法、5つの改善ポイントまで、初心者でもすぐ実践できる内容をプロが伝授します。
[/DESCRIPTION]

[TAGS]
ミキシング,位相,モノラル,ステレオ,DTM,音が消える,トラブル対処,初心者向け
[/TAGS]

[CONTENT]
<h2>モノラルで聴くと音が消える現象</h2>
<p>ステレオで聴いた時は問題ないのに、モノラルにすると特定の音が消えたり小さくなったりする...。</p>
...（記事本文）...
[/CONTENT]
"""
        return prompt

    def determine_category(self, title: str, theme: dict) -> int:
        """
        記事タイトルとテーマからカテゴリを判定する

        Args:
            title: 記事タイトル
            theme: テーマ情報

        Returns:
            カテゴリID
        """
        prompt = f"""あなたはDTM/宅録専門ブログのカテゴリ分類担当です。

以下の記事タイトルとテーマから、最も適切なカテゴリを1つ選んでください。

# 記事タイトル
{title}

# テーマ情報
悩み: {theme.get('target_pain', '')}
アプローチ: {theme.get('approach', '')}

# カテゴリ選択肢
1. DTM - 機材、ソフトウェア、DAW、プラグイン、環境設定、PC/Mac関連
2. ミキシング＆マスタリング - ミックス技術、マスタリング、音量調整、EQ、コンプレッサー、エフェクト処理
3. 作曲・編曲 - 作曲理論、編曲技術、音楽理論、コード進行、メロディ作成、アレンジ
4. 歌い手活動 - ボーカル録音、歌唱技術、マイク選び、ボーカルミックス、歌ってみた

# 判定基準
- 記事の**主な内容**がどのカテゴリに最も近いか
- 複数のカテゴリに該当する場合は、最も中心的なテーマを選ぶ
- 例：「ボーカルが引っ込む」→ ミキシングの問題なので「ミキシング＆マスタリング」
- 例：「モノラルで音が消える」→ 位相の問題、ミックス技術なので「ミキシング＆マスタリング」
- 例：「DTMに必要な機材」→ 機材選びなので「DTM」
- 例：「コード進行の作り方」→ 作曲理論なので「作曲・編曲」

**カテゴリ名だけを出力してください。説明は不要です。**

出力例：
ミキシング＆マスタリング
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={'temperature': 0.3}
            )
            category_name = response.text.strip()

            # カテゴリ名からIDを取得
            category_id = self.CATEGORY_MAP.get(category_name)

            if category_id:
                print(f"  カテゴリ判定: {category_name} (ID: {category_id})")
                return category_id
            else:
                print(f"  ⚠ カテゴリ判定失敗: '{category_name}' は未定義")
                print(f"  デフォルトカテゴリ「歌い手活動」を使用")
                return 1  # デフォルト: 歌い手活動

        except Exception as e:
            print(f"  ⚠ カテゴリ判定エラー: {e}")
            print(f"  デフォルトカテゴリ「歌い手活動」を使用")
            return 1  # デフォルト: 歌い手活動

    def add_internal_links(self, content: str, title: str, existing_posts: list, max_links: int = 2) -> str:
        """
        記事本文に内部リンクを挿入する

        Args:
            content: 記事本文（HTML）
            title: 記事タイトル
            existing_posts: 既存記事のリスト [{'title': ..., 'link': ...}, ...]
            max_links: 挿入する最大リンク数

        Returns:
            内部リンクを挿入した記事本文
        """
        if not existing_posts or len(existing_posts) < 3:
            return content  # 既存記事が少ない場合はスキップ

        # 既存記事のタイトル一覧を作成
        posts_list = "\n".join([f"- {post['title']}" for post in existing_posts[:30]])  # 最大30件

        prompt = f"""あなたは内部リンク最適化の専門家です。

# 現在の記事タイトル
{title}

# 既存記事一覧（最大30件）
{posts_list}

# タスク
上記の既存記事の中から、現在の記事と**最も関連性が高い記事を{max_links}個**選んでください。

# 選定基準
1. テーマの関連性（同じジャンル、関連技術）
2. 読者の次のアクションとして自然
3. 補完関係（現在の記事で触れていないが関連する内容）

# 出力形式
関連記事のタイトルを{max_links}個、改行区切りで出力してください。タイトルだけを出力し、説明は不要です。

出力例:
ボーカルミックスで差がつく7つのテクニック
コンプレッサーの使い方完全ガイド
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={'temperature': 0.3}
            )
            related_titles = [line.strip() for line in response.text.strip().split('\n') if line.strip()]

            # 選ばれた記事のリンクを取得
            related_posts = []
            for post in existing_posts:
                if post['title'] in related_titles:
                    related_posts.append(post)
                if len(related_posts) >= max_links:
                    break

            if not related_posts:
                return content

            # 記事本文の末尾に関連記事セクションを追加
            links_html = "\n\n<h2>あわせて読みたい</h2>\n<ul>\n"
            for post in related_posts:
                links_html += f'<li><a href="{post["link"]}">{post["title"]}</a></li>\n'
            links_html += "</ul>"

            # contentの末尾に追加
            return content + links_html

        except Exception as e:
            print(f"  ⚠ 内部リンク生成エラー: {e}")
            return content


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

    # カテゴリバランスを表示
    try:
        recent_posts = wp_client.get_all_posts(per_page=10)
        if recent_posts:
            from collections import Counter
            category_counts = Counter()
            category_names = {7: 'DTM', 8: 'ミキシング＆マスタリング', 9: '作曲・編曲', 1: '歌い手活動'}

            for post in recent_posts:
                for cat_id in post.get('categories', []):
                    if cat_id in category_names:
                        category_counts[category_names[cat_id]] += 1

            if category_counts:
                print(f"\n直近10記事のカテゴリ分布:")
                for cat_name, count in category_counts.most_common():
                    print(f"  {cat_name}: {count}記事")
    except Exception as e:
        print(f"  ⚠ カテゴリバランス表示エラー: {e}")

    # 未使用テーマの確認
    unused_count = theme_manager.get_unused_count()
    print(f"\n未使用テーマ数: {unused_count}")

    # テーマが3個以下の場合、自動で3個追加
    if unused_count <= 3:
        print(f"\nテーマが少なくなっています（残り{unused_count}個）")
        print("新しいテーマを自動生成中...")
        try:
            new_themes = theme_manager.generate_new_themes(
                api_key=os.getenv('GEMINI_API_KEY'),
                count=3
            )
            theme_manager.add_themes(new_themes)

            # 生成されたテーマを表示
            print("\n生成されたテーマ:")
            for theme in new_themes:
                print(f"  - {theme['title']}")

            unused_count = theme_manager.get_unused_count()
            print(f"\n更新後の未使用テーマ数: {unused_count}")
        except Exception as e:
            print(f"⚠ テーマ自動生成エラー: {e}")
            print("  既存のテーマで続行します")

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

    # カテゴリを判定
    print("\nカテゴリを判定中...")
    try:
        category_id = article_generator.determine_category(
            title=article['title'],
            theme=theme
        )
    except Exception as e:
        print(f"  ⚠ カテゴリ判定エラー: {e}")
        category_id = 1  # デフォルト: 歌い手活動

    # タグを処理
    tag_ids = []
    if article.get('tags'):
        print("\nタグを処理中...")
        try:
            tag_names = [tag.strip() for tag in article['tags'].split(',')]
            tag_ids = wp_client.get_or_create_tags(tag_names)
            print(f"  ✓ {len(tag_ids)}個のタグを設定")
        except Exception as e:
            print(f"  ⚠ タグ処理エラー: {e}")

    # 内部リンクを追加
    print("\n内部リンクを追加中...")
    try:
        existing_posts = wp_client.get_all_posts(per_page=30)
        if existing_posts:
            posts_data = [{'title': post['title']['rendered'], 'link': post['link']} for post in existing_posts]
            article['content'] = article_generator.add_internal_links(
                content=article['content'],
                title=article['title'],
                existing_posts=posts_data,
                max_links=2
            )
            print(f"  ✓ 既存記事{len(existing_posts)}件から関連記事を選定")
        else:
            print(f"  ⚠ 既存記事が見つからないためスキップ")
    except Exception as e:
        print(f"  ⚠ 内部リンク追加エラー: {e}")

    # WordPressに下書き投稿
    print("\nWordPressに投稿中...")
    try:
        auto_publish = os.getenv('AUTO_PUBLISH', '0') == '1'
        status = 'publish' if auto_publish else 'draft'

        result = wp_client.create_post(
            title=article['title'],
            content=article['content'],
            status=status,
            categories=[category_id],
            tags=tag_ids if tag_ids else None
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
