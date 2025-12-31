# coding: utf-8
"""
パターン4: dl/dt/dd structure
古いoryouri.2chblog.jp形式など、dl/dt/dd構造を持つサイト用
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor


class DlDtDdExtractor(BaseExtractor):
    """パターン4: dl/dt/dd structure"""
    
    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """パターン4で投稿を抽出"""
        posts = []
        
        # dl要素を探す
        dl_elements = soup.find_all('dl')
        
        for dl in dl_elements:
            dt_elements = dl.find_all('dt', recursive=False)
            dd_elements = dl.find_all('dd', recursive=False)
            
            # dt要素とdd要素をペアで処理
            for i, dt in enumerate(dt_elements):
                dt_text = dt.get_text(strip=True)
                
                # レスヘッダーかどうかをチェック（数字:で始まる）
                if not re.match(r'^\d+:', dt_text):
                    continue
                
                # 対応するdd要素を取得
                dd = dd_elements[i] if i < len(dd_elements) else None
                
                # ヘッダーを解析
                parsed = self.parse_response_header(dt_text)
                
                # 画像を収集
                images = []
                if dd:
                    image_data_list = self.extract_images_from_element(dd)
                    for img_type, img_url, img_element in image_data_list:
                        images.append((img_type, img_url, img_element))
                    
                    # 本文を収集
                    body_text = self.clean_text_from_images(dd)
                else:
                    body_text = ""
                
                posts.append({
                    "header": dt_text,
                    "body": body_text,
                    "images": images,
                    "id": parsed["id"]
                })
        
        return posts
