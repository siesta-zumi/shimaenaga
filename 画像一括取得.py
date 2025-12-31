# coding: utf-8
"""
画像一括取得システム
バージョン: 2.0.0
"""
import os
import re
import shutil
import sys
import requests
from urllib.parse import urljoin
from typing import List, Dict, Tuple, Optional

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright

# バージョン情報
try:
    from version import VERSION, get_version
    __version__ = VERSION
except ImportError:
    __version__ = "2.0.0"
    def get_version():
        return __version__

# Windows環境でのUnicodeエラーを防ぐ
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# EXE実行時のPlaywrightブラウザパス設定
# PyInstallerでビルドされた場合、システムのブラウザを使用
if getattr(sys, 'frozen', False):
    # EXEとして実行されている場合
    PLAYWRIGHT_BROWSERS_PATH = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "ms-playwright"
    )
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_PATH

# ----------------------------------------
# 画像ダウンロード用の HTTP セッション
# ----------------------------------------
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/120.0 Safari/537.36"
})
TIMEOUT = 10


def is_ad_image(img_url: str, img_tag: Tag, parent_elem: Optional[Tag] = None) -> bool:
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


def extract_img_src(img_tag: Tag) -> Optional[str]:
    for attr in ["src", "data-src", "data-original", "data-lazy", "data-image"]:
        val = img_tag.get(attr)
        if val:
            return val
    return None


