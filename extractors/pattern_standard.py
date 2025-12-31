# coding: utf-8
"""
パターン1: .t_h / .t_b 構造（標準パターン）
旅のろぐなど、標準的な構造を持つサイト用
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup, Tag

from extractors.base import BaseExtractor


class StandardExtractor(BaseExtractor):
    """標準パターン: .t_h / .t_b 構造"""
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """標準パターンで投稿を抽出"""
        posts = []
        
        # メイン記事要素を探す
        main_article_selectors = [
            "article.post",
            "article.article", 
            "main#main.main article",
            "article",
            ".entry-content",
            ".article-body",
            "#main article"
        ]
        
        main_article = None
        for selector in main_article_selectors:
            main_article = soup.select_one(selector)
            if main_article:
                break
        
        if main_article:
            # メイン記事内で .t_h / .t_b を探す
            inner_selectors = [
                ".entry-content .t_h, .entry-content .t_b",
                ".article-body .t_h, .article-body .t_b",
                ".t_h, .t_b",
                "div.t_h, div.t_b",
            ]
            
            targets = None
            for selector in inner_selectors:
                targets = main_article.select(selector)
                if targets:
                    break
        else:
            # フォールバック: より広いセレクターで探す
            selectors_to_try = [
                ".article-body .t_h, .article-body .t_b",
                ".entry-content .t_h, .entry-content .t_b",
                ".t_h, .t_b",
                "div.t_h, div.t_b",
                "article .t_h, article .t_b",
                "main .t_h, main .t_b"
            ]
            
            for selector in selectors_to_try:
                targets = soup.select(selector)
                if targets:
                    break
        
        if not targets:
            return posts
        
        # .t_h要素と.t_b要素をペアとして再構築
        processed_targets = []
        pending_t_b = None
        
        for i, elem in enumerate(targets):
            classes = elem.get("class", [])
            
            if "t_h" in classes:
                # .t_h要素が見つかったら、保留中の.t_b要素があれば処理
                if pending_t_b:
                    processed_targets.append(("t_b", pending_t_b))
                    pending_t_b = None
                processed_targets.append(("t_h", elem))
            elif "t_b" in classes:
                # .t_b要素が見つかったら、次の.t_h要素を待つか、現在の.t_h要素に関連付ける
                if i + 1 < len(targets):
                    next_classes = targets[i + 1].get("class", [])
                    if "t_h" in next_classes:
                        # 次の要素が.t_h要素の場合、この.t_b要素を保留
                        pending_t_b = elem
                        continue
                # 次の要素が.t_h要素でない場合、現在の.t_h要素に関連付ける
                processed_targets.append(("t_b", elem))
        
        # 最後の保留中の.t_b要素を処理
        if pending_t_b:
            processed_targets.append(("t_b", pending_t_b))
        
        # 投稿を構築
        current_header_full = ""
        current_body_parts = []
        current_imgs = []
        current_id = None

        for elem_type, elem in processed_targets:
            if elem_type == "t_h":
                # 前の投稿を保存
                if current_header_full:
                    posts.append({
                        "header": current_header_full,
                        "body": "\n".join(current_body_parts),
                        "images": list(current_imgs),
                        "id": current_id
                    })

                # 新しい投稿の開始
                current_header_full = elem.get_text(" ", strip=True)
                parsed = self.parse_response_header(current_header_full)
                current_id = parsed["id"]
                current_body_parts = []
                current_imgs = []

            elif elem_type == "t_b":
                # .t_h要素がない場合の処理（通常は発生しないが、念のため）
                if not current_header_full:
                    elem_text = elem.get_text(strip=True)
                    header_match = re.search(r'^(\d+):', elem_text)
                    if header_match:
                        post_num = header_match.group(1)
                        current_header_full = f"{post_num}: {elem_text[:50]}"
                        parsed = self.parse_response_header(current_header_full)
                        current_id = parsed["id"]
                    else:
                        continue
                
                # 広告/RSSセクションをスキップ
                elem_text = elem.get_text(strip=True)
                is_ad_section = any(marker in elem_text for marker in [
                    '記事の途中ですが',
                    'グルメRSS',
                    '大人含むRSS',
                    'スポンサーリンク'
                ])
                
                if is_ad_section:
                    continue
                
                # 画像を収集
                image_data_list = self.extract_images_from_element(elem)
                for img_type, img_url, img_element in image_data_list:
                    current_imgs.append((img_type, img_url, img_element))
                
                # 本文を収集
                body_text = self.clean_text_from_images(elem)
                if body_text:
                    current_body_parts.append(body_text)

        # 最後の投稿を保存
        if current_header_full:
            posts.append({
                "header": current_header_full,
                "body": "\n".join(current_body_parts),
                "images": list(current_imgs),
                "id": current_id
            })

        return posts
