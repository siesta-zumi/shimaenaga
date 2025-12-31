# EXE化手順

**最終更新**: 2025年12月31日

---

## 📋 前提条件

- Python 3.8以上がインストールされていること
- 依存パッケージがインストールされていること

---

## 🚀 EXE化の手順

### ステップ1: 依存パッケージのインストール

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# PyInstallerをインストール（未インストールの場合）
pip install pyinstaller

# Playwrightブラウザをインストール
playwright install chromium
```

### ステップ2: EXE化の実行

```bash
# specファイルを使用してEXE化
pyinstaller 画像一括取得.spec
```

### ステップ3: EXEファイルの確認

EXEファイルは `dist/` フォルダに生成されます：

```
dist/
└── 画像一括取得_v2_0_0.exe
```

**ファイル名**: `画像一括取得_v2_0_0.exe`（バージョン番号を含む）

---

## 📦 バージョン管理

### バージョン番号の変更

バージョンを変更する場合は、`version.py` を編集：

```python
# version.py
VERSION = "2.0.1"  # バージョン番号を変更
```

### バージョン番号の形式

**セマンティックバージョニング**を使用：
- `MAJOR.MINOR.PATCH`
- 例: `2.0.0`, `2.0.1`, `2.1.0`, `3.0.0`

**変更の目安**:
- **MAJOR**: 大きな変更（破壊的変更、アーキテクチャ変更）
- **MINOR**: 機能追加（後方互換性あり）
- **PATCH**: バグ修正、小さな改善

### EXEファイル名の自動更新

`画像一括取得.spec` でバージョン番号が自動的に反映されます：

```python
name=f'画像一括取得_v{VERSION_STR}',  # 例: 画像一括取得_v2_0_0.exe
```

---

## 📁 配布パッケージの作成

### EXEファイルのみを配布する場合

```
配布用/
├── 画像一括取得_v2_0_0.exe
├── urls.txt（サンプル）
├── README.md（使用方法）
└── README_使い方.txt（簡易マニュアル）
```

### PythonとEXE両方を配布する場合

```
配布用/
├── Python版/
│   ├── 画像一括取得.py
│   ├── extractors/（すべてのパターンモジュール）
│   ├── urls.txt（サンプル）
│   ├── requirements.txt
│   └── README.md
│
├── EXE版/
│   ├── 画像一括取得_v2_0_0.exe
│   ├── urls.txt（サンプル）
│   └── README.md
│
└── 共通/
    ├── README_使い方.txt
    └── バージョン履歴.md
```

---

## 🔧 トラブルシューティング

### エラー: ModuleNotFoundError: No module named 'extractors'

**原因**: `hiddenimports` に extractors モジュールが含まれていない

**解決策**: `画像一括取得.spec` の `hiddenimports` を確認

### エラー: ImportError: cannot import name 'extract_posts_from_page'

**原因**: extractors モジュールが正しく含まれていない

**解決策**: `画像一括取得.spec` の `hiddenimports` にすべての extractors モジュールを追加

### EXEファイルが大きすぎる

**原因**: すべての依存パッケージが含まれている

**解決策**: これは正常です。スタンドアロン実行のために必要です。

---

## 📝 バージョン履歴の管理

### バージョン履歴ファイルの作成

`バージョン履歴.md` を作成して、バージョンごとの変更内容を記録：

```markdown
# バージョン履歴

## v2.0.0 (2025-12-31)
- パターン選択システムを実装
- extractors/ フォルダでパターンモジュールを管理
- 動的モジュール読み込みを実装
- 出力フォルダを統一（result_js/）

## v1.0.0
- 初回リリース
```

---

## 🎯 まとめ

### EXE化の流れ

1. **依存パッケージのインストール**: `pip install -r requirements.txt`
2. **EXE化の実行**: `pyinstaller 画像一括取得.spec`
3. **EXEファイルの確認**: `dist/画像一括取得_v2_0_0.exe`

### バージョン管理

- **バージョン番号**: `version.py` で管理
- **EXEファイル名**: 自動的にバージョン番号が含まれる
- **バージョン履歴**: `バージョン履歴.md` で管理

---

**最終更新**: 2025年12月31日
