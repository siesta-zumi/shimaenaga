==========================================
画像一括取得ツール - 使い方
==========================================

【必要な環境】
- Python 3.8以上
- インターネット接続

【初回セットアップ】

1. Pythonがインストールされているか確認
   コマンドプロンプトまたはPowerShellで以下を実行:
   
   python --version
   
   バージョンが表示されればOK

2. 必要なライブラリをインストール
   
   pip install requests beautifulsoup4 playwright
   
3. Playwrightのブラウザをインストール
   
   playwright install chromium

【使い方】

1. 「urls.txt」ファイルを開いて、画像を取得したいURLを1行に1つずつ記入
   例:
   https://example.com/article1.html
   https://example.com/article2.html

2. コマンドプロンプトまたはPowerShellで以下を実行:
   
   python 画像一括取得.py
   
3. 処理が完了すると、「画像取得結果」フォルダが作成されます
   - 各URLごとにフォルダが作られます
   - 「画像」フォルダ: ダウンロードした画像
   - posts.txt: 投稿内容とファイル名の対応表

【注意事項】
- 初回実行時は時間がかかる場合があります
- エラーが出た場合は、上記のセットアップ手順を再度確認してください
- 大量のURLを処理する場合は時間がかかります

【トラブルシューティング】
- 「playwright」が見つからない → pip install playwright を実行
- ブラウザエラー → playwright install chromium を実行
- 文字化け → コマンドプロンプトの設定で文字コードをUTF-8に変更

==========================================


