"""
画像管理モジュール - Unsplashとの連携
"""
from typing import Optional, Dict
import requests
from unsplash_client import UnsplashClient
from wordpress_client import WordPressClient


class ImageManager:
    """画像取得・アップロード・設定を統合管理"""

    def __init__(
        self,
        unsplash_client: UnsplashClient,
        wordpress_client: WordPressClient
    ):
        """
        Args:
            unsplash_client: Unsplashクライアント
            wordpress_client: WordPressクライアント
        """
        self.unsplash = unsplash_client
        self.wordpress = wordpress_client

    def add_featured_image_to_post(
        self,
        post_id: int,
        keywords: list,
        fallback_keyword: str = "music production"
    ) -> Optional[int]:
        """
        投稿にアイキャッチ画像を追加する

        Args:
            post_id: WordPress投稿ID
            keywords: 検索キーワードのリスト
            fallback_keyword: フォールバックキーワード

        Returns:
            アップロードされたメディアID、失敗時はNone
        """
        # キーワードを順に試す
        search_keywords = keywords + [fallback_keyword]

        for keyword in search_keywords:
            try:
                print(f"  画像検索中: {keyword}")

                # Unsplashで画像検索
                image_info = self.unsplash.get_best_image_for_keyword(keyword)

                if not image_info:
                    print(f"    {keyword} の画像が見つかりませんでした")
                    continue

                image_id = image_info['id']
                print(f"    画像ID {image_id} を取得")
                print(f"    撮影者: {image_info['photographer']}")

                # Unsplashから画像ダウンロード
                print(f"    画像ダウンロード中...")
                image_data = self.unsplash.download_image(
                    image_url=image_info['url'],
                    download_location=image_info['download_location']
                )

                # WordPressにアップロード
                print(f"    WordPressにアップロード中...")
                filename = f"unsplash_{image_id}.jpg"
                alt_text = image_info.get('description', keyword)

                media = self.wordpress.upload_media(
                    image_data=image_data,
                    filename=filename,
                    alt_text=alt_text
                )

                media_id = media['id']
                print(f"    メディアID: {media_id}")

                # アイキャッチ画像として設定
                print(f"    アイキャッチ画像を設定中...")
                endpoint = f"{self.wordpress.api_base}/posts/{post_id}"
                response = requests.post(
                    endpoint,
                    headers=self.wordpress.headers,
                    json={'featured_media': media_id}
                )
                response.raise_for_status()

                print(f"  ✓ アイキャッチ画像設定完了")
                return media_id

            except Exception as e:
                print(f"    エラー ({keyword}): {e}")
                continue

        print("  ⚠ アイキャッチ画像の設定に失敗しました")
        return None

    def insert_images_into_content(
        self,
        content: str,
        keywords: list,
        max_images: int = 2
    ) -> str:
        """
        記事本文に画像を挿入する

        Args:
            content: 記事本文HTML
            keywords: 検索キーワードのリスト
            max_images: 挿入する画像の最大数

        Returns:
            画像が挿入された本文HTML
        """
        # 将来の拡張用
        # 見出し（<h2>）の後に画像を挿入する処理などを追加可能
        return content


if __name__ == "__main__":
    # テスト実行
    import os
    from dotenv import load_dotenv

    load_dotenv()

    unsplash = UnsplashClient(
        access_key=os.getenv('UNSPLASH_ACCESS_KEY')
    )

    wordpress = WordPressClient(
        site_url=os.getenv('WP_SITE_URL'),
        username=os.getenv('WP_USERNAME'),
        app_password=os.getenv('WP_APP_PASSWORD')
    )

    manager = ImageManager(unsplash, wordpress)

    # テスト: 画像検索
    print("画像検索テスト:")
    result = unsplash.search_images("audio mixing", per_page=1)
    if result:
        print(f"  検索成功: {len(result)}件")
    else:
        print("  検索失敗")
