# coding: utf-8
"""
画像一括取得システム - Webアプリ版
Flask APIサーバー
"""
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import zipfile
import os
import shutil
import time
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

# 既存の関数をインポート（同じディレクトリにあることを前提）
from 画像一括取得 import scrape_single_url_js

app = Flask(__name__)
CORS(app, expose_headers=['X-Success-URLs', 'X-Failed-URLs'])

# 一時ファイルのクリーンアップ用
temp_files_to_cleanup = []

def cleanup_temp_files():
    """古い一時ファイルを削除（5分経過後）"""
    while True:
        time.sleep(60)  # 1分ごとにチェック
        now = time.time()
        for temp_dir, created_at in list(temp_files_to_cleanup):
            if now - created_at > 300:  # 5分経過したら削除
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    temp_files_to_cleanup.remove((temp_dir, created_at))
                except:
                    pass

# バックグラウンドでクリーンアップスレッドを起動
cleanup_thread = threading.Thread(target=cleanup_temp_files, daemon=True)
cleanup_thread.start()

@app.route('/api/scrape', methods=['POST'])
def scrape():
    """
    URLリストを受け取り、画像取得処理を実行してZIPファイルを返す
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLが指定されていません'}), 400
        
        # URLの検証
        validated_urls = []
        for url in urls:
            url = url.strip()
            if url and not url.startswith('#'):
                if url.startswith('http://') or url.startswith('https://'):
                    validated_urls.append(url)
                else:
                    # http://を自動追加（オプション）
                    validated_urls.append('https://' + url)
        
        if not validated_urls:
            return jsonify({'error': '有効なURLがありません'}), 400
        
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        result_root = os.path.join(temp_dir, 'result_js')
        os.makedirs(result_root, exist_ok=True)
        
        # 成功/失敗を記録
        success_urls = []
        failed_urls = []

        try:
            # Playwrightで画像取得処理を実行
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                for url in validated_urls:
                    try:
                        scrape_single_url_js(url, result_root, browser)
                        success_urls.append(url)
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                        failed_urls.append({'url': url, 'error': str(e)})
                        continue
                browser.close()

            # 結果サマリーファイルを作成
            summary_path = os.path.join(result_root, '_result_summary.txt')
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("画像一括取得システム - 処理結果\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"総URL数: {len(validated_urls)}\n")
                f.write(f"成功: {len(success_urls)}件\n")
                f.write(f"失敗: {len(failed_urls)}件\n\n")

                if success_urls:
                    f.write("-" * 60 + "\n")
                    f.write("✅ 成功したURL:\n")
                    f.write("-" * 60 + "\n")
                    for url in success_urls:
                        f.write(f"  • {url}\n")
                    f.write("\n")

                if failed_urls:
                    f.write("-" * 60 + "\n")
                    f.write("❌ 失敗したURL:\n")
                    f.write("-" * 60 + "\n")
                    for item in failed_urls:
                        f.write(f"  • {item['url']}\n")
                        f.write(f"    エラー: {item['error']}\n\n")
                    f.write("-" * 60 + "\n")
                    f.write("💡 ヒント:\n")
                    f.write("失敗したURLは新しいextractorパターンが必要かもしれません。\n")
                    f.write("Claude Codeで '/analyze-failed-url' Skillを使用して\n")
                    f.write("URL構造を分析できます。\n")

            # 結果をZIP化
            zip_path = os.path.join(temp_dir, 'result.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(result_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 相対パスでZIPに追加
                        arcname = os.path.relpath(file_path, result_root)
                        zipf.write(file_path, arcname)
            
            # クリーンアップリストに追加（5分後に削除）
            temp_files_to_cleanup.append((temp_dir, time.time()))

            # ZIPファイルを返す（成功/失敗情報をヘッダーに含める）
            import json
            response = send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name='result.zip'
            )
            # 成功したURLリストをヘッダーに追加
            response.headers['X-Success-URLs'] = json.dumps(success_urls)
            # 失敗したURLリストをヘッダーに追加（URLのみ）
            response.headers['X-Failed-URLs'] = json.dumps([item['url'] for item in failed_urls])
            return response
            
        except Exception as e:
            # エラー時は即座に削除
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """HTMLページを返す"""
    import os
    file_path = os.path.abspath('index.html')
    file_size = os.path.getsize(file_path)
    print(f"[INFO] Serving index.html from: {file_path}")
    print(f"[INFO] File size: {file_size} bytes")
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
