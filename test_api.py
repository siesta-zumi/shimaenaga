# APIテスト用スクリプト
import requests
import sys

# Windows環境でのUnicodeエラーを防ぐ
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("APIエンドポイントのテスト...")
print()

# 1. ルートパス（HTMLページ）の確認
print("1. ルートパス (/) の確認:")
try:
    response = requests.get('http://localhost:5000/', timeout=5)
    if response.status_code == 200:
        print("   [OK] HTMLページが正常に返されました")
        print(f"   コンテンツタイプ: {response.headers.get('Content-Type', 'N/A')}")
    else:
        print(f"   [WARN] ステータスコード: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

print()

# 2. APIエンドポイントの確認（エラーレスポンスの確認）
print("2. APIエンドポイント (/api/scrape) の確認:")
try:
    # URLなしでリクエスト（エラーが返されることを確認）
    response = requests.post('http://localhost:5000/api/scrape', 
                            json={'urls': []}, 
                            timeout=5)
    if response.status_code == 400:
        print("   [OK] APIエンドポイントが正常に動作しています（エラーハンドリング確認）")
        error_data = response.json()
        print(f"   エラーメッセージ: {error_data.get('error', 'N/A')}")
    else:
        print(f"   [WARN] 予期しないステータスコード: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

print()
print("動作確認完了！")
print()
print("次のステップ:")
print("1. ブラウザで http://localhost:5000 にアクセス")
print("2. URLを入力して「取得開始」ボタンをクリック")
print("3. 処理が完了するとZIPファイルがダウンロードされます")
