# coding: utf-8
"""
パターン判定ロジック
ページ構造から適切な抽出パターンを判定する
"""

import re
from typing import Optional
from bs4 import BeautifulSoup


def detect_extraction_pattern(soup: BeautifulSoup) -> str:
    """
    ページ構造から抽出パターンを判定
    
    Args:
        soup: BeautifulSoupオブジェクト
    
    Returns:
        パターン名（"pattern_standard", "pattern_t_b_only", "pattern_generic_2ch", "pattern_dl_dt_dd", "pattern_fallback"）
    """
    
    # パターン1: .t_h / .t_b 構造（標準パターン）
    main_article = soup.select_one("article.post, article.article, main#main.main article")
    if main_article:
        targets = main_article.select(".entry-content .t_h, .entry-content .t_b, .article-body .t_h, .article-body .t_b, .t_h, .t_b")
        if targets:
            t_h_count = sum(1 for t in targets if "t_h" in t.get("class", []))
            t_b_count = sum(1 for t in targets if "t_b" in t.get("class", []))
            
            if t_h_count > 0 and t_b_count > 0:
                return "pattern_standard"  # .t_h と .t_b の両方が存在
            elif t_b_count > 0:
                return "pattern_t_b_only"  # .t_b のみ存在
    
    # フォールバック: より広いセレクターで .t_h / .t_b を探す
    targets = soup.select(".article-body .t_h, .article-body .t_b, .entry-content .t_h, .entry-content .t_b, .t_h, .t_b")
    if targets:
        t_h_count = sum(1 for t in targets if "t_h" in t.get("class", []))
        t_b_count = sum(1 for t in targets if "t_b" in t.get("class", []))
        
        if t_h_count > 0 and t_b_count > 0:
            return "pattern_standard"
        elif t_b_count > 0:
            return "pattern_t_b_only"
    
    # パターン2: Generic 2ch blog format
    article = soup.select_one("article, .article-body, .entry-content, #article-body")
    if article:
        elements = article.find_all(['div', 'p', 'blockquote'], recursive=False)
        if elements and any(re.match(r'^\d+:', elem.get_text(strip=True)) for elem in elements):
            return "pattern_generic_2ch"
    
    # パターン3: dl/dt/dd structure
    dl_elements = soup.find_all('dl')
    if dl_elements:
        for dl in dl_elements:
            dt_elements = dl.find_all('dt', recursive=False)
            if dt_elements and any(re.match(r'^\d+:', dt.get_text(strip=True)) for dt in dt_elements):
                return "pattern_dl_dt_dd"
    
    # フォールバック
    return "pattern_fallback"


def get_extractor_module_name(pattern: str) -> str:
    """
    パターン名からモジュール名を取得
    
    Args:
        pattern: パターン名（例: "pattern_standard"）
    
    Returns:
        モジュール名（例: "extractors.pattern_standard"）
    """
    return f"extractors.{pattern}"


def get_extractor_class_name(pattern: str) -> str:
    """
    パターン名からクラス名を取得
    
    Args:
        pattern: パターン名（例: "pattern_standard"）
    
    Returns:
        クラス名（例: "StandardExtractor"）
    """
    # pattern_standard -> StandardExtractor
    parts = pattern.split("_")
    class_name = "".join(word.capitalize() for word in parts[1:]) + "Extractor"
    return class_name
