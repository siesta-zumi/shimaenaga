# requirements.txt の役割と使用方法

**最終更新**: 2025年12月16日

---

## 📋 requirements.txt とは

`requirements.txt` は、Pythonプロジェクトで使用する**外部パッケージ（依存ライブラリ）のリスト**を管理するファイルです。

**単なる管理ファイルではなく、実際に使用されます。**

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

## 🚀 実際の使用方法

### シナリオ1: 初回セットアップ

```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. Playwrightブラウザをインストール
playwright install chromium

# 3. 実行
py 画像一括取得.py
```

**`requirements.txt` がないと**:
- どのパッケージをインストールすべきか分からない
- 手動で1つずつインストールする必要がある
- バージョンの違いで問題が発生する可能性

### シナリオ2: 他の人が使用する場合

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
   pip install -r requirements.txt  ← ここで使用
   ↓
2. PyInstallerでEXE化
   ↓
   pyinstaller 画像一括取得.spec
   ↓
3. EXEファイルが生成される
   ↓
   dist/画像一括取得.exe
   （依存パッケージがすべて含まれる）
```

### 重要なポイント

#### ✅ EXE化前には必要
- **EXE化の前に**依存パッケージをインストールする必要がある
- `requirements.txt` がないと、どのパッケージをインストールすべきか分からない
- インストールされていないパッケージはEXEに含まれない

#### ✅ EXE化後は不要（配布時）
- EXEファイルには依存パッケージがすべて含まれる
- 配布するEXEファイルには `requirements.txt` は不要
- ユーザーはPythonをインストールする必要がない

---

## 🔄 共有時のシナリオ

### シナリオ1: EXEファイルのみを共有（推奨）

**配布するもの**:
```
配布用/
├── 画像一括取得.exe
├── urls.txt（サンプル）
├── README.md（使用方法）
└── README_使い方.txt（簡易マニュアル）
```

**不要なもの**:
- ❌ `requirements.txt`（EXEには含まれているため不要）
- ❌ `画像一括取得.py`（ソースコード）
- ❌ `extractors/` フォルダ（EXEに含まれているため不要）

**ユーザーの作業**:
1. EXEファイルをダブルクリック
2. `urls.txt` にURLを記述
3. 実行

**注意点**:
- Playwrightブラウザは別途インストールが必要な場合がある
- 初回実行時に自動インストールされる可能性がある

### シナリオ2: ソースコードを共有

**配布するもの**:
```
配布用/
├── 画像一括取得.py
├── extractors/（すべてのパターンモジュール）
├── urls.txt（サンプル）
├── requirements.txt（**必須**）← ここで使用
├── README.md（使用方法）
└── README_使い方.txt（簡易マニュアル）
```

**ユーザーの作業**:
```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt  ← requirements.txt を使用

# 2. Playwrightブラウザをインストール
playwright install chromium

# 3. 実行
py 画像一括取得.py
```

---

## 💡 結論

### requirements.txt の役割

1. **開発時**: 依存パッケージを明示し、環境を再現
2. **共有時**: 他の人が同じ環境を構築できる
3. **EXE化時**: EXE化前に依存パッケージをインストールするために必要

### EXEファイルを配布する場合

- **EXE化前**: `requirements.txt` が必要（依存パッケージをインストールするため）
- **EXE化後**: 配布パッケージには不要（EXEに含まれているため）
- **ユーザー**: `requirements.txt` は不要（EXEを実行するだけ）

### ソースコードを共有する場合

- **`requirements.txt` は必須**
- ユーザーが `pip install -r requirements.txt` を実行する必要がある

---

## 🎯 推奨事項

### プロジェクト管理

**常に `requirements.txt` を保持**:
- 開発環境の再現性を保つ
- 他の開発者が参加しやすい
- EXE化時に必要

### 配布パッケージ

**EXEファイルを配布する場合**:
- 配布パッケージには `requirements.txt` を含めなくてOK
- ただし、ソースコードも含める場合は必須

**ソースコードを配布する場合**:
- `requirements.txt` は必須
- ユーザーが環境を構築するために必要

---

## 📝 まとめ

**`requirements.txt` は管理するだけではなく、実際に使用されます。**

- **開発時**: `pip install -r requirements.txt` で使用
- **EXE化時**: EXE化前に依存パッケージをインストールするために使用
- **共有時**: 他の人が環境を構築するために使用

**EXEファイルを配布する場合**:
- EXEファイルには依存パッケージが含まれるため、配布パッケージには不要
- ただし、プロジェクトには常に保持することを推奨

---

**最終更新**: 2025年12月16日
