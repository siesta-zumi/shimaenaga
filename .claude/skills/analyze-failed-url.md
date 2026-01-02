---
name: analyze-failed-url
description: 画像取得に失敗したURLのHTML構造を分析し、新しいextractorパターンの作成をサポート
---

# 失敗URLの構造分析Skill

このSkillは、画像一括取得システムで画像取得に失敗したURLを分析し、新しいextractorパターンを作成するための情報を提供します。

## 使用方法

ユーザーが以下のような依頼をした時に、このSkillを使用してください：
- "このURLで画像が取れなかったので分析して"
- "example.comの構造を調べて新しいextractorを作りたい"
- "失敗したURLのHTML構造を見て"

## 実行手順

### 1. URL取得とHTML構造の分析

対象URLにアクセスして、以下の情報を収集：

```python
# WebFetchツールまたはPlaywrightを使用してHTMLを取得
# 以下の要素を重点的に分析：

1. 画像タグ（<img>）の配置場所
   - 親要素のクラス名、ID
   - 兄弟要素の構造
   - ネストの深さ

2. コンテンツ構造
   - 記事/投稿のコンテナ要素
   - リスト構造（ul/ol、dl/dt/dd）
   - 一般的なクラス名パターン

3. 画像の特徴
   - data-src vs src
   - lazy loading の有無
   - レスポンシブ画像（srcset）
```

### 2. 既存extractorパターンとの比較

`extractors/` フォルダ内の既存パターンを確認：
- `pattern_standard.py` - 標準的な構造
- `pattern_t_b_only.py` - .t_bクラス専用
- `pattern_generic_2ch.py` - 2ch系掲示板
- `pattern_dl_dt_dd.py` - 定義リスト構造
- `pattern_fallback.py` - フォールバック

既存パターンで対応できないか検討してから、新規作成を提案する。

### 3. 新しいextractorパターンの提案

分析結果に基づいて以下を提供：

#### A. パターン名の提案
```
pattern_[サイト名または構造の特徴].py
例: pattern_example_com.py, pattern_article_wrapper.py
```

#### B. BaseExtractorを継承したテンプレートコード

```python
# coding: utf-8
"""
[サイト名/構造名] 用の抽出パターン
"""
from bs4 import BeautifulSoup
from typing import List, Dict
from extractors.base import BaseExtractor

class [クラス名]Extractor(BaseExtractor):
    """
    [説明]

    対象サイト: [URL例]
    特徴: [構造の特徴]
    """

    def extract(self, soup: BeautifulSoup) -> List[Dict]:
        """
        投稿と画像を抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            投稿のリスト [{"post_id": str, "images": [urls]}]
        """
        posts = []

        # [ここに抽出ロジックを実装]
        # 例: コンテナ要素を取得
        containers = soup.select('[CSSセレクタ]')

        for idx, container in enumerate(containers):
            post_id = f"post_{idx + 1}"

            # 画像を抽出
            img_tags = container.find_all('img')
            images = []

            for img in img_tags:
                img_url = self._get_image_url(img)
                if img_url and self._is_valid_image(img_url, img):
                    images.append(img_url)

            if images:
                posts.append({
                    "post_id": post_id,
                    "images": images
                })

        return posts
```

#### C. pattern_detector.pyへの追加コード

```python
# extractors/pattern_detector.py の detect_extraction_pattern() 関数に追加

# [新しいパターン] の判定
if soup.select('[特徴的なCSSセレクタ]'):
    return "pattern_[名前]"
```

### 4. 実装手順の説明

新しいextractorを追加する具体的な手順を提示：

1. `extractors/pattern_[名前].py` ファイルを作成
2. 上記テンプレートコードを貼り付け
3. 抽出ロジックを実装（CSSセレクタを調整）
4. `extractors/__init__.py` に追加
5. `extractors/pattern_detector.py` に判定ロジック追加
6. テスト実行

### 5. テストコマンドの提供

```bash
# 単体でテスト
python 画像一括取得.py

# 対象URLを urls.txt に記載してから実行
```

## 出力形式

分析結果は以下の形式で提示：

```markdown
## URL構造分析結果

### 対象URL
[URL]

### HTML構造の特徴
- コンテナ要素: [要素名とクラス/ID]
- 画像配置: [説明]
- 特記事項: [lazy loadingなど]

### 推奨extractorパターン
**パターン名**: pattern_[名前]
**理由**: [なぜこのパターンが適しているか]

### 実装コード
[上記テンプレートに基づいたコード]

### 次のステップ
1. [手順1]
2. [手順2]
...
```

## 注意事項

- 既存パターンで対応可能な場合は、新規作成せずに既存パターンの使用を推奨
- セキュリティ: 悪意のあるサイトの分析は避ける
- プライバシー: 個人情報が含まれるサイトは注意
- 著作権: 画像取得が許可されているか確認

## 関連ファイル

- `画像一括取得.py` - メインスクリプト
- `extractors/base.py` - BaseExtractorクラス
- `extractors/pattern_detector.py` - パターン自動判定
- `extractors/pattern_fallback.py` - フォールバック参考実装
