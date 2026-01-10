"""
記事テーマの管理を行うモジュール
"""
import json
import os
from typing import Dict, Optional, List
import google.generativeai as genai


class ThemeManager:
    """記事テーマの選定と管理を行うクラス"""

    def __init__(self, themes_file: str = None):
        """
        Args:
            themes_file: テーマデータのJSONファイルパス
        """
        if themes_file is None:
            # プロジェクトルートのdataフォルダを参照
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            themes_file = os.path.join(project_root, "data", "themes.json")

        self.themes_file = themes_file
        self.themes_data = self._load_themes()

    def _load_themes(self) -> Dict:
        """テーマデータを読み込む"""
        if not os.path.exists(self.themes_file):
            raise FileNotFoundError(f"テーマファイルが見つかりません: {self.themes_file}")

        with open(self.themes_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_themes(self) -> None:
        """テーマデータを保存する"""
        with open(self.themes_file, 'w', encoding='utf-8') as f:
            json.dump(self.themes_data, f, ensure_ascii=False, indent=2)

    def get_next_theme(self) -> Optional[Dict]:
        """
        未使用の次のテーマを取得する

        Returns:
            テーマ情報の辞書。全て使用済みの場合はNone
        """
        themes = self.themes_data.get('themes', [])

        for theme in themes:
            if not theme.get('used', False):
                return theme

        return None

    def mark_as_used(self, theme_id: int) -> None:
        """
        テーマを使用済みとしてマークする

        Args:
            theme_id: テーマID
        """
        themes = self.themes_data.get('themes', [])

        for theme in themes:
            if theme.get('id') == theme_id:
                theme['used'] = True
                self._save_themes()
                return

        raise ValueError(f"テーマID {theme_id} が見つかりません")

    def get_unused_count(self) -> int:
        """
        未使用のテーマ数を取得する

        Returns:
            未使用のテーマ数
        """
        themes = self.themes_data.get('themes', [])
        return sum(1 for theme in themes if not theme.get('used', False))

    def reset_all_themes(self) -> None:
        """全てのテーマを未使用状態にリセットする（管理用）"""
        themes = self.themes_data.get('themes', [])

        for theme in themes:
            theme['used'] = False

        self._save_themes()

    def generate_new_themes(self, api_key: str, count: int = 5, model: str = "models/gemini-2.5-flash") -> List[Dict]:
        """
        AIで新しいテーマを自動生成する

        Args:
            api_key: Gemini APIキー
            count: 生成するテーマ数
            model: 使用するGeminiモデル

        Returns:
            生成されたテーマのリスト
        """
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel(model)

        # 現在のテーマを参考にして新しいテーマを生成
        existing_themes = self.themes_data.get('themes', [])
        max_id = max([t['id'] for t in existing_themes]) if existing_themes else 0

        prompt = f"""あなたは「音脳ラボ」というDTM/宅録専門ブログのテーマ企画担当です。
初心者〜中級者向けの実践的な記事テーマを{count}個提案してください。

# 既存テーマ（重複厳禁）
{chr(10).join([f"- {t['title']}" for t in existing_themes[:5]])}

# テーマ条件
1. 初心者の具体的な悩みに焦点
2. 「なぜ」を解明する内容
3. 失敗パターン・勘違いを解消
4. DTM/宅録/ミックス/マスタリング分野
5. 初心者でも興味を持てる

# 重要：完全で正しいJSON配列のみ出力
以下の形式で{count}個を出力：

[
  {{"title":"タイトル","keywords":["keyword1","keyword2","keyword3","keyword4"],"target_pain":"悩み","approach":"解決策"}},
  {{"title":"タイトル","keywords":["keyword1","keyword2","keyword3","keyword4"],"target_pain":"悩み","approach":"解決策"}}
]

注意：
- JSON配列のみ出力（説明不要）
- keywordsは英語
- titleは短く簡潔に（40文字以内）
- target_painとapproachも簡潔に（各50文字以内）
"""

        response = gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.9,
                'max_output_tokens': 3000,
            }
        )

        # JSONをパース
        import re
        response_text = response.text.strip()

        # コードブロックを削除（```json ... ``` の形式）
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        try:
            new_themes_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"レスポンス: {response_text}")
            raise

        # IDとusedフラグを追加
        new_themes = []
        for i, theme_data in enumerate(new_themes_data):
            theme = {
                'id': max_id + i + 1,
                'title': theme_data['title'],
                'keywords': theme_data['keywords'],
                'target_pain': theme_data['target_pain'],
                'approach': theme_data['approach'],
                'used': False
            }
            new_themes.append(theme)

        return new_themes

    def add_themes(self, new_themes: List[Dict]) -> None:
        """
        新しいテーマをthemes.jsonに追加する

        Args:
            new_themes: 追加するテーマのリスト
        """
        self.themes_data['themes'].extend(new_themes)
        self._save_themes()
        print(f"✓ {len(new_themes)}個の新しいテーマを追加しました")


if __name__ == "__main__":
    # テスト実行
    manager = ThemeManager()

    print(f"未使用テーマ数: {manager.get_unused_count()}")

    next_theme = manager.get_next_theme()
    if next_theme:
        print(f"\n次のテーマ:")
        print(f"  ID: {next_theme['id']}")
        print(f"  タイトル: {next_theme['title']}")
        print(f"  対象の悩み: {next_theme['target_pain']}")
    else:
        print("\n利用可能なテーマがありません")
