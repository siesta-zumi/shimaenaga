# GitHubリポジトリ管理手順

## 📋 概要

このプロジェクトをGitHubリポジトリで管理する手順です。

**最終更新**: 2025年1月

---

## 🚀 セットアップ手順

### 1. .gitignoreファイルの確認

`.gitignore`ファイルがプロジェクトルートに作成されていることを確認してください。

**除外されるファイル**:
- `__pycache__/` - Pythonキャッシュ
- `build/`, `dist/` - ビルド成果物
- `*.exe` - 実行ファイル
- `result_js/` - 出力フォルダ
- `backup/` - バックアップファイル
- `配布用/` - 配布用ファイル

---

### 2. Gitリポジトリの初期化

```bash
# プロジェクトディレクトリに移動
cd "C:\Users\81806\Desktop\しまえながプロジェクト\画像取得システム"

# Gitリポジトリを初期化
git init

# 現在の状態を確認
git status
```

---

### 3. 初回コミット

```bash
# すべてのファイルをステージング
git add .

# コミット
git commit -m "Initial commit: 画像一括取得システム v2.0.0"
```

---

### 4. GitHubリポジトリの作成

#### 方法1: GitHub Webサイトで作成

1. **GitHubにログイン**
   - https://github.com にアクセス

2. **新しいリポジトリを作成**
   - 右上の「+」→「New repository」をクリック
   - リポジトリ名を入力（例: `image-scraper`）
   - 説明を入力（例: `2chまとめサイトから画像と投稿内容を一括取得するシステム`）
   - **Public** または **Private** を選択
   - 「Initialize this repository with a README」は**チェックしない**（既にファイルがあるため）
   - 「Create repository」をクリック

3. **リモートリポジトリを追加**
   ```bash
   # リモートリポジトリを追加（YOUR_USERNAMEとREPO_NAMEを置き換え）
   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
   
   # 例:
   # git remote add origin https://github.com/username/image-scraper.git
   ```

#### 方法2: GitHub CLIで作成

```bash
# GitHub CLIがインストールされている場合
gh repo create image-scraper --public --source=. --remote=origin --push
```

---

### 5. プッシュ

```bash
# メインブランチをmainにリネーム（必要に応じて）
git branch -M main

# リモートリポジトリにプッシュ
git push -u origin main
```

---

## 📝 コミットメッセージの例

### 機能追加
```bash
git commit -m "feat: Webアプリ化の実装を追加"
```

### バグ修正
```bash
git commit -m "fix: 画像取得時のエラーハンドリングを改善"
```

### ドキュメント
```bash
git commit -m "docs: GitHub管理手順を追加"
```

### リファクタリング
```bash
git commit -m "refactor: コードの整理とコメント追加"
```

---

## 🔄 日常的な作業フロー

### 変更をコミット

```bash
# 変更を確認
git status

# 変更をステージング
git add .

# または特定のファイルのみ
git add 画像一括取得.py
git add docs/

# コミット
git commit -m "コミットメッセージ"

# プッシュ
git push
```

### ブランチの使用（オプション）

```bash
# 新しいブランチを作成
git checkout -b feature/web-app

# 変更をコミット
git add .
git commit -m "feat: Webアプリ機能を追加"

# ブランチをプッシュ
git push -u origin feature/web-app

# メインブランチに戻る
git checkout main

# ブランチをマージ
git merge feature/web-app
```

---

## 📁 リポジトリに含めるべきファイル

### ✅ 含めるべきファイル

- `画像一括取得.py` - メインスクリプト
- `extractors/` - パターンモジュール
- `docs/` - ドキュメント
- `requirements.txt` - 依存関係
- `README.md` - 説明書
- `version.py` - バージョン情報
- `.gitignore` - Git除外設定
- `バージョン履歴.md` - 変更履歴

### ❌ 含めないファイル（.gitignoreで除外）

- `__pycache__/` - Pythonキャッシュ
- `build/`, `dist/` - ビルド成果物
- `*.exe` - 実行ファイル
- `result_js/` - 出力フォルダ
- `backup/` - バックアップ
- `配布用/` - 配布用ファイル

---

## 🔐 プライベートリポジトリ vs パブリックリポジトリ

### プライベートリポジトリ（推奨）

**メリット**:
- ✅ コードが非公開
- ✅ グループメンバーのみアクセス可能
- ✅ 無料で利用可能（個人アカウント）

**デメリット**:
- ❌ 他の人と共有する場合は招待が必要

### パブリックリポジトリ

**メリット**:
- ✅ 誰でもアクセス可能
- ✅ オープンソースとして公開可能

**デメリット**:
- ❌ コードが公開される
- ❌ セキュリティリスク

**推奨**: プライベートリポジトリで開始し、必要に応じて公開

---

## 📋 README.mdの更新

GitHubリポジトリ用にREADME.mdを更新することをお勧めします。

### 追加すべき情報

1. **インストール手順**
2. **使用方法**
3. **ライセンス**
4. **貢献方法**（オプション）

---

## 🔧 トラブルシューティング

### エラー: "remote origin already exists"

```bash
# 既存のリモートを削除
git remote remove origin

# 新しいリモートを追加
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### エラー: "failed to push some refs"

```bash
# リモートの変更を取得
git pull origin main --allow-unrelated-histories

# 再度プッシュ
git push -u origin main
```

### 大きなファイルのエラー

```bash
# .gitignoreに追加されているか確認
# 必要に応じて、Git LFSを使用
git lfs install
git lfs track "*.exe"
```

---

## 📚 参考リンク

- [Git公式ドキュメント](https://git-scm.com/doc)
- [GitHub公式ドキュメント](https://docs.github.com/)
- [GitHub CLI](https://cli.github.com/)

---

## ✅ チェックリスト

- [ ] `.gitignore`ファイルを作成
- [ ] `git init`でリポジトリを初期化
- [ ] 初回コミットを作成
- [ ] GitHubでリポジトリを作成
- [ ] リモートリポジトリを追加
- [ ] プッシュを実行
- [ ] README.mdを更新（オプション）

---

**最終更新**: 2025年1月
