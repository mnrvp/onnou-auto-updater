"""
Shutterstock API連携モジュール
"""
import requests
import base64
from typing import List, Dict, Optional


class ShutterstockClient:
    """Shutterstock APIクライアント"""

    def __init__(self, consumer_key: str, consumer_secret: str, access_token: Optional[str] = None):
        """
        Args:
            consumer_key: Shutterstock Consumer Key
            consumer_secret: Shutterstock Consumer Secret
            access_token: Shutterstock Access Token（ライセンス取得に必要）
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.api_base = "https://api.shutterstock.com/v2"

        # Basic認証のヘッダーを準備（検索用）
        credentials = f"{consumer_key}:{consumer_secret}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers_basic = {
            'Authorization': f'Basic {token}'
        }

        # OAuth認証のヘッダーを準備（ライセンス取得・ダウンロード用）
        if access_token:
            self.headers_oauth = {
                'Authorization': f'Bearer {access_token}'
            }
        else:
            self.headers_oauth = self.headers_basic

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        image_type: str = "photo"
    ) -> List[Dict]:
        """
        画像を検索する

        Args:
            query: 検索キーワード
            per_page: 取得する画像数
            image_type: 画像タイプ（photo, illustration, vector）

        Returns:
            画像情報のリスト

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        endpoint = f"{self.api_base}/images/search"

        params = {
            'query': query,
            'per_page': per_page,
            'image_type': image_type,
            'sort': 'popular',  # 人気順
            'orientation': 'horizontal'  # 横向き画像
        }

        response = requests.get(
            endpoint,
            headers=self.headers_basic,
            params=params
        )

        response.raise_for_status()
        data = response.json()

        return data.get('data', [])

    def download_image(
        self,
        image_id: str,
        size: str = "medium"
    ) -> bytes:
        """
        画像をダウンロードする

        Args:
            image_id: 画像ID
            size: 画像サイズ（small, medium, huge）

        Returns:
            画像データ（バイナリ）

        Raises:
            requests.exceptions.HTTPError: API呼び出しが失敗した場合
        """
        # ライセンス取得
        license_endpoint = f"{self.api_base}/images/licenses"
        license_data = {
            "images": [
                {
                    "image_id": image_id,
                    "subscription_id": "auto",  # 自動選択
                    "size": size
                }
            ]
        }

        license_response = requests.post(
            license_endpoint,
            headers=self.headers_oauth,
            json=license_data
        )
        license_response.raise_for_status()

        # ダウンロードURLを取得
        license_result = license_response.json()

        # デバッグ: レスポンス構造を確認
        print(f"    ライセンスレスポンス: {license_result}")

        # レスポンス構造に応じてダウンロードURLを取得
        if 'data' in license_result and len(license_result['data']) > 0:
            first_item = license_result['data'][0]
            if 'download' in first_item:
                download_url = first_item['download']['url']
            elif 'url' in first_item:
                download_url = first_item['url']
            else:
                raise ValueError(f"ダウンロードURLが見つかりません: {first_item.keys()}")
        else:
            raise ValueError(f"不正なレスポンス構造: {license_result}")

        # 画像をダウンロード
        image_response = requests.get(download_url, headers=self.headers_oauth)
        image_response.raise_for_status()

        return image_response.content

    def get_best_image_for_keyword(
        self,
        keyword: str
    ) -> Optional[Dict]:
        """
        キーワードに最適な画像を1つ取得

        Args:
            keyword: 検索キーワード

        Returns:
            画像情報（id, description, preview_url等）
        """
        try:
            results = self.search_images(keyword, per_page=1)
            if results:
                image = results[0]
                return {
                    'id': image['id'],
                    'description': image.get('description', keyword),
                    'preview_url': image['assets']['preview']['url'],
                    'photographer': image.get('contributor', {}).get('id', 'Shutterstock')
                }
        except Exception as e:
            print(f"画像検索エラー ({keyword}): {e}")

        return None


if __name__ == "__main__":
    # テスト実行
    import os
    from dotenv import load_dotenv

    load_dotenv()

    client = ShutterstockClient(
        consumer_key=os.getenv('SHUTTERSTOCK_CONSUMER_KEY'),
        consumer_secret=os.getenv('SHUTTERSTOCK_CONSUMER_SECRET')
    )

    # テスト検索
    results = client.search_images("music production", per_page=3)
    print(f"検索結果: {len(results)}件")

    for img in results:
        print(f"  ID: {img['id']}, Description: {img.get('description', 'N/A')}")
