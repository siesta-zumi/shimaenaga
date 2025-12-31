# coding: utf-8
"""
パターン3: Generic 2ch blog format
oryouri.2chblog.jpなど、汎用的な2chまとめブログ形式用
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor


class Generic2chExtractor(BaseExtractor):
    """パターン3: Generic 2ch blog format"""
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """パターン3で投稿を抽出"""
        posts = []
        
        article = soup.select_one("article, .article-body, .entry-content, #article-body")
        
        if not article:
            return posts
        
        elements = article.find_all(['div', 'p', 'blockquote'], recursive=False)
        
        current_header = ""
        current_body_parts = []
        current_imgs = []
        current_id = None
        
        for elem in elements:
            elem_text = elem.get_text(strip=True)
            
            # レスヘッダーかどうかをチェック（数字:で始まる）
            if elem_text and re.match(r'^\d+:', elem_text):
                # 前の投稿を保存
                if current_header:
                    posts.append({
                        "header": current_header,
                        "body": "\n".join([p for p in current_body_parts if p]),
                        "images": list(current_imgs),
                        "id": current_id
                    })
                
                # 新しいレスヘッダー
                current_header = elem_text
                parsed = self.parse_response_header(elem_text)
                current_id = parsed["id"]
                current_body_parts = []
                current_imgs = []
                continue
            
            # 現在のヘッダーがある場合、本文と画像を収集
            if current_header:
                # 画像を収集
                image_data_list = self.extract_images_from_element(elem)
                for img_type, img_url, img_element in image_data_list:
                    current_imgs.append((img_type, img_url, img_element))
                
                # 本文を収集（画像URLを除外）
                body_text = self.clean_text_from_images(elem)
                if body_text and body_text != current_header:
                    current_body_parts.append(body_text)
        
        # 最後の投稿を保存
        if current_header:
            posts.append({
                "header": current_header,
                "body": "\n".join([p for p in current_body_parts if p]),
                "images": list(current_imgs),
                "id": current_id
            })
        
        return posts
