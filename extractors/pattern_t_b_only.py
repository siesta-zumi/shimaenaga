# coding: utf-8
"""
パターン2: .t_b のみ（.t_h要素が存在しない）
tabinolog.comなど、.t_b要素のみが存在するサイト用
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from extractors.base import BaseExtractor


class T_B_OnlyExtractor(BaseExtractor):
    """パターン2: .t_b のみ"""
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """パターン2で投稿を抽出"""
        posts = []
        
        # メイン記事エリアを特定
        main_article = soup.select_one("article.post, article.article, main#main.main article, .entry-content")
        if not main_article:
            main_article = soup
        
        # .t_b要素を探す
        t_b_elements = main_article.select(".t_b")
        
        if not t_b_elements:
            return posts
        
        print("[INFO] .t_h要素が見つかりません。.t_b要素から直接抽出を試みます。")
        
        # .t_b要素ごとに投稿を作成
        for t_b in t_b_elements:
            # 広告セクションをスキップ
            elem_text = t_b.get_text(strip=True)
            is_ad_section = any(marker in elem_text for marker in [
                '記事の途中ですが',
                'グルメRSS',
                '大人含むRSS',
                'スポンサーリンク'
            ])
            if is_ad_section:
                continue
            
            # 本文を抽出
            body_text = self.clean_text_from_images(t_b)
            if not body_text:
                continue
            
            # この.t_b要素内の画像を抽出
            image_data_list = self.extract_images_from_element(t_b)
            images = []
            for img_type, img_url, img_element in image_data_list:
                images.append((img_type, img_url, img_element))
            
            # 投稿番号を抽出（本文から）
            header_match = re.search(r'^(\d+):', body_text)
            if header_match:
                post_num = header_match.group(1)
                header_text = f"{post_num}: {body_text[:100]}"
            else:
                header_text = body_text[:50]
            
            parsed = self.parse_response_header(header_text)
            
            posts.append({
                "header": header_text,
                "body": body_text,
                "images": images,
                "id": parsed["id"]
            })
        
        return posts
