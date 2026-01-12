"""
WordPress REST APIとの連携を行うモジュール
"""
import requests
from typing import Dict, Optional
import base64


class WordPressClient:
    """WordPress REST APIクライアント"""

    def __init__(self, site_url: str, username: str, app_password: str):
        """
        Args:
            site_url: WordPressサイトのURL（例: https://example.com）
            username: WordPressユーザー名
            app_password: WordPressアプリケーションパスワード
        """
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.username = username
        self.app_password = app_password

        # Basic認証のヘッダーを準備
        credentials = f"{username}:{app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }

    def create_post(
        self,
        title: str,
        content: str,
        status: str = 'draft',
        categories: Optional[list] = None,
        tags: Optional[list] = None
    ) -> Dict:
        """
        新規投稿を作成する

        Args:
            title: 投稿タイトル
            content: 投稿本文（HTML）
            status: 投稿ステータス（draft, publish, private等）
            categories: カテゴリーIDのリスト
            tags: タグIDのリスト

        Returns:
            作成された投稿の情報

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/posts"

        post_data = {
            'title': title,
            'content': content,
            'status': status,
        }

        if categories:
            post_data['categories'] = categories

        if tags:
            post_data['tags'] = tags

        response = requests.post(
            endpoint,
            headers=self.headers,
            json=post_data
        )

        response.raise_for_status()
        return response.json()

    def get_post(self, post_id: int) -> Dict:
        """
        投稿を取得する

        Args:
            post_id: 投稿ID

        Returns:
            投稿情報

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/posts/{post_id}"

        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """
        投稿を更新する

        Args:
            post_id: 投稿ID
            title: 新しいタイトル（省略可）
            content: 新しい本文（省略可）
            status: 新しいステータス（省略可）

        Returns:
            更新された投稿情報

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/posts/{post_id}"

        post_data = {}
        if title is not None:
            post_data['title'] = title
        if content is not None:
            post_data['content'] = content
        if status is not None:
            post_data['status'] = status

        response = requests.post(
            endpoint,
            headers=self.headers,
            json=post_data
        )

        response.raise_for_status()
        return response.json()

    def upload_media(
        self,
        image_data: bytes,
        filename: str,
        alt_text: str = ""
    ) -> Dict:
        """
        メディアをアップロードする

        Args:
            image_data: 画像データ（バイナリ）
            filename: ファイル名
            alt_text: 代替テキスト

        Returns:
            アップロードされたメディア情報

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/media"

        # Content-Type を適切に設定
        headers = self.headers.copy()
        headers['Content-Type'] = 'image/jpeg'
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        response = requests.post(
            endpoint,
            headers=headers,
            data=image_data
        )

        response.raise_for_status()
        media_data = response.json()

        # alt_textを設定
        if alt_text:
            media_id = media_data['id']
            update_endpoint = f"{self.api_base}/media/{media_id}"
            requests.post(
                update_endpoint,
                headers=self.headers,
                json={'alt_text': alt_text}
            )

        return media_data

    def set_featured_image(
        self,
        post_id: int,
        media_id: int
    ) -> Dict:
        """
        投稿にアイキャッチ画像を設定する

        Args:
            post_id: 投稿ID
            media_id: メディアID

        Returns:
            更新された投稿情報

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        return self.update_post(
            post_id=post_id,
            **{'featured_media': media_id}
        )

    def get_or_create_tags(self, tag_names: list) -> list:
        """
        タグ名のリストからタグIDのリストを取得（存在しない場合は作成）

        Args:
            tag_names: タグ名のリスト

        Returns:
            タグIDのリスト
        """
        tag_ids = []
        endpoint = f"{self.api_base}/tags"

        for tag_name in tag_names:
            # 既存タグを検索
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={'search': tag_name}
            )

            if response.status_code == 200:
                tags = response.json()
                if tags and tags[0]['name'].lower() == tag_name.lower():
                    # 既存タグが見つかった
                    tag_ids.append(tags[0]['id'])
                    continue

            # タグが見つからない場合は作成
            response = requests.post(
                endpoint,
                headers=self.headers,
                json={'name': tag_name}
            )

            if response.status_code == 201:
                tag_ids.append(response.json()['id'])

        return tag_ids

    def get_all_posts(self, per_page: int = 100) -> list:
        """
        すべての投稿を取得する

        Args:
            per_page: 1ページあたりの投稿数

        Returns:
            投稿情報のリスト
        """
        endpoint = f"{self.api_base}/posts"
        all_posts = []
        page = 1

        while True:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={'per_page': per_page, 'page': page}
            )

            if response.status_code != 200:
                break

            posts = response.json()
            if not posts:
                break

            all_posts.extend(posts)
            page += 1

        return all_posts

    def test_connection(self) -> bool:
        """
        接続テストを行う

        Returns:
            接続成功時True、失敗時False
        """
        try:
            endpoint = f"{self.api_base}/posts"
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={'per_page': 1}
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"接続テスト失敗: {e}")
            return False


if __name__ == "__main__":
    # テスト実行用
    import os
    from dotenv import load_dotenv

    load_dotenv()

    client = WordPressClient(
        site_url=os.getenv('WP_SITE_URL'),
        username=os.getenv('WP_USERNAME'),
        app_password=os.getenv('WP_APP_PASSWORD')
    )

    if client.test_connection():
        print("WordPress接続成功！")
    else:
        print("WordPress接続失敗")
