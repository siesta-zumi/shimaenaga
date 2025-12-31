# URL入力パターン - 1つ vs 複数

## 📋 概要

現在の実装は**複数のURLに対応**していますが、**1つのURLだけ**の運用にも対応可能です。

**最終更新**: 2025年1月

---

## ✅ 対応パターン

### パターン1: 複数URL（現在の実装）

```
URL1
URL2
URL3
```

**動作**:
- すべてのURLを順次処理
- 結果を1つのZIPファイルにまとめる

**メリット**:
- 複数のページを一度に取得可能
- 効率的

**デメリット**:
- 処理時間が長くなる（URL数 × 2-5分）

---

### パターン2: 1つのURLのみ

```
URL1
```

**動作**:
- 1つのURLのみ処理
- 結果をZIPファイルでダウンロード

**メリット**:
- シンプル
- 処理時間が短い（2-5分）

**デメリット**:
- 複数ページを取得する場合は複数回実行が必要

---

## 💻 実装例（両方に対応）

### 現在の実装（複数URL対応）

既に実装済みのコードは、**1つのURLでも複数のURLでも**動作します：

```python
# app.py
@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    urls = data.get('urls', [])  # リスト形式
    
    # 1つのURLでも複数のURLでも動作
    for url in urls:  # urlsが1つでもループは動作
        scrape_single_url_js(url, result_root, browser)
```

**動作例**:
- `urls = ['https://example.com/page1']` → 1つのURLを処理 ✅
- `urls = ['url1', 'url2', 'url3']` → 3つのURLを処理 ✅

---

## 🎨 UIの改善案（1つのURLに特化）

もし**1つのURLだけ**の運用にする場合、UIをシンプルにできます：

### シンプル版（1つのURLのみ）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>画像一括取得システム</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        input[type="url"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            margin-bottom: 15px;
        }
        input[type="url"]:focus {
            outline: none;
            border-color: #007bff;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
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
            text-align: center;
            color: #666;
        }
        .error {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background-color: #fee;
            color: #c33;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>画像一括取得システム</h1>
        <form id="scrapeForm">
            <input 
                type="url" 
                id="url" 
                placeholder="https://example.com/page1"
                required
            >
            <button type="submit" id="submitBtn">取得開始</button>
        </form>
        
        <div class="loading" id="loading">
            <p>⏳ 処理中... しばらくお待ちください（2-5分かかります）</p>
        </div>
        
        <div class="error" id="error"></div>
    </div>

    <script>
        document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('url').value.trim();
            
            if (!url) {
                showError('URLを入力してください');
                return;
            }
            
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            
            submitBtn.disabled = true;
            loading.style.display = 'block';
            errorDiv.style.display = 'none';
            
            try {
                // 1つのURLを配列として送信
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ urls: [url] })  // 配列として送信
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'エラーが発生しました');
                }
                
                // ZIPファイルをダウンロード
                const blob = await response.blob();
                const url_obj = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url_obj;
                a.download = `result_${Date.now()}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url_obj);
                
                alert('ダウンロードが完了しました！');
                
            } catch (error) {
                showError('エラー: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    </script>
</body>
</html>
```

---

## 🔄 両方に対応するUI（推奨）

1つのURLでも複数のURLでも使える、柔軟なUI：

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>画像一括取得システム</title>
    <style>
        /* スタイルは前回と同じ */
    </style>
</head>
<body>
    <div class="container">
        <h1>画像一括取得システム</h1>
        
        <form id="scrapeForm">
            <div class="input-section">
                <label for="urls">URL（1つまたは複数）:</label>
                <textarea 
                    id="urls" 
                    placeholder="1つのURL:&#10;https://example.com/page1&#10;&#10;複数のURL:&#10;https://example.com/page1&#10;https://example.com/page2"
                    required
                ></textarea>
                <div class="url-count" id="urlCount">0 URL</div>
            </div>
            
            <button type="submit" id="submitBtn">取得開始</button>
        </form>
        
        <!-- その他の要素 -->
    </div>

    <script>
        // URL数をカウント
        function updateUrlCount() {
            const urls = document.getElementById('urls').value
                .split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
            
            const count = urls.length;
            document.getElementById('urlCount').textContent = 
                `${count} URL${count !== 1 ? 's' : ''}`;
        }

        document.getElementById('urls').addEventListener('input', updateUrlCount);

        // フォーム送信（前回と同じ）
        document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const urls = document.getElementById('urls').value
                .split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
            
            if (urls.length === 0) {
                showError('URLを入力してください');
                return;
            }
            
            // 1つでも複数でも同じAPIを呼び出す
            // ...
        });
    </script>
</body>
</html>
```

---

## 📊 比較表

| 項目 | 1つのURL | 複数のURL |
|------|---------|----------|
| **入力方法** | 1行のみ | 複数行 |
| **処理時間** | 2-5分 | URL数 × 2-5分 |
| **結果** | 1つのフォルダ | 複数のフォルダ（1つのZIPにまとめる） |
| **UI** | シンプル（input要素） | テキストエリア |
| **実装** | 同じAPI（配列で1要素） | 同じAPI（配列で複数要素） |

---

## 🎯 推奨

### 現在の実装（複数URL対応）をそのまま使用

**理由**:
1. ✅ **1つのURLでも動作する**（配列に1要素だけ入れる）
2. ✅ **将来、複数のURLが必要になった場合に対応可能**
3. ✅ **実装がシンプル**（1つのAPIで両方に対応）
4. ✅ **UIも柔軟**（1行でも複数行でも入力可能）

### 使い方

**1つのURLの場合**:
```
https://example.com/page1
```

**複数のURLの場合**:
```
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

どちらでも同じUI・同じAPIで動作します！

---

## 💡 まとめ

- **現在の実装**: 1つのURLでも複数のURLでも動作 ✅
- **UI**: テキストエリアに1行でも複数行でも入力可能 ✅
- **API**: 配列形式で受け取るため、1つでも複数でも対応 ✅

**結論**: 現在の実装のままで、1つのURLだけの運用も複数のURLの運用も可能です！

---

**最終更新**: 2025年1月
