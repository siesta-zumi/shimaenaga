# coding: utf-8
"""
バージョン情報
"""

# バージョン番号（セマンティックバージョニング）
VERSION = "2.0.0"

# バージョン情報の詳細
VERSION_INFO = {
    "version": VERSION,
    "major": 2,
    "minor": 0,
    "patch": 0,
    "release_date": "2025-12-31",
    "description": "パターン選択システム実装版"
}

def get_version():
    """バージョン番号を取得"""
    return VERSION

def get_version_info():
    """バージョン情報を取得"""
    return VERSION_INFO