def extract_images_from_element(elem: Tag) -> List[str]:
    """
    Extract all image URLs from an element, including:
    - <img> tags
    - <a> links to image files (imgur, etc.)
    - <iframe> tags (imgur embeds)
    重複を避けるため、画像IDで重複チェック
    2段階処理: まず<img>を収集、次に<a>を処理（同一投稿内での重複を回避）
    """
    image_urls = []
    seen_ids = set()  # 画像IDでの重複チェック用
    
    def extract_image_id(url: str) -> str:
        """Extract unique image ID from URL (e.g., nKqZYrk from any URL containing it)"""
        import re
        # Try to extract imgur-style ID (alphanumeric, typically 7 chars)
        # Also handle livedoor blog image formats like: 9df4f32a-s.jpg and 9df4f32a.jpg
        # Also handle tabinolog formats like: /imgs/a314e997-s.jpg
        # Pattern: /id-suffix.ext or /id.ext (match the last path segment before extension)
        # Try multiple patterns
        patterns = [
            r'/([a-zA-Z0-9]{7,})(?:-[a-z0-9]+)?\.(?:jpg|jpeg|png|gif|webp)',  # Original pattern
            r'/([a-zA-Z0-9]{7,})\.(?:jpg|jpeg|png|gif|webp)',  # Without suffix
            r'([a-zA-Z0-9]{7,})(?:-[a-z0-9]+)?\.(?:jpg|jpeg|png|gif|webp)',  # Without leading slash
        ]
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        # Fallback to full URL
        return url.split('?')[0].lower()
    
    # Collect local image URLs (from <img> tags) and imgur URLs separately
    local_images = []  # (url, img_tag)
    imgur_urls_in_post = []  # (url, element)
    
    # STEP 1: Extract from <img> tags
    for img in elem.find_all("img"):
        src = extract_img_src(img)
        if src:
            # Check if ad image (親要素を渡してスレッド本文内かどうかを判定)
            is_ad = is_ad_image(src, img, elem)
            # デバッグ: 最初の数件のみ
            if len(local_images) + len(imgur_urls_in_post) < 3:
                print(f"[DEBUG] extract_images_from_element STEP1: Found <img> with src={src}, is_ad={is_ad}")
            
            if is_ad:
                if len(local_images) + len(imgur_urls_in_post) < 3:
                    print(f"[DEBUG] extract_images_from_element STEP1: Skipped ad image")
                continue
            
            # Check if this <img> is wrapped by an <a> tag pointing to a full-size image
            parent_a = img.find_parent("a", href=True)
            if parent_a:
                href = parent_a.get("href", "")
                # Check if the href points to an image file
                if any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                    # Use the <a> href (full-size) instead of <img> src (thumbnail)
                    src = href
                    if len(local_images) + len(imgur_urls_in_post) < 3:
                        print(f"[DEBUG] extract_images_from_element STEP1: Using parent <a> href: {src}")
            
            # Store for later prioritization
            if "imgur" in src.lower():
                imgur_urls_in_post.append((src, img))
                if len(imgur_urls_in_post) <= 3:
                    print(f"[DEBUG] extract_images_from_element STEP1: Added to imgur_urls_in_post: {src}")
            else:
                local_images.append((src, img))
                if len(local_images) <= 3:
                    print(f"[DEBUG] extract_images_from_element STEP1: Added to local_images: {src}")
    
    # STEP 2: Extract from <iframe> tags (imgur embeds)
    for iframe in elem.find_all("iframe"):
        src = iframe.get("src", "")
        if "imgur.com" in src.lower():
            # Extract imgur ID from embed URL
            # Format: https://imgur.com/xN0u202/embed?context=...
            import re
            match = re.search(r'imgur\.com/([a-zA-Z0-9]{7,})(?:/|$)', src, re.IGNORECASE)
            if match:
                imgur_id = match.group(1)
                # Convert to direct image URL
                direct_url = f"https://i.imgur.com/{imgur_id}.jpg"
                imgur_urls_in_post.append((direct_url, iframe))
    
    # STEP 3: Extract from <a> tags
    for a in elem.find_all("a", href=True):
        href = a.get("href", "")
        
        # Skip if this is inside an RSS/ad area
        parent_classes = ' '.join(a.parent.get('class', [])) if a.parent else ''
        if any(keyword in parent_classes.lower() for keyword in ['rss', 'ad', 'related', 'sidebar', 'widget']):
            continue
        
        # Check if link points to an image
        is_image_link = False
        if any(keyword in href.lower() for keyword in ["imgur.com", "i.imgur"]):
            is_image_link = True
        elif any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            is_image_link = True
        
        if is_image_link:
            # Check if this <a> contains an <img> tag
            has_img_inside = bool(a.find("img"))
            
            if has_img_inside:
                # This <a> wraps an <img>, skip to avoid duplicate
                # (the <img> was already processed in STEP 1)
                continue
            
            # Check if the link text is a URL
            link_text = a.get_text(strip=True)
            is_url_text = link_text.startswith('http://') or link_text.startswith('https://')
            
            # If the link text is a URL, collect it for prioritization
            if is_url_text:
                is_imgur_url = "imgur" in href.lower()
                if is_imgur_url:
                    # Imgur URL text - add to imgur list
                    imgur_urls_in_post.append((href, a))
                else:
                    # Non-imgur URL text → skip (rarely useful)
                    continue
            else:
                # Not a URL text → regular image link
                img_id = extract_image_id(href)
                if img_id not in seen_ids:
                    seen_ids.add(img_id)
                    image_urls.append(("link", href, a))
    
    # STEP 4: Add both local and imgur for 404 fallback
    # Simple approach: Add all candidates, download will handle 404 naturally
    # If local fails (404), imgur will be tried as next image
    
    # Add local images first (primary source)
    for local_url, local_elem in local_images:
        local_id = extract_image_id(local_url)
        # デバッグ: 最初の数件のみ
        if len(image_urls) < 3:
            print(f"[DEBUG] extract_images_from_element STEP4: Processing local image URL: {local_url}")
            print(f"[DEBUG] extract_images_from_element STEP4: Extracted image ID: {local_id}")
            print(f"[DEBUG] extract_images_from_element STEP4: Seen IDs: {list(seen_ids)}")
        
        if local_id not in seen_ids:
            seen_ids.add(local_id)
            image_urls.append(("img", local_url, local_elem))
            if len(image_urls) <= 3:
                print(f"[DEBUG] extract_images_from_element STEP4: Added to image_urls: {local_url}")
        # デバッグ: 最初の数件のみ
        elif len(image_urls) < 3:
            print(f"[DEBUG] extract_images_from_element STEP4: Skipped duplicate local image ID: {local_id} (URL: {local_url})")
    
    # Add imgur URLs (fallback source - only if NOT already added)
    for imgur_url, imgur_elem in imgur_urls_in_post:
        imgur_id = extract_image_id(imgur_url)
        if imgur_id not in seen_ids:
            seen_ids.add(imgur_id)
            elem_type = "iframe" if imgur_elem.name == "iframe" else "img"
            image_urls.append((elem_type, imgur_url, imgur_elem))
        # デバッグ: 最初の数件のみ
        elif len(image_urls) < 3:
            print(f"[DEBUG] extract_images_from_element: Skipped duplicate imgur image ID: {imgur_id} (URL: {imgur_url})")
    
    # デバッグ: 最終的な結果を確認
    if len(local_images) > 0 or len(imgur_urls_in_post) > 0:
        if len(image_urls) == 0:
            print(f"[DEBUG] extract_images_from_element: Found {len(local_images)} local images and {len(imgur_urls_in_post)} imgur images, but returned 0 images")
            if len(local_images) > 0:
                first_local_url = local_images[0][0]
                first_local_id = extract_image_id(first_local_url)
                print(f"[DEBUG]   First local image URL: {first_local_url}")
                print(f"[DEBUG]   First local image ID: {first_local_id}")
                print(f"[DEBUG]   Seen IDs: {list(seen_ids)[:5]}")
    
    return image_urls


