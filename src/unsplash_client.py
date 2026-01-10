"""
Unsplash API連携モジュール
"""
import requests
from typing import List, Dict, Optional


class UnsplashClient:
    """Unsplash APIクライアント"""

    def __init__(self, access_key: str):
        """
        Args:
            access_key: Unsplash Access Key
        """
        self.access_key = access_key
        self.api_base = "https://api.unsplash.com"
        self.headers = {
            'Authorization': f'Client-ID {access_key}'
        }

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape"
    ) -> List[Dict]:
        """
        画像を検索する

        Args:
            query: 検索キーワード
            per_page: 取得する画像数
            orientation: 画像の向き（landscape, portrait, squarish）

        Returns:
            画像情報のリスト

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/search/photos"

        params = {
            'query': query,
            'per_page': per_page,
            'orientation': orientation
        }

        response = requests.get(
            endpoint,
            headers=self.headers,
            params=params
        )

        response.raise_for_status()
        data = response.json()

        return data.get('results', [])

    def download_image(
        self,
        image_url: str,
        download_location: Optional[str] = None
    ) -> bytes:
        """
        画像をダウンロードする

        Args:
            image_url: 画像URL
            download_location: ダウンロードトラッキング用URL（Unsplash規約）

        Returns:
            画像データ（バイナリ）

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        # Unsplash規約：ダウンロードをトラッキング
        if download_location:
            try:
                requests.get(download_location)
            except Exception:
                pass  # トラッキング失敗しても画像取得は続行

        # 画像をダウンロード
        response = requests.get(image_url)
        response.raise_for_status()

        return response.content

    def get_best_image_for_keyword(
        self,
        keyword: str
    ) -> Optional[Dict]:
        """
        キーワードに最適な画像を1つ取得

        Args:
            keyword: 検索キーワード

        Returns:
            画像情報（id, description, url, download_location等）
        """
        try:
            results = self.search_images(keyword, per_page=1)
            if results:
                image = results[0]
                return {
                    'id': image['id'],
                    'description': image.get('alt_description') or image.get('description') or keyword,
                    'url': image['urls']['regular'],  # 1080px幅の画像
                    'download_location': image['links']['download_location'],
                    'photographer': image['user']['name'],
                    'photographer_url': image['user']['links']['html']
                }
        except Exception as e:
            print(f"画像検索エラー ({keyword}): {e}")

        return None


if __name__ == "__main__":
    # テスト実行
    import os
    from dotenv import load_dotenv

    load_dotenv()

    client = UnsplashClient(
        access_key=os.getenv('UNSPLASH_ACCESS_KEY')
    )

    # テスト検索
    results = client.search_images("music production", per_page=3)
    print(f"検索結果: {len(results)}件")

    for img in results:
        print(f"  ID: {img['id']}, Description: {img.get('alt_description', 'N/A')}")
