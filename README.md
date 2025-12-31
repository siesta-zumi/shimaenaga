# 画像一括取得システム

2ch(5ch)まとめサイト・ブログから画像と投稿内容を一括取得するシステム

---

## 📋 概要

このシステムは、2ch(5ch)まとめサイトやブログから、スレッド内の画像と投稿内容を自動的に取得し、整理された形式で保存します。

### 主な機能

- ✅ **複数サイト対応**: パターン自動選択システムで様々なサイト構造に対応
- ✅ **画像自動取得**: スレッド内の画像を自動的にダウンロード
- ✅ **投稿内容抽出**: レスヘッダー、本文、画像の対応関係を維持
- ✅ **スレ主ID判定**: 1番レスIDと色付きIDからスレ主を自動判定
- ✅ **広告除外**: 広告画像を自動的に除外
- ✅ **Lazy Load対応**: スクロールして画像を読み込む
- ✅ **Imgur対応**: Imgur URLを自動変換

---

## 📁 ディレクトリ構造

```
画像取得システム/
├── 画像一括取得.py          # メインスクリプト（トリガー）
├── urls.txt                 # URLリスト（1行1URL）
├── requirements.txt         # 依存パッケージ
├── README.md               # このファイル
│
├── extractors/             # パターンモジュール（自動選択）
│   ├── __init__.py
│   ├── base.py             # 基底クラスと共通ユーティリティ
│   ├── pattern_detector.py # パターン判定ロジック
│   ├── pattern_loader.py   # 動的モジュール読み込み
│   ├── pattern_standard.py # パターン1: .t_h / .t_b 構造
│   ├── pattern_t_b_only.py # パターン2: .t_b のみ
│   ├── pattern_generic_2ch.py # パターン3: Generic 2ch blog format
│   ├── pattern_dl_dt_dd.py # パターン4: dl/dt/dd structure
│   └── pattern_fallback.py # パターン5: フォールバック
│
├── result_js/              # 出力フォルダ
│   └── [ページタイトル]/
│       ├── posts.txt       # 投稿内容
│       └── images/         # 画像ファイル
│           ├── 画像1.jpg
│           ├── 画像2.jpg
│           └── ...
│
├── docs/                   # ドキュメント
│   ├── 要件定義.md         # 詳細要件定義
│   ├── 画像取得システム.md  # 現行仕様
│   └── 開発ナレッジ.md     # 開発・検証過程の知見
│
├── backup/                 # バックアップファイル
└── build/, dist/           # ビルド関連（EXE化時）
```

---

## 🚀 使用方法

### 1. 環境準備

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# Playwrightブラウザのインストール
playwright install chromium
```

### 2. URLリストの準備

`urls.txt` に取得したいURLを1行1URLで記述：

```
https://tabinolog.com/archives/16141932.html
https://tabinolog.com/archives/16142958.html
https://tabinolog.com/archives/21661990.html
```

### 3. 実行

```bash
# Pythonで実行
py 画像一括取得.py

# または EXEで実行
画像一括取得.exe
```

### 4. 結果確認

`result_js/` フォルダに結果が保存されます：

```
result_js/
└── [ページタイトル]/
    ├── posts.txt       # 投稿内容
    └── images/         # 画像ファイル
        ├── 画像1.jpg
        ├── 画像2.jpg
        └── ...
```

---

## 🔄 処理フロー

```
1. URL読み込み (urls.txt)
   ↓
2. 各URLに対して処理
   ↓
3. ページ読み込み（Playwright）
   ├─ JavaScript実行
   ├─ 自動スクロール（Lazy Load対応）
   └─ DOM取得
   ↓
4. HTML解析（BeautifulSoup）
   ↓
5. パターン判定 (pattern_detector.py)
   ├─ ページ構造を解析
   └─ 適切なパターンを判定
   ↓
6. パターンローダー (pattern_loader.py)
   ├─ パターン名からモジュール名を取得
   ├─ 動的にモジュールをインポート
   ├─ 抽出器クラスのインスタンスを作成
   └─ 抽出を実行
   ↓
7. データ整形
   ├─ posts.txt生成
   └─ 画像ダウンロード
   ↓
8. ファイル保存
   └─ result_js/[タイトル]/ に出力
