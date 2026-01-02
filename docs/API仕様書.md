# API仕様書

## 📋 概要

画像一括取得システムのAPI仕様です。このAPIは、他のアプリケーションからも呼び出して使用できます。

**最終更新**: 2025年1月

---

## 🔌 APIエンドポイント

### POST `/api/scrape`

画像取得処理を実行し、結果をZIPファイルとして返します。

#### リクエスト

**URL**: `http://localhost:5000/api/scrape`  
**メソッド**: `POST`  
**Content-Type**: `application/json`

**リクエストボディ**:
```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ]
}
```

**パラメータ**:
- `urls` (array, required): 取得したいURLのリスト（1行1URL）

#### レスポンス

**成功時 (200 OK)**:
- **Content-Type**: `application/zip`
- **Content-Disposition**: `attachment; filename=result.zip`
- **ボディ**: ZIPファイル（バイナリ）

**エラー時 (400 Bad Request / 500 Internal Server Error)**:
- **Content-Type**: `application/json`
- **ボディ**:
```json
{
  "error": "エラーメッセージ"
}
```

---

## 💻 使用例

### 1. 現在のWebアプリ（index.html）から使用

```javascript
const response = await fetch('/api/scrape', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ urls: ['https://example.com/page1'] })
});

const blob = await response.blob();
// ZIPファイルをダウンロード
```

---

### 2. Pythonアプリケーションから使用

```python
import requests

# APIを呼び出し
response = requests.post(
    'http://localhost:5000/api/scrape',
    json={
        'urls': [
            'https://example.com/page1',
            'https://example.com/page2'
        ]
    },
    timeout=300  # 5分（処理に時間がかかる場合があるため）
)

if response.status_code == 200:
    # ZIPファイルを保存
    with open('result.zip', 'wb') as f:
        f.write(response.content)
    print('ダウンロード完了')
else:
    error = response.json()
    print(f'エラー: {error["error"]}')
```

---

### 3. Node.jsアプリケーションから使用

```javascript
const axios = require('axios');
const fs = require('fs');

async function scrapeImages(urls) {
    try {
        const response = await axios.post(
            'http://localhost:5000/api/scrape',
            { urls: urls },
            {
                responseType: 'arraybuffer',
                timeout: 300000  // 5分
            }
        );
        
        // ZIPファイルを保存
        fs.writeFileSync('result.zip', response.data);
        console.log('ダウンロード完了');
    } catch (error) {
        console.error('エラー:', error.response?.data || error.message);
    }
}

// 使用例
scrapeImages([
    'https://example.com/page1',
    'https://example.com/page2'
]);
```

---

### 4. cURLコマンドから使用

```bash
# リクエスト送信
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/page1"]}' \
  --output result.zip

# エラーの場合
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": []}'
# レスポンス: {"error": "URLが指定されていません"}
```

---

### 5. Vercel/Next.jsアプリケーションから使用

```typescript
// pages/api/trigger-scrape.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { urls } = req.body;

  try {
    // 画像取得APIを呼び出し
    const response = await fetch('http://your-server:5000/api/scrape', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ urls }),
    });

    if (!response.ok) {
      const error = await response.json();
      return res.status(response.status).json(error);
    }

    // ZIPファイルを取得
    const zipBuffer = await response.arrayBuffer();
    
    // クライアントに返す
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', 'attachment; filename=result.zip');
    res.send(Buffer.from(zipBuffer));
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

---

## 🔐 認証・セキュリティ

### 現在の実装

- **認証**: なし（ローカル環境での使用を想定）
- **CORS**: 有効（`flask-cors`を使用）

### 本番環境での推奨事項

1. **認証の追加**
   ```python
   from flask_httpauth import HTTPBasicAuth
   
   auth = HTTPBasicAuth()
   
   @auth.verify_password
   def verify_password(username, password):
       return username == 'admin' and password == 'secret'
   
   @app.route('/api/scrape', methods=['POST'])
   @auth.login_required
   def scrape():
       # ...
   ```

2. **APIキーの使用**
   ```python
   @app.route('/api/scrape', methods=['POST'])
   def scrape():
       api_key = request.headers.get('X-API-Key')
       if api_key != os.environ.get('API_KEY'):
           return jsonify({'error': 'Invalid API key'}), 401
       # ...
   ```

3. **レート制限**
   ```python
   from flask_limiter import Limiter
   
   limiter = Limiter(
       app,
       key_func=get_remote_address,
       default_limits=["10 per hour"]
   )
   
   @app.route('/api/scrape', methods=['POST'])
   @limiter.limit("5 per hour")
   def scrape():
       # ...
   ```

---

## ⚠️ 注意事項

### タイムアウト

- **処理時間**: 1URLあたり2-5分かかる場合があります
- **推奨タイムアウト**: 300秒（5分）以上
- **複数URL**: URL数 × 2-5分

### エラーハンドリング

- **ネットワークエラー**: タイムアウトや接続エラーが発生する可能性があります
- **処理エラー**: 一部のURLでエラーが発生しても、他のURLの処理は継続されます
- **リトライ**: クライアント側でリトライロジックを実装することを推奨します

### リソース消費

- **メモリ**: 1リクエストあたり350-1,000MB
- **CPU**: Playwrightのブラウザエンジンを使用
- **同時実行**: 複数のリクエストが同時に来ると、サーバーリソースを消費します

---

## 📊 レスポンス例

### 成功レスポンス

```
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename=result.zip
Content-Length: 1234567

[ZIPファイルのバイナリデータ]
```

### エラーレスポンス

```json
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "URLが指定されていません"
}
```

---

## 🔄 他のアプリケーションとの統合例

### ワークフロー自動化（n8n、Zapier等）

1. **n8nワークフロー**:
   - HTTP Requestノードで `/api/scrape` を呼び出し
   - 結果のZIPファイルを処理

2. **Zapier**:
   - WebhookトリガーでAPIを呼び出し
   - 結果をGoogle DriveやDropboxに保存

3. **Slack Bot**:
   - SlackコマンドでURLを送信
   - APIを呼び出して結果を返す

---

## 📝 まとめ

### APIの用途

1. **現在**: Webアプリ（`index.html`）から使用
2. **将来**: 他のアプリケーションからも使用可能

### 他のアプリケーションから使用できるか？

**はい、使用できます！**

- ✅ REST APIとして実装されている
- ✅ JSON形式でリクエスト/レスポンス
- ✅ 標準的なHTTPプロトコル
- ✅ どのプログラミング言語からでも呼び出し可能

### 使用可能なアプリケーション例

- Pythonアプリケーション
- Node.jsアプリケーション
- Vercel/Next.jsアプリケーション
- モバイルアプリ（React Native、Flutter等）
- ワークフロー自動化ツール（n8n、Zapier等）
- コマンドラインツール（cURL等）

---

**最終更新**: 2025年1月
