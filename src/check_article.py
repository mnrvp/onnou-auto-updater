import os
import sys
from dotenv import load_dotenv
from wordpress_client import WordPressClient

load_dotenv()

wp_client = WordPressClient(
    site_url=os.getenv('WP_SITE_URL'),
    username=os.getenv('WP_USERNAME'),
    app_password=os.getenv('WP_APP_PASSWORD')
)

# 最新記事を取得
post = wp_client.get_post(252)

print("=== タイトル ===")
print(post['title']['rendered'])
print("\n=== 本文（HTML削除） ===")

import re
content = post['content']['rendered']
# HTMLタグを削除
content_text = re.sub(r'<[^>]+>', '', content)
# HTML実体参照をデコード
import html
content_text = html.unescape(content_text)
# 余分な空白行を削除
content_text = re.sub(r'\n\s*\n', '\n\n', content_text)

print(content_text)
