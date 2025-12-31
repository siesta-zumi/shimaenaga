# ファイル配置とURL入力方法

## 📁 ファイル配置

### 推奨ディレクトリ構成

```
web-app/
├── app.py                    # Flask API（メイン）
├── index.html                # HTMLページ
├── 画像一括取得.py            # 既存のPythonファイル（そのまま配置）
├── extractors/               # 既存のextractorsフォルダ（そのまま配置）
│   ├── __init__.py
│   ├── base.py
│   ├── pattern_detector.py
│   ├── pattern_loader.py
│   ├── pattern_standard.py
│   ├── pattern_t_b_only.py
│   ├── pattern_generic_2ch.py
│   ├── pattern_dl_dt_dd.py
│   └── pattern_fallback.py
├── requirements.txt          # 依存関係
└── README.md                 # 説明書
```

### 重要なポイント

1. **`画像一括取得.py`と`extractors/`は同じディレクトリに配置**
   - 既存の相対インポート（`from extractors.pattern_loader import ...`）がそのまま動作します

2. **`urls.txt`は不要**
   - フォームから直接URLリストを受け取るため、ファイルは不要です

3. **`result_js/`フォルダも不要**
   - 一時ディレクトリを使用し、処理完了後に削除します

---

## 💻 実装例

### 1. app.py（Flask API）

```python
# app.py
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
CORS(app)

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
        
        # URLの検証（オプション）
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
        
        try:
            # Playwrightで画像取得処理を実行
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                for url in validated_urls:
                    try:
                        scrape_single_url_js(url, result_root, browser)
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                        continue
                browser.close()
            
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
            
            # ZIPファイルを返す
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name='result.zip'
            )
            
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
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

### 2. index.html（URL入力フォーム + ドラッグ&ドロップ対応）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>画像一括取得システム</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .input-section {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        textarea {
            width: 100%;
            height: 200px;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
        }
        textarea:focus {
            outline: none;
            border-color: #007bff;
        }
        .drop-zone {
            border: 2px dashed #ccc;
            border-radius: 4px;
            padding: 40px;
            text-align: center;
            background-color: #fafafa;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .drop-zone:hover {
            border-color: #007bff;
            background-color: #f0f7ff;
        }
        .drop-zone.dragover {
            border-color: #007bff;
            background-color: #e7f3ff;
        }
        .drop-zone-text {
            color: #666;
            font-size: 14px;
        }
        .drop-zone-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 15px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .loading {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background-color: #e7f3ff;
            border-radius: 4px;
            color: #0056b3;
        }
        .error {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background-color: #fee;
            color: #c33;
            border-radius: 4px;
        }
        .success {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background-color: #efe;
            color: #3c3;
            border-radius: 4px;
        }
        .url-count {
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>画像一括取得システム</h1>
        
        <form id="scrapeForm">
            <div class="input-section">
                <label for="urls">URLリスト（1行1URL）:</label>
                
                <!-- ドラッグ&ドロップゾーン -->
                <div class="drop-zone" id="dropZone">
                    <div class="drop-zone-icon">📄</div>
                    <div class="drop-zone-text">
                        テキストファイルをドラッグ&ドロップ<br>
                        またはクリックしてファイルを選択
                    </div>
                    <input type="file" id="fileInput" accept=".txt" style="display: none;">
                </div>
                
                <!-- テキストエリア -->
                <textarea 
                    id="urls" 
                    placeholder="https://example.com/page1&#10;https://example.com/page2&#10;&#10;または、上記のドラッグ&ドロップゾーンにテキストファイルをドロップしてください"
                    required
                ></textarea>
                
                <div class="url-count" id="urlCount">0 URL</div>
            </div>
            
            <button type="submit" id="submitBtn">取得開始</button>
        </form>
        
        <div class="loading" id="loading">
            <p>⏳ 処理中... しばらくお待ちください（数分かかる場合があります）</p>
        </div>
        
        <div class="error" id="error"></div>
        <div class="success" id="success"></div>
    </div>

    <script>
        const form = document.getElementById('scrapeForm');
        const urlsTextarea = document.getElementById('urls');
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');
        const errorDiv = document.getElementById('error');
        const successDiv = document.getElementById('success');
        const urlCount = document.getElementById('urlCount');

        // URL数をカウントして表示
        function updateUrlCount() {
            const urls = urlsTextarea.value
                .split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
            urlCount.textContent = `${urls.length} URL`;
        }

        urlsTextarea.addEventListener('input', updateUrlCount);

        // ドラッグ&ドロップの処理
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const file = e.dataTransfer.files[0];
            if (file && file.type === 'text/plain') {
                const reader = new FileReader();
                reader.onload = (e) => {
                    urlsTextarea.value = e.target.result;
                    updateUrlCount();
                };
                reader.readAsText(file);
            } else {
                showError('テキストファイル（.txt）のみ対応しています');
            }
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    urlsTextarea.value = e.target.result;
                    updateUrlCount();
                };
                reader.readAsText(file);
            }
        });

        // フォーム送信
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const urls = urlsTextarea.value
                .split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
            
            if (urls.length === 0) {
                showError('URLを入力してください');
                return;
            }
            
            // UI更新
            submitBtn.disabled = true;
            loading.style.display = 'block';
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ urls: urls })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'エラーが発生しました');
                }
                
                // ZIPファイルをダウンロード
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `result_${Date.now()}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                // 成功メッセージ
                showSuccess('ダウンロードが完了しました！');
                
            } catch (error) {
                showError('エラー: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
        
        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        function showSuccess(message) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
        }
    </script>
</body>
</html>
```

---

## 📋 セットアップ手順

### 1. ディレクトリ作成

```bash
mkdir web-app
cd web-app
```

### 2. ファイルをコピー

```bash
# 既存のファイルをコピー
cp ../画像一括取得.py .
cp -r ../extractors .
```

### 3. 新規ファイル作成

```bash
# app.py と index.html を作成（上記のコードをコピー）
```

### 4. requirements.txt に追加

```txt
playwright
beautifulsoup4
requests
lxml
flask
flask-cors
```

### 5. インストール

```bash
pip install -r requirements.txt
playwright install chromium
```

### 6. 実行

```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセス

---

## ✅ 動作確認

1. **テキストエリアに直接入力**
   - URLを1行ずつ入力
   - URL数が自動表示される

2. **ドラッグ&ドロップ**
   - `urls.txt`ファイルをドラッグ&ドロップ
   - 内容が自動的にテキストエリアに読み込まれる

3. **ファイル選択**
   - ドロップゾーンをクリックしてファイルを選択

4. **実行**
   - 「取得開始」ボタンをクリック
   - 処理完了後、ZIPファイルが自動ダウンロード

---

## 🎯 まとめ

### ファイル配置

- **`画像一括取得.py`**: `app.py`と同じディレクトリ
- **`extractors/`**: `app.py`と同じディレクトリ
- **`urls.txt`**: 不要（フォームから直接入力）

### URL入力方法

1. ✅ **テキストエリアに直接入力**（1行1URL）
2. ✅ **ドラッグ&ドロップ**（テキストファイル）
3. ✅ **ファイル選択**（クリックして選択）

すべての方法に対応しています！

---

**最終更新**: 2025年1月
