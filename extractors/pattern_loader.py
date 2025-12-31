# coding: utf-8
"""
パターンローダー
動的にパターンモジュールを読み込む
"""

import importlib
from typing import Optional, Type
from bs4 import BeautifulSoup
import requests

from extractors.base import BaseExtractor
from extractors.pattern_detector import (
    detect_extraction_pattern,
    get_extractor_module_name,
    get_extractor_class_name
)


def load_extractor(pattern: str, session: requests.Session, base_url: str) -> Optional[BaseExtractor]:
    """
    パターン名から抽出器を動的に読み込む
    
    Args:
        pattern: パターン名（例: "pattern_standard"）
        session: HTTPセッション
        base_url: ベースURL
    
    Returns:
        BaseExtractorのインスタンス、またはNone（エラー時）
    """
    try:
        # モジュール名を取得
        module_name = get_extractor_module_name(pattern)
        
        # モジュールを動的にインポート
        module = importlib.import_module(module_name)
        
        # クラス名を取得
        class_name = get_extractor_class_name(pattern)
        
        # クラスを取得
        extractor_class = getattr(module, class_name)
        
        # インスタンスを作成
        extractor = extractor_class(session, base_url)
        
        return extractor
    except Exception as e:
        print(f"[ERROR] Failed to load extractor for pattern {pattern}: {e}")
        return None


def extract_posts_from_page(soup: BeautifulSoup, session: requests.Session, base_url: str) -> list:
    """
    ページから投稿を抽出（パターン自動選択）
    
    Args:
        soup: BeautifulSoupオブジェクト
        session: HTTPセッション
        base_url: ベースURL
    
    Returns:
        投稿のリスト
    """
    # パターンを判定
    pattern = detect_extraction_pattern(soup)
    print(f"[INFO] Detected extraction pattern: {pattern}")
    
    # 抽出器を読み込む
    extractor = load_extractor(pattern, session, base_url)
    
    if not extractor:
        print(f"[ERROR] Failed to load extractor, trying fallback pattern")
        # フォールバックパターンを試行
        extractor = load_extractor("pattern_fallback", session, base_url)
        if not extractor:
            return []
    
    # 投稿を抽出
    try:
        posts = extractor.extract(soup)
    except Exception as e:
        print(f"[ERROR] Extraction failed for pattern {pattern}: {e}")
        # エラーが発生した場合、フォールバックパターンを試行
        if pattern != "pattern_fallback":
            print(f"[INFO] Trying fallback pattern")
            fallback_extractor = load_extractor("pattern_fallback", session, base_url)
            if fallback_extractor:
                posts = fallback_extractor.extract(soup)
            else:
                posts = []
        else:
            posts = []
    
    # 画像が取得できなかった場合、フォールバックパターンを試行
    if posts and all(len(post.get("images", [])) == 0 for post in posts):
        if pattern != "pattern_fallback":
            print(f"[WARN] Pattern {pattern} extracted posts but no images found, trying fallback pattern")
            fallback_extractor = load_extractor("pattern_fallback", session, base_url)
            if fallback_extractor:
                fallback_posts = fallback_extractor.extract(soup)
                if fallback_posts and any(len(post.get("images", [])) > 0 for post in fallback_posts):
                    print(f"[INFO] Fallback pattern found images, using fallback results")
                    return fallback_posts
    
    return posts