```

---

## 🎯 パターン選択システム

このシステムは、ページ構造を自動判定して適切な抽出パターンを選択します。

### 対応パターン

1. **pattern_standard**: .t_h / .t_b 構造（標準パターン）
   - 対象: 旅のろぐなど、標準的な構造

2. **pattern_t_b_only**: .t_b のみ
   - 対象: tabinolog.comなど、.t_h要素が存在しないサイト

3. **pattern_generic_2ch**: Generic 2ch blog format
   - 対象: oryouri.2chblog.jpなど、汎用的な2chまとめブログ形式

4. **pattern_dl_dt_dd**: dl/dt/dd structure
   - 対象: 古いoryouri.2chblog.jp形式など

5. **pattern_fallback**: フォールバック
   - 対象: どのパターンにも該当しないサイト

### パターン判定の優先順位

1. pattern_standard
2. pattern_t_b_only
3. pattern_generic_2ch
4. pattern_dl_dt_dd
5. pattern_fallback

---

## 📝 出力形式

### posts.txt のフォーマット

```
ページタイトル
ID:スレ主ID1
ID:スレ主ID2
（空行）
レス番号: 名前 日時 ID:投稿者ID
画像1.jpg
コメント本文
（空行）
レス番号: 名前 日時 ID:投稿者ID
画像2.jpg
コメント本文
（空行）
```

### 画像ファイル

- ファイル名: `画像1.jpg`, `画像2.jpg`, ...（連番）
- 保存先: `result_js/[ページタイトル]/images/`

---

## 🔧 新しいパターンの追加

新しいサイト構造に対応する場合、以下の手順で新しいパターンを追加できます：

1. **新しいパターンファイルを作成**
   ```
   extractors/pattern_new.py
   ```

2. **BaseExtractorを継承したクラスを実装**
   ```python
   from extractors.base import BaseExtractor
   
   class NewExtractor(BaseExtractor):
       def extract(self, soup: BeautifulSoup) -> List[Dict]:
           # 抽出ロジックを実装
           pass
   ```

3. **パターン判定ロジックを追加**
   ```python
   # extractors/pattern_detector.py
   def detect_extraction_pattern(soup: BeautifulSoup) -> str:
       # 新しいパターンの判定条件を追加
       if has_new_pattern(soup):
           return "pattern_new"
       ...
   ```

詳細は `docs/開発ナレッジ.md` を参照してください。

---

## 📚 ドキュメント

- **`docs/要件定義.md`**: 詳細要件定義（最新仕様）
- **`docs/画像取得システム.md`**: 現行仕様（As-Is）
- **`docs/開発ナレッジ.md`**: 開発・検証過程の知見

---

## ⚙️ システム要件

- **Python**: 3.8以上推奨
- **依存パッケージ**: `requirements.txt` を参照
- **OS**: Windows 10/11（主に開発・テスト環境）

---

## 🐛 トラブルシューティング

### 画像が0枚になる場合

1. パターンが正しく判定されているか確認（ログで `[INFO] Detected extraction pattern:` を確認）
2. `.t_h` / `.t_b`要素が存在するか確認
3. 広告判定で除外されていないか確認
4. URL解決が正しく行われているか確認

### パターンが正しく判定されない場合

1. `extractors/pattern_detector.py` の判定条件を確認
2. ページ構造が想定と異なる可能性
3. 新しいパターンの判定条件を追加する必要がある可能性

### インポートエラー

1. `extractors/` フォルダが存在するか確認
2. `extractors/__init__.py` が存在するか確認
3. 各パターンモジュールが存在するか確認

---

## 📊 対応サイト例

- 旅のろぐ（tabinolog.com）
- お料理速報（oryouri.2chblog.jp）
- 明日は何を食べようか
- その他2ch(5ch)まとめブログ

---

## 🔄 更新履歴

### v2.0（2025年12月）
- パターン選択システムを実装
- `extractors/` フォルダでパターンモジュールを管理
- 動的モジュール読み込みを実装
- 出力フォルダを統一（`result_js/`）

### v1.0
- 初回リリース

---

## 📝 ライセンス

このプロジェクトは個人利用を想定しています。

---

## 💡 注意事項

- 取得した画像・テキストの利用は、各サイトの利用規約に従ってください
- 過度なアクセスは避け、適切な間隔を空けて実行してください
- 取得したデータの取り扱いには注意してください

---

**最終更新**: 2025年12月31日
