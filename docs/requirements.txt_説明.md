# requirements.txt の役割と使用方法

**最終更新**: 2025年12月16日

---

## 📋 requirements.txt とは

`requirements.txt` は、Pythonプロジェクトで使用する**外部パッケージ（依存ライブラリ）のリスト**を管理するファイルです。

---

## 🎯 主な役割

### 1. 依存パッケージの明示
プロジェクトで使用している外部パッケージを明示します。

### 2. 環境の再現性
他の環境でも同じパッケージをインストールして、同じ動作を保証します。

### 3. バージョン管理
パッケージのバージョンを固定して、環境の違いによる問題を防ぎます。

---

## 📦 現在の requirements.txt の内容

```
playwright
beautifulsoup4
requests
lxml
```

### 各パッケージの用途

| パッケージ | 用途 | 使用箇所 |
|-----------|------|---------|
| **playwright** | ブラウザ自動化 | ページ読み込み、スクロール、JavaScript実行 |
| **beautifulsoup4** | HTML解析 | HTMLから投稿・画像を抽出 |
| **requests** | HTTP通信 | 画像ダウンロード |
| **lxml** | HTMLパーサー | BeautifulSoupの高速パーサー |

---

## 🚀 使用方法

### 通常のPython実行時

#### 1. 初回セットアップ
```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# Playwrightブラウザをインストール
playwright install chromium
```

#### 2. 他の環境でのセットアップ
他の人がこのプロジェクトを使う場合：
```bash
# 1. プロジェクトをダウンロード
# 2. requirements.txt から依存パッケージをインストール
pip install -r requirements.txt

# 3. Playwrightブラウザをインストール
playwright install chromium

# 4. 実行
py 画像一括取得.py
```

---

## 📦 EXE化時の扱い

### EXE化の流れ

```
1. 開発環境で依存パッケージをインストール
   ↓
   pip install -r requirements.txt
   ↓
2. PyInstallerでEXE化
   ↓
   pyinstaller 画像一括取得.spec
   ↓
3. EXEファイルが生成される
   ↓
   dist/画像一括取得.exe
```

### EXE化時の注意点

#### ✅ requirements.txt は必要
- **EXE化の前に**依存パッケージをインストールする必要がある
- `requirements.txt` がないと、どのパッケージをインストールすべきか分からない

#### ✅ EXE化後は不要
- EXEファイルには依存パッケージが含まれる
- 配布するEXEファイルには `requirements.txt` は不要
- ただし、**ソースコードを共有する場合は必要**

---

## 🔄 共有時のシナリオ

### シナリオ1: EXEファイルのみを共有

**配布するもの**:
- `画像一括取得.exe`
- `urls.txt`（サンプル）
- `README.md`（使用方法）

**不要なもの**:
- `requirements.txt`（EXEには含まれているため）
- `画像一括取得.py`（ソースコード）
- `extractors/` フォルダ（EXEに含まれているため）

**注意点**:
- ユーザーはPythonをインストールする必要がない
- ただし、Playwrightブラウザは別途インストールが必要な場合がある

### シナリオ2: ソースコードを共有

**配布するもの**:
- `画像一括取得.py`
- `extractors/` フォルダ
- `urls.txt`（サンプル）
- `requirements.txt`（**必須**）
- `README.md`（使用方法）

**使用方法**:
```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. Playwrightブラウザをインストール
playwright install chromium

# 3. 実行
py 画像一括取得.py
```

---

## 💡 推奨事項

### EXEファイルを配布する場合

#### 配布パッケージに含めるもの
```
配布用/
├── 画像一括取得.exe
├── urls.txt（サンプル）
├── README.md（使用方法）
└── README_使い方.txt（簡易マニュアル）
```

#### 配布パッケージに含めないもの
- `requirements.txt`（EXEには含まれているため不要）
- `画像一括取得.py`（ソースコード）
- `extractors/` フォルダ（EXEに含まれているため不要）

### ソースコードを共有する場合

#### 配布パッケージに含めるもの
```
配布用/
├── 画像一括取得.py
├── extractors/（すべてのパターンモジュール）
├── urls.txt（サンプル）
├── requirements.txt（**必須**）
├── README.md（使用方法）
└── README_使い方.txt（簡易マニュアル）
```

---

## 🔧 PyInstallerの設定確認

`画像一括取得.spec` で依存パッケージが正しく含まれているか確認：

```python
# 例: 画像一括取得.spec
a = Analysis(
    ['画像一括取得.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'extractors.pattern_loader',
        'extractors.pattern_detector',
        'extractors.pattern_standard',
        'extractors.pattern_t_b_only',
        'extractors.pattern_generic_2ch',
        'extractors.pattern_dl_dt_dd',
        'extractors.pattern_fallback',
        'extractors.base',
    ],
    ...
)
```

---

## 📝 まとめ

### requirements.txt の役割

1. **開発時**: 依存パッケージを明示し、環境を再現
2. **共有時**: 他の人が同じ環境を構築できる
3. **EXE化時**: EXE化前に依存パッケージをインストールするために必要

### EXEファイルを配布する場合

- **EXEファイルには依存パッケージが含まれる**
- **requirements.txt は配布パッケージに含めなくてOK**
- ただし、**ソースコードを共有する場合は必須**

### ソースコードを共有する場合

- **requirements.txt は必須**
- ユーザーが `pip install -r requirements.txt` を実行する必要がある

---

## 🎯 結論

**`requirements.txt` は必要です。**

- **EXE化前**: 依存パッケージをインストールするために必要
- **ソースコード共有時**: 他の人が環境を構築するために必須
- **EXEファイル配布時**: EXEには含まれているため、配布パッケージには不要

**推奨**: プロジェクトには常に `requirements.txt` を保持し、EXEファイルを配布する際は別途配布パッケージを作成する

---

**最終更新**: 2025年12月16日
