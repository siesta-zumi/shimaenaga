# coding: utf-8
"""
パターン5: フォールバック
どのパターンにも該当しない場合、ページ全体から画像を抽出
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from extractors.base import BaseExtractor


class FallbackExtractor(BaseExtractor):
    """パターン5: フォールバック"""
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """パターン5で投稿を抽出"""
        posts = []
        
        print("[INFO] .t_h/.t_b要素が見つかりません。ページ全体から画像を抽出します。")
        
        # メイン記事エリアを特定
        main_article = soup.select_one("article.post, article.article, main#main.main article, .entry-content")
        if not main_article:
            main_article = soup
        
        # 広告・RSSセクションを除外
        for ad_elem in main_article.find_all(class_=re.compile(r'(rss|ad|related|sidebar|widget|sponsor)', re.I)):
            ad_elem.decompose()
        
        # すべての画像を抽出
        all_images = []
        seen_urls = set()
        
        # 1. <img>タグから画像を抽出
        for img in main_article.find_all("img"):
            src = self.extract_img_src(img)
            if not src:
                continue
            
            # 広告判定（緩和版: 20x20以上）
            if self.is_ad_image(src, img):
                # サイズ判定を緩和
                width = img.get("width")
                height = img.get("height")
                if width and height:
                    try:
                        w = int(str(width).replace("px", ""))
                        h = int(str(height).replace("px", ""))
                        if w < 20 or h < 20:
                            continue
                    except (ValueError, TypeError):
                        pass
                else:
                    continue
            
            # 親の<a>タグを確認（フルサイズ画像へのリンク）
            parent_a = img.find_parent("a", href=True)
            if parent_a:
                href = parent_a.get("href", "")
                if any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                    src = href
            
            # URLを完全なURLに変換
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = urljoin(self.base_url, src)
            elif not src.startswith("http"):
                src = urljoin(self.base_url, src)
            
            # 重複チェック
            url_key = src.split('?')[0].lower()
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                all_images.append(("img", src, img))
        
        # 2. <a>タグから画像リンクを抽出
        for a in main_article.find_all("a", href=True):
            href = a.get("href", "")
            if not href:
                continue
            
            # 画像ファイルへのリンクか確認
            is_image_link = False
            if any(keyword in href.lower() for keyword in ["imgur.com", "i.imgur"]):
                is_image_link = True
            elif any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                is_image_link = True
            
            if is_image_link:
                # <a>タグ内に<img>タグがある場合はスキップ（既に処理済み）
                if a.find("img"):
                    continue
                
                # URLを完全なURLに変換
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = urljoin(self.base_url, href)
                elif not href.startswith("http"):
                    href = urljoin(self.base_url, href)
                
                # imgur URLを変換
                if "imgur.com" in href.lower() and "i.imgur.com" not in href.lower():
                    match = re.search(r'imgur\.com/([a-zA-Z0-9]+)', href, re.IGNORECASE)
                    if match:
                        imgur_id = match.group(1)
                        href = f"https://i.imgur.com/{imgur_id}.jpg"
                
                # 重複チェック
                url_key = href.split('?')[0].lower()
                if url_key not in seen_urls:
                    seen_urls.add(url_key)
                    all_images.append(("link", href, a))
        
        if all_images:
            posts.append({
                "header": "投稿1",
                "body": "",
                "images": all_images,
                "id": None
            })
        
        return posts
