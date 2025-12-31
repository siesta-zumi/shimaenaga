# coding: utf-8
"""
抽出パターンの基底クラスと共通ユーティリティ
"""

import re
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup, Tag
import requests
from urllib.parse import urljoin


class BaseExtractor:
    """抽出パターンの基底クラス"""
    
    def __init__(self, session: requests.Session, base_url: str):
        """
        Args:
            session: HTTPセッション
            base_url: ベースURL
        """
        self.session = session
        self.base_url = base_url
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """
        ページから投稿を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
        
        Returns:
            投稿のリスト。各投稿は以下のキーを持つ辞書:
            - header: レスヘッダー（例: "1: 名無しさん＠おーぷん 25/03/23(日) 08:24:57 ID:od5C"）
            - body: 本文
            - images: 画像のリスト [(type, url, element), ...]
            - id: レスID（スレ主判定用）
        """
        raise NotImplementedError("Subclasses must implement extract()")
    
    def extract_img_src(self, img_tag: Tag) -> Optional[str]:
        """画像のsrc属性を取得（data-src等にも対応）"""
        for attr in ["src", "data-src", "data-original", "data-lazy", "data-image"]:
            val = img_tag.get(attr)
            if val:
                return val
        return None
    
    def is_ad_image(self, img_url: str, img_tag: Tag, parent_elem: Optional[Tag] = None) -> bool:
        """
        広告画像かどうかを判定する
        
        Args:
            img_url: 画像URL
            img_tag: 画像タグ要素
            parent_elem: 親要素（.t_b要素など、スレッド本文内かどうかの判定に使用）
        
        Returns:
            True: 広告画像と判定された場合
            False: 広告画像ではない場合
        """
        if not img_url:
            return True

        # スレッド本文内（.t_b要素内）の画像は広告判定を緩和
        is_in_thread_body = False
        if parent_elem:
            # 親要素が.t_bクラスを持つか確認
            parent_classes = parent_elem.get("class", [])
            if "t_b" in parent_classes:
                is_in_thread_body = True
            else:
                # 親要素の親も確認（ネストされた構造に対応）
                parent_parent = parent_elem.parent
                if parent_parent:
                    parent_parent_classes = parent_parent.get("class", [])
                    if "t_b" in parent_parent_classes:
                        is_in_thread_body = True

        lower = img_url.lower()
        bad_keywords = [
            "/ads/", "adservice", "doubleclick", "tracking",
            "banner", "/banners/", "affiliate", "googleads",
            "ad-", "-ad.", "/ad.", ".ad/", "adsense", "adsbygoogle"
        ]
        if any(k in lower for k in bad_keywords):
            # スレッド本文内でもURLに広告キーワードが含まれる場合は除外
            return True

        # スレッド本文内の画像はサイズ判定を緩和
        width = img_tag.get("width")
        height = img_tag.get("height")
        if width and height:
            try:
                w = int(str(width).replace("px", ""))
                h = int(str(height).replace("px", ""))
                # スレッド本文内の画像は最小サイズの閾値を下げる（30x30以上）
                min_size = 30 if is_in_thread_body else 50
                if w < min_size or h < min_size:
                    return True
            except (ValueError, TypeError):
                pass

        classes = " ".join(img_tag.get("class", [])).lower()
        img_id = (img_tag.get("id") or "").lower()
        
        bad_class_keywords = ["ad", "banner", "sponsor", "promo", "advertisement"]
        if any(k in classes for k in bad_class_keywords):
            # スレッド本文内でもクラス名に広告キーワードが含まれる場合は除外
            return True
        
        if any(k in img_id for k in bad_class_keywords):
            return True

        return False
    
    def extract_images_from_element(self, elem: Tag) -> List[Tuple[str, str, Tag]]:
        """
        要素から画像URLを抽出
        
        Args:
            elem: BeautifulSoup要素
        
        Returns:
            [(type, url, element), ...] のリスト
            type: "img", "link", "iframe" のいずれか
        """
        image_urls = []
        seen_ids = set()
        
        def extract_image_id(url: str) -> str:
            """画像IDを抽出（重複チェック用）"""
            patterns = [
                r'/([a-zA-Z0-9]{7,})(?:-[a-z0-9]+)?\.(?:jpg|jpeg|png|gif|webp)',
                r'/([a-zA-Z0-9]{7,})\.(?:jpg|jpeg|png|gif|webp)',
                r'([a-zA-Z0-9]{7,})(?:-[a-z0-9]+)?\.(?:jpg|jpeg|png|gif|webp)',
            ]
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    return match.group(1).lower()
            return url.split('?')[0].lower()
        
        # STEP 1: <img>タグから抽出
        local_images = []
        imgur_urls_in_post = []
        
        for img in elem.find_all("img"):
            src = self.extract_img_src(img)
            if not src:
                continue
            
            # 相対URLを絶対URLに変換
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = urljoin(self.base_url, src)
            elif not src.startswith("http"):
                src = urljoin(self.base_url, src)
            
            # 広告判定
            if self.is_ad_image(src, img, elem):
                continue
            
            local_images.append((src, img))
            
            # Imgur URLの検出
            if "imgur" in src.lower():
                imgur_urls_in_post.append((src, img))
        
        # STEP 2: <a>タグから画像リンクを抽出
        for a in elem.find_all("a", href=True):
            href = a.get("href", "")
            if not href:
                continue
            
            # 相対URLを絶対URLに変換
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = urljoin(self.base_url, href)
            elif not href.startswith("http"):
                href = urljoin(self.base_url, href)
            
            # 画像ファイルの拡張子をチェック
            is_image_link = any(href.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
            
            # Imgur URLのチェック
            if "imgur" in href.lower() and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                is_image_link = True
            
            if is_image_link:
                # <a>内に<img>がある場合はスキップ（重複回避）
                if a.find("img"):
                    continue
                
                # リンクテキストがURLの場合はスキップ
                link_text = a.get_text(strip=True)
                if link_text.startswith('http://') or link_text.startswith('https://'):
                    if "imgur" in href.lower():
                        imgur_urls_in_post.append((href, a))
                    continue
                
                img_id = extract_image_id(href)
                if img_id not in seen_ids:
                    seen_ids.add(img_id)
                    image_urls.append(("link", href, a))
        
        # STEP 3: <iframe>タグからImgur埋め込みを抽出
        for iframe in elem.find_all("iframe"):
            src = iframe.get("src", "")
            if not src:
                continue
            
            if "imgur" in src.lower():
                # Imgur埋め込みURLを画像URLに変換
                imgur_id_match = re.search(r'imgur\.com/([a-zA-Z0-9]+)', src)
                if imgur_id_match:
                    imgur_id = imgur_id_match.group(1)
                    imgur_url = f"https://i.imgur.com/{imgur_id}.jpg"
                    imgur_urls_in_post.append((imgur_url, iframe))
        
        # STEP 4: ローカル画像を追加
        for local_url, local_elem in local_images:
            local_id = extract_image_id(local_url)
            if local_id not in seen_ids:
                seen_ids.add(local_id)
                image_urls.append(("img", local_url, local_elem))
        
        # STEP 5: Imgur URLを追加（重複チェック）
        for imgur_url, imgur_elem in imgur_urls_in_post:
            imgur_id = extract_image_id(imgur_url)
            if imgur_id not in seen_ids:
                seen_ids.add(imgur_id)
                elem_type = "iframe" if imgur_elem.name == "iframe" else "img"
                image_urls.append((elem_type, imgur_url, imgur_elem))
        
        return image_urls
    
    def clean_text_from_images(self, elem: Tag) -> str:
        """要素から画像を除去してテキストのみを抽出"""
        from bs4 import BeautifulSoup
        elem_copy = BeautifulSoup(str(elem), "html.parser")
        
        # 広告/RSSセクションを除去
        for ad_elem in elem_copy.find_all(class_=re.compile(r'(rss|ad|related|sidebar|widget)', re.I)):
            ad_elem.decompose()
        
        # 特定の広告テキストパターンを除去
        for div in elem_copy.find_all(['div', 'p', 'span']):
            text = div.get_text()
            if any(keyword in text for keyword in ['記事の途中ですが', 'RSS', '関連記事', 'スポンサー', '広告']):
                div.decompose()
        
        # 画像を除去
        for img in elem_copy.find_all("img"):
            img.decompose()
        
        # リンクのテキストのみを保持
        for a in elem_copy.find_all("a"):
            href = a.get("href", "")
            if href and (href.startswith("http://") or href.startswith("https://")):
                a.decompose()
            else:
                a.unwrap()
        
        return elem_copy.get_text(" ", strip=True)
    
    def parse_response_header(self, header_text: str) -> Dict[str, Optional[str]]:
        """
        レスヘッダーを解析してIDを抽出
        
        Args:
            header_text: レスヘッダーのテキスト（例: "1: 名無しさん＠おーぷん 25/03/23(日) 08:24:57 ID:od5C"）
        
        Returns:
            {"id": "od5C", "name": "名無しさん＠おーぷん", ...} の辞書
        """
        result = {
            "id": None,
            "name": None,
            "date": None,
            "number": None
        }
        
        # ID抽出: "ID:xxxx" パターン
        id_match = re.search(r'ID[:\s]+([a-zA-Z0-9]+)', header_text)
        if id_match:
            result["id"] = id_match.group(1)
        
        # 名前抽出: IDの前の部分
        if result["id"]:
            name_match = re.search(r'(\d+):\s*([^0-9]+?)\s+\d+/\d+/\d+', header_text)
            if name_match:
                result["name"] = name_match.group(2).strip()
                result["number"] = name_match.group(1)
        
        return result
