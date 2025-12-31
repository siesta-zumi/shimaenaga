# テスト用スクリプト
import requests
import time
import sys

# Windows環境でのUnicodeエラーを防ぐ
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# サーバーが起動するまで待機
print("サーバー起動を待機中...")
time.sleep(2)

try:
    # ルートパスにアクセス
    response = requests.get('http://localhost:5000/', timeout=5)
    if response.status_code == 200:
        print("[OK] サーバーは正常に起動しています")
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンスサイズ: {len(response.content)} bytes")
    else:
        print(f"[WARN] サーバーは起動していますが、ステータスコード: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("[ERROR] サーバーに接続できません。app.pyが起動しているか確認してください。")
except Exception as e:
    print(f"[ERROR] エラー: {e}")