def clean_text_from_images(elem: Tag) -> str:
    elem_copy = BeautifulSoup(str(elem), "html.parser")
    
    # Remove ad/RSS sections
    for ad_elem in elem_copy.find_all(class_=re.compile(r'(rss|ad|related|sidebar|widget)', re.I)):
        ad_elem.decompose()
    
    # Remove specific ad text patterns
    for div in elem_copy.find_all(['div', 'p', 'span']):
        text = div.get_text()
        if any(keyword in text for keyword in ['記事の途中ですが', 'RSS', '関連記事', 'スポンサー', '広告']):
            div.decompose()
    
    for img in elem_copy.find_all("img"):
        img.decompose()
    
    for a in elem_copy.find_all("a"):
        href = a.get("href", "")
        text = a.get_text()
        if any(keyword in href.lower() for keyword in ["imgur.com", "i.imgur", ".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            a.decompose()
        elif any(keyword in text.lower() for keyword in ["imgur.com", "i.imgur", ".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            a.decompose()
    
    text = elem_copy.get_text("\n", strip=True)
    text = re.sub(r'https?://[^\s]*(?:imgur\.com|i\.imgur)[^\s]*', '', text)
    text = re.sub(r'https?://[^\s]*\.(?:jpg|jpeg|png|gif|webp)[^\s]*', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def normalize_title(raw: str) -> str:
    if not raw:
        return "post"

    title = raw.strip()
    title = re.sub(r'[\\/:*?"<>|\s。、，．・]+', "_", title)
    title = title.strip("_")
    if not title:
        title = "post"
    return title[:50]


def extract_id_from_text(text: str) -> Optional[str]:
    match = re.search(r'ID:([A-Za-z0-9]+)', text)
    if match:
        return match.group(1)
    return None


def detect_thread_creator_ids(soup: BeautifulSoup, first_post_id: Optional[str]) -> List[str]:
    op_ids = set()
    
    if first_post_id:
        op_ids.add(first_post_id)
    
    op_elements = soup.find_all(class_=re.compile(r'(op|thread-creator|author|postauthor)', re.I))
    for elem in op_elements:
        text = elem.get_text()
        post_id = extract_id_from_text(text)
        if post_id:
            op_ids.add(post_id)
    
    return sorted(list(op_ids))


def parse_response_header(header_text: str) -> Dict[str, str]:
    result = {
        "number": "",
        "name": "",
        "datetime": "",
        "id": "",
        "full": header_text.strip()
    }
    
    num_match = re.match(r'^(\d+):', header_text)
    if num_match:
        result["number"] = num_match.group(1)
    
    id_match = re.search(r'ID:([A-Za-z0-9]+)', header_text)
    if id_match:
        result["id"] = id_match.group(1)
    
    return result


def scrape_single_url_js(url: str, result_root: str, browser) -> Tuple[bool, str, int]:
    try:
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
        except Exception:
            pass
    except Exception as e:
        return False, f"[ERROR] Page load failed: {url}\n{e}"

    try:
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)
        
        last_height = page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        
        for _ in range(20):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:
                    break
            else:
                scroll_attempts = 0
            last_height = new_height
        
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
    except Exception:
        pass

    # Capture Twitter/X embeds as screenshots before getting HTML
    twitter_screenshots = []
    try:
        # Wait a bit more for Twitter iframes to load
        page.wait_for_timeout(2000)
        
        # Get all iframe elements
        iframe_elements = page.query_selector_all("iframe")
        
        for i, iframe_elem in enumerate(iframe_elements):
            try:
                iframe_src = iframe_elem.get_attribute("src")
                # Check if this is a Twitter/X embed (Tweet.html, not widgets)
                if iframe_src:
                    lower_src = iframe_src.lower()
                    is_twitter_embed = "twitter.com/embed/tweet.html" in lower_src
                    
                    if is_twitter_embed:
                        # Scroll element into view first
                        try:
                            iframe_elem.scroll_into_view_if_needed(timeout=5000)
                            page.wait_for_timeout(1000)
                        except Exception:
                            pass
                        
                        # Take screenshot of this iframe
                        screenshot_bytes = iframe_elem.screenshot(timeout=10000)
                        twitter_screenshots.append(("twitter_embed", screenshot_bytes))
            except Exception:
                continue
    except Exception:
        pass

    try:
        html = page.content()
    finally:
        page.close()

    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.title.get_text(strip=True) if soup.title else "post"
    folder_name = normalize_title(title_tag)
    folder = os.path.join(result_root, folder_name)

    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

    img_folder = os.path.join(folder, "images")
    os.makedirs(img_folder, exist_ok=True)

    # パターン選択ロジックを使用して投稿を抽出
    try:
        from extractors.pattern_loader import extract_posts_from_page
        posts = extract_posts_from_page(soup, session, url)
    except ImportError as e:
        print(f"[ERROR] Failed to import extractors.pattern_loader: {e}")
        print("[ERROR] Please ensure extractors/ folder exists with all required modules.")
        posts = []
        article = soup.select_one("article, .article-body, .entry-content, #article-body")
        
        if article:
            elements = article.find_all(['div', 'p', 'blockquote'], recursive=False)
            
            current_header = ""
            current_body_parts = []
            current_imgs = []
            current_id = None
            
            for elem in elements:
                elem_text = elem.get_text(strip=True)
                
                # Check if this is a response header (starts with number:)
                if elem_text and re.match(r'^\d+:', elem_text):
                    # Save previous post
                    if current_header:
                        posts.append({
                            "header": current_header,
                            "body": "\n".join([p for p in current_body_parts if p]),
                            "images": list(current_imgs),
                            "id": current_id
                        })
                    
                    # New response header
                    current_header = elem_text
                    parsed = parse_response_header(elem_text)
                    current_id = parsed["id"]
                    current_body_parts = []
                    current_imgs = []
                    continue
                
                # If we have a current header, collect body and images
                if current_header:
                    # Collect images
                    for img in elem.find_all("img"):
                        current_imgs.append(img)
                    
                    # Collect text (excluding image URLs)
                    body_text = clean_text_from_images(elem)
                    if body_text and body_text != current_header:
                        current_body_parts.append(body_text)
            
            # Save last post
            if current_header:
                posts.append({
                    "header": current_header,
                    "body": "\n".join([p for p in current_body_parts if p]),
                    "images": list(current_imgs),
                    "id": current_id
                })

    # 旧コード（参考用）:
    # Pattern 3: Old oryouri.2chblog.jp format (dl/dt/dd structure)
    if False and not posts:
        # Look for dl > dt (header) and dd (body) pattern
        dl_elements = soup.find_all('dl')
        
        for dl in dl_elements:
            dt_elements = dl.find_all('dt', recursive=False)
            dd_elements = dl.find_all('dd', recursive=False)
            
            # Process dt/dd pairs
            for dt in dt_elements:
                header_text = dt.get_text(strip=True)
                
                # Check if this looks like a response header
                if header_text and re.match(r'^\d+:', header_text):
                    parsed = parse_response_header(header_text)
                    
                    # Find corresponding dd (next sibling)
                    dd = dt.find_next_sibling('dd')
                    
                    body_parts = []
                    imgs = []
                    
                    if dd:
                        # Collect images
                        for img in dd.find_all("img"):
                            imgs.append(img)
                        
                        # Collect text
                        body_text = clean_text_from_images(dd)
                        if body_text:
                            body_parts.append(body_text)
                    
                    posts.append({
                        "header": header_text,
                        "body": "\n".join(body_parts),
                        "images": imgs,
                        "id": parsed["id"]
                    })

    if not posts:
        # デバッグ情報をファイルに保存
        debug_log_path = os.path.join(folder, "debug_log.txt")
        with open(debug_log_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n")
            f.write(f"Title: {title_tag}\n\n")
            f.write("Available classes in page (first 50):\n")
            all_classes = []
            for elem in soup.find_all(class_=True):
                for cls in elem.get('class', []):
                    if cls not in all_classes:
                        all_classes.append(cls)
            f.write("\n".join(all_classes[:50]))
        
        post_path = os.path.join(folder, "posts.txt")
        with open(post_path, "w", encoding="utf-8") as f:
            f.write("Could not extract thread structure from this page.")
        return True, f"[WARN] No thread structure: {url} -> {folder} (see debug_log.txt for details)", 0

    first_post_id = posts[0]["id"] if posts else None
    op_ids = detect_thread_creator_ids(soup, first_post_id)

    image_counter = 1
    image_mapping = {}
    downloaded_image_ids = set()  # Track downloaded images by ID to avoid duplicates
    
    # Save Twitter/X embed screenshots first
    twitter_image_files = []
    for i, (embed_type, screenshot_bytes) in enumerate(twitter_screenshots, 1):
        filename = f"画像{image_counter}.png"
        filepath = os.path.join(img_folder, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(screenshot_bytes)
            twitter_image_files.append(filename)
            image_counter += 1
        except Exception:
            pass
    
    def get_image_id_from_url(url: str) -> str:
        """Extract image ID from URL for duplicate checking"""
        import re
        # Handle various image URL formats:
        # - imgur: /nKqZYrk.jpg, /nKqZYrk-640x480.jpg, /nKqZYrk-scaled.jpg
        # - livedoor: /9df4f32a.jpg, /9df4f32a-s.jpg (thumbnail)
        # - tabinolog: /filename-640x480.jpg, /filename-scaled.jpg
        match = re.search(r'/([a-zA-Z0-9]{7,})(?:-[a-z0-9]+)?\.(?:jpg|jpeg|png|gif|webp)', url, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return url.split('?')[0].lower()
    
    # Download images with 404 fallback logic
    # Strategy: For each post, try local first, if 404 then try imgur
    image_mapping = {}
    
    for post_idx, post in enumerate(posts):
        # Separate local and imgur images for this post
        local_imgs = []
        imgur_imgs = []
        
        # デバッグ: 最初の数レスのみ
        if post_idx < 3:
            print(f"[DEBUG] Processing post {post_idx+1}: {len(post['images'])} images in post['images']")
        
        for img_data in post["images"]:
            if isinstance(img_data, tuple) and len(img_data) == 3:
                img_type, src, img_element = img_data
                # URL解決のデバッグログ
                if src:
                    original_src = src
                    full_url = urljoin(url, src)
                    # デバッグ: URL解決の確認（最初の数件のみ）
                    if post_idx < 3 and len(local_imgs) + len(imgur_imgs) < 3:
                        print(f"[DEBUG] Image URL resolution: '{original_src}' -> '{full_url}'")
                else:
                    full_url = None
                
                if full_url:
                    # Categorize by source
                    if "imgur" in full_url.lower():
                        imgur_imgs.append((img_type, full_url, img_element))
                    else:
                        local_imgs.append((img_type, full_url, img_element))
        
        # デバッグ: 最初の数レスのみ
        if post_idx < 3:
            print(f"[DEBUG] Post {post_idx+1}: {len(local_imgs)} local images, {len(imgur_imgs)} imgur images")
        
        # Process each local image with imgur fallback
        max_imgs = max(len(local_imgs), len(imgur_imgs))
        
        for i in range(max_imgs):
            local_img = local_imgs[i] if i < len(local_imgs) else None
            imgur_img = imgur_imgs[i] if i < len(imgur_imgs) else None
            
            downloaded = False
            
            # Try local first
            if local_img:
                img_type, full_url, img_element = local_img
                img_id = get_image_id_from_url(full_url)
                
                if img_id not in downloaded_image_ids:
                    # Skip ads (親要素情報がないため、img_elementから親を取得)
                    parent_for_ad_check = img_element.parent if hasattr(img_element, 'parent') else None
                    if not (img_type == "img" and is_ad_image(full_url, img_element, parent_for_ad_check)):
                        ext = os.path.splitext(full_url.split("?")[0])[1].lower()
                        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                            ext = ".jpg"
                        
                        filename = f"画像{image_counter}{ext}"
                        filepath = os.path.join(img_folder, filename)
                        
                        try:
                            resp = session.get(full_url, timeout=TIMEOUT)
                            resp.raise_for_status()
                            with open(filepath, "wb") as f:
                                f.write(resp.content)
                            
                            image_mapping[full_url] = filename
                            downloaded_image_ids.add(img_id)
                            image_counter += 1
                            downloaded = True
                        except requests.exceptions.HTTPError as e:
                            # 404エラーなどのHTTPエラーをログに記録（最初の数件のみ）
                            if image_counter <= 3:
                                print(f"[DEBUG] Failed to download local image (HTTP {e.response.status_code}): {full_url}")
                        except Exception as e:
                            # その他のエラーをログに記録（最初の数件のみ）
                            if image_counter <= 3:
                                print(f"[DEBUG] Failed to download local image: {full_url} - {type(e).__name__}")
                            pass  # Local failed, will try imgur fallback
            
            # If local failed or doesn't exist, try imgur
            if not downloaded and imgur_img:
                img_type, full_url, img_element = imgur_img
                img_id = get_image_id_from_url(full_url)
                
                if img_id not in downloaded_image_ids:
                    ext = os.path.splitext(full_url.split("?")[0])[1].lower()
                    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                        ext = ".jpg"
                    
                    filename = f"画像{image_counter}{ext}"
                    filepath = os.path.join(img_folder, filename)
                    
                    try:
                        resp = session.get(full_url, timeout=TIMEOUT)
                        resp.raise_for_status()
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
                        
                        image_mapping[full_url] = filename
                        downloaded_image_ids.add(img_id)
                        image_counter += 1
                    except requests.exceptions.HTTPError as e:
                        # 404エラーなどのHTTPエラーをログに記録（最初の数件のみ）
                        if image_counter <= 3:
                            print(f"[DEBUG] Failed to download imgur image (HTTP {e.response.status_code}): {full_url}")
                    except Exception as e:
                        # その他のエラーをログに記録（最初の数件のみ）
                        if image_counter <= 3:
                            print(f"[DEBUG] Failed to download imgur image: {full_url} - {type(e).__name__}")
                        pass  # Both failed, skip this image



    lines = []
    
    lines.append(title_tag)
    for op_id in op_ids:
        lines.append(f"ID:{op_id}")
    lines.append("")
    
    # Add Twitter/X embed screenshots at the beginning
    if twitter_image_files:
        lines.append("=== X（Twitter）投稿 ===")
        for twitter_img in twitter_image_files:
            lines.append(twitter_img)
        lines.append("")
    
    for post in posts:
        lines.append(post["header"])
        
        for img_data in post["images"]:
            # img_data is tuple: (type, url, element)
            if isinstance(img_data, tuple) and len(img_data) == 3:
                img_type, src, img_element = img_data
                full_url = urljoin(url, src) if src else None
            else:
                # Fallback
                src = extract_img_src(img_data) if hasattr(img_data, 'get') else None
                full_url = urljoin(url, src) if src else None
            
            if full_url and full_url in image_mapping:
                lines.append(image_mapping[full_url])
        
        if post["body"]:
            lines.append(post["body"])
        
        lines.append("")

    post_path = os.path.join(folder, "posts.txt")
    with open(post_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    image_count = image_counter - 1
    return True, f"[OK] {url} -> {folder} (Posts: {len(posts)}, Images: {image_count}, OP IDs: {len(op_ids)})", image_count


def main():
    # バージョン情報を表示
    print(f"=== 画像一括取得システム v{get_version()} ===")
    print()
    
    root_dir = os.getcwd()
    urls_file = os.path.join(root_dir, "urls.txt")
    result_root = os.path.join(root_dir, "result_js")

    if not os.path.exists(result_root):
        os.makedirs(result_root, exist_ok=True)

    if not os.path.exists(urls_file):
        print("urls.txt not found. Please place it in the same folder as this script.")
        return

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs found in urls.txt.")
        return

    logs = []
    failed_urls = []  # 画像が取得できなかったURLを記録

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for url in urls:
            try:
                print(f"Processing -> {url}")
                result = scrape_single_url_js(url, result_root, browser)
                
                # 戻り値の形式を確認（後方互換性のため）
                if isinstance(result, tuple) and len(result) == 3:
                    ok, msg, image_count = result
                else:
                    ok, msg = result
                    # メッセージから画像数を抽出
                    image_match = re.search(r'Images: (\d+)', msg)
                    image_count = int(image_match.group(1)) if image_match else 0
                
                logs.append(msg)
                print(msg)
                
                # 画像が0枚の場合、フォールバック対象として記録
                if image_count == 0:
                    failed_urls.append(url)
                    print(f"[WARN] No images found for {url}, will try fallback script")
            except Exception as e:
                error_msg = f"[ERROR] Unexpected error: {url}\n{str(e)}"
                logs.append(error_msg)
                print(error_msg)
                failed_urls.append(url)
        browser.close()

    log_path = os.path.join(result_root, "log_js.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(logs))

    print("\n=== Scraping completed ===")
    print(f"Check result_js folder: {result_root}")
    
    # 画像が取得できなかったURLの情報を表示
    if failed_urls:
        print(f"\n=== {len(failed_urls)} URL(s) failed to get images ===")
        print("These URLs may require a new extraction pattern.")
        print("Please check the logs and consider adding a new pattern to extractors/")
        for url in failed_urls:
            print(f"  - {url}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n=== エラーが発生しました ===")
        print(f"エラー内容: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nEnterキーを押して終了してください...")
