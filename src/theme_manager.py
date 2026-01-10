"""
記事テーマの管理を行うモジュール
"""
import json
import os
from typing import Dict, Optional


class ThemeManager:
    """記事テーマの選定と管理を行うクラス"""

    def __init__(self, themes_file: str = "data/themes.json"):
        """
        Args:
            themes_file: テーマデータのJSONファイルパス
        """
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
