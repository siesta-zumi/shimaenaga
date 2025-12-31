# Vercel + Supabase との違いと制限事項

## 📋 概要

既存のアプリをVercelとSupabaseで運用していてコストがかからない場合と、今回の画像取得システム（Playwright使用）との違いを説明します。

**最終更新**: 2025年1月

---

## 🔍 主な違い

### 1. 実行時間の制限

#### Vercelのサーバーレス関数の制限

| プラン | 実行時間制限 | 備考 |
|--------|------------|------|
| **無料プラン** | **10秒** | 1リクエストあたり最大10秒 |
| **Proプラン** | **60秒** | 1リクエストあたり最大60秒 |
| **Enterprise** | **300秒（5分）** | 1リクエストあたり最大5分 |

#### 画像取得システムの処理時間

| 処理内容 | 想定時間 | Vercel無料枠 | Vercel Pro |
|---------|---------|-------------|-----------|
| **1URLの処理** | 2-5分 | ❌ 制限超過 | ❌ 制限超過 |
| **10URLの処理** | 10-30分 | ❌ 制限超過 | ❌ 制限超過 |
| **Playwright起動** | 5-10秒 | ⚠️ ギリギリ | ✅ 可能 |
| **ページ読み込み** | 3-10秒 | ⚠️ ギリギリ | ✅ 可能 |
| **スクロール処理** | 30-60秒 | ❌ 制限超過 | ⚠️ ギリギリ |
| **画像ダウンロード** | 1-5分 | ❌ 制限超過 | ❌ 制限超過 |

**結論**: Vercelのサーバーレス関数では、画像取得処理の実行時間が制限を超えるため、**そのままでは使用できません**。

---

### 2. メモリ制限

#### Vercelのサーバーレス関数のメモリ制限

| プラン | メモリ制限 | 備考 |
|--------|-----------|------|
| **無料プラン** | **1GB** | 1リクエストあたり最大1GB |
| **Proプラン** | **1GB** | 1リクエストあたり最大1GB |
| **Enterprise** | **3GB** | 1リクエストあたり最大3GB |

#### Playwrightのメモリ消費

| コンポーネント | メモリ消費 | Vercel無料枠 | Vercel Pro |
|---------------|-----------|-------------|-----------|
| **Chromiumブラウザ** | 200-500MB | ⚠️ ギリギリ | ⚠️ ギリギリ |
| **ページ読み込み** | 100-300MB | ⚠️ ギリギリ | ⚠️ ギリギリ |
| **画像バッファ** | 50-200MB | ⚠️ ギリギリ | ⚠️ ギリギリ |
| **合計** | **350-1,000MB** | ⚠️ **ギリギリ** | ⚠️ **ギリギリ** |

**結論**: メモリ制限内で動作する可能性はありますが、**余裕がなく、エラーが発生しやすい**です。

---

### 3. ファイルサイズの制限

#### Vercelのサーバーレス関数の制限

| 項目 | 制限 | 備考 |
|------|------|------|
| **レスポンスサイズ** | **4.5MB** | サーバーレス関数のレスポンス最大サイズ |
| **デプロイサイズ** | **100MB** | デプロイパッケージの最大サイズ |

#### 画像取得システムの出力サイズ

| 出力内容 | 想定サイズ | Vercel制限 | 問題 |
|---------|-----------|-----------|------|
| **1URLの画像（10-50枚）** | 5-50MB | ❌ 4.5MB超過 | **ダウンロード不可** |
| **10URLの画像（100-500枚）** | 50-500MB | ❌ 4.5MB超過 | **ダウンロード不可** |
| **ZIPファイル** | 5-500MB | ❌ 4.5MB超過 | **ダウンロード不可** |

**結論**: 画像ファイルをZIP化してダウンロードする場合、**Vercelのレスポンスサイズ制限（4.5MB）を超える**ため、そのままでは使用できません。

---

### 4. Playwrightのブラウザエンジン

#### 問題点

1. **ブラウザバイナリのサイズ**
   - Chromiumバイナリ: 約150-300MB
   - Vercelのデプロイサイズ制限（100MB）を超える可能性

2. **起動時間**
   - Playwrightの起動: 5-10秒
   - Vercelの実行時間制限（10秒）と競合

3. **サーバーレス環境での動作**
   - サーバーレス関数は一時的な環境
   - ブラウザの起動・終了を毎回行う必要がある
   - コールドスタートの遅延が大きい

---

## 💡 Vercel + Supabaseで実現する方法

### 方法1: 非同期処理 + 外部ストレージ（推奨）

#### アーキテクチャ

```
[フロントエンド]
Vercel (Next.js)
  ↓ API呼び出し（10秒以内）
[バックエンド API]
Vercel Serverless Function
  ↓ タスク登録（10秒以内）
[Supabase]
タスク情報を保存
  ↓ 非同期処理をトリガー
[外部ワーカー]
別サーバー（VPS等）でPlaywright実行
  ↓ 結果を保存
[Supabase Storage]
画像ファイルを保存
  ↓ 完了通知
[フロントエンド]
ポーリングで進捗確認
  ↓ ダウンロード
[Supabase Storage]
ZIPファイルをダウンロード
```

#### コスト

| 項目 | サービス | 月額費用 | 備考 |
|------|---------|---------|------|
| **フロントエンド** | Vercel無料プラン | ¥0 | 制限内で使用可能 |
| **API** | Vercel無料プラン | ¥0 | タスク登録のみ（10秒以内） |
| **データベース** | Supabase無料プラン | ¥0 | タスク情報保存 |
| **ストレージ** | Supabase無料プラン | ¥0 | 1GBまで無料 |
| **ワーカー** | VPS（ConoHa 2GB） | ¥1,000 | Playwright実行用 |
| **合計** | | **¥1,000/月** | |

**メリット**:
- VercelとSupabaseの無料枠を最大限活用
- 長時間処理は外部ワーカーで実行
- コストを最小化

**デメリット**:
- 外部ワーカー（VPS）が必要
- アーキテクチャが複雑

---

### 方法2: Supabase Edge Functions（検討中）

#### アーキテクチャ

```
[フロントエンド]
Vercel (Next.js)
  ↓ API呼び出し
[Supabase Edge Functions]
Playwright実行（制限あり）
  ↓ 結果保存
[Supabase Storage]
画像ファイルを保存
```

#### 制限事項

| 項目 | Supabase Edge Functions | 画像取得システム | 問題 |
|------|------------------------|----------------|------|
| **実行時間** | 60秒（無料）、300秒（Pro） | 2-5分/URL | ⚠️ 制限超過の可能性 |
| **メモリ** | 256MB（無料）、512MB（Pro） | 350-1,000MB | ❌ メモリ不足 |
| **ファイルサイズ** | 制限あり | 5-500MB | ⚠️ 制限超過の可能性 |

**結論**: Supabase Edge Functionsも、**実行時間とメモリの制限により、そのままでは使用が困難**です。

---

### 方法3: Vercel + 外部API（完全サーバーレス）

#### アーキテクチャ

```
[フロントエンド]
Vercel (Next.js)
  ↓ API呼び出し
[外部API]
Browserless.io / ScrapingBee
  ↓ 結果取得
[Supabase Storage]
画像ファイルを保存
```

#### コスト

| 項目 | サービス | 月額費用 | 備考 |
|------|---------|---------|------|
| **フロントエンド** | Vercel無料プラン | ¥0 | |
| **ブラウザAPI** | Browserless.io | ¥0-5,000 | 無料枠あり、使用量ベース |
| **ストレージ** | Supabase無料プラン | ¥0 | 1GBまで無料 |
| **合計** | | **¥0-5,000/月** | 使用量による |

**メリット**:
- 完全サーバーレス
- メンテナンス不要
- スケーラブル

**デメリット**:
- 外部APIのコストが発生する可能性
- カスタマイズが制限される

---

## 📊 比較表

### 既存アプリ（Vercel + Supabase）との違い

| 項目 | 既存アプリ | 画像取得システム | 違い |
|------|----------|-----------------|------|
| **実行時間** | 1秒未満 | 2-5分/URL | ⚠️ **100-300倍長い** |
| **メモリ消費** | 50-200MB | 350-1,000MB | ⚠️ **2-5倍多い** |
| **ファイルサイズ** | 数KB-数MB | 5-500MB | ⚠️ **100-1000倍大きい** |
| **ブラウザエンジン** | 不要 | 必要（150-300MB） | ⚠️ **追加リソース必要** |
| **処理方式** | 同期処理 | 非同期処理が必要 | ⚠️ **アーキテクチャが複雑** |

---

## 🎯 推奨アプローチ

### ハイブリッド構成（Vercel + Supabase + VPS）

既存のVercel + Supabaseの構成を活用しつつ、長時間処理のみ外部ワーカーで実行する方法が最もコスト効率が良いです。

#### 構成

```
[フロントエンド]
Vercel (Next.js) - 無料
  ↓
[API]
Vercel Serverless Function - 無料（タスク登録のみ）
  ↓
[データベース]
Supabase - 無料（タスク情報保存）
  ↓
[ストレージ]
Supabase Storage - 無料（1GBまで）
  ↓
[ワーカー]
VPS（ConoHa 2GB） - ¥1,000/月（Playwright実行）
```

#### コスト

- **月額**: ¥1,000/月（VPSのみ）
- **年間**: ¥12,000

#### メリット

✅ VercelとSupabaseの無料枠を最大限活用  
✅ 既存のインフラを再利用可能  
✅ コストを最小化（¥1,000/月）  
✅ スケーラブル（必要に応じてVPSをアップグレード）

---

## 💰 コスト比較

### 完全VPS構成 vs ハイブリッド構成

| 項目 | 完全VPS構成 | ハイブリッド構成 |
|------|-----------|----------------|
| **フロントエンド** | VPS内で実行 | Vercel無料 |
| **API** | VPS内で実行 | Vercel無料 |
| **データベース** | VPS内で実行 | Supabase無料 |
| **ストレージ** | VPS内蔵 | Supabase無料（1GBまで） |
| **ワーカー** | VPS内で実行 | VPS（¥1,000/月） |
| **月額コスト** | ¥2,100/月 | **¥1,000/月** |
| **年間コスト** | ¥25,200 | **¥12,000** |

**結論**: ハイブリッド構成の方が**約50%コスト削減**できます。

---

## 🔧 実装例

### Vercel Serverless Function（タスク登録）

```typescript
// pages/api/scrape.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
)

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const { urls } = req.body

  // タスクをSupabaseに登録（10秒以内）
  const { data, error } = await supabase
    .from('scrape_tasks')
    .insert({
      urls: urls,
      status: 'pending',
      created_at: new Date().toISOString()
    })
    .select()
    .single()

  if (error) {
    return res.status(500).json({ error: error.message })
  }

  // 外部ワーカーに通知（Webhook等）
  // または、ワーカーがポーリングで取得

  return res.status(200).json({ task_id: data.id })
}
```

### 外部ワーカー（VPS上で実行）

```python
# worker.py
import time
import requests
from supabase import create_client
from 画像一括取得 import scrape_single_url_js
from playwright.sync_api import sync_playwright

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_task(task_id, urls):
    """タスクを処理"""
    # ステータスを更新
    supabase.table('scrape_tasks').update({
        'status': 'processing'
    }).eq('id', task_id).execute()
    
    # Playwrightで画像取得
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        results = []
        for url in urls:
            result = scrape_single_url_js(url, result_root, browser)
            results.append(result)
        browser.close()
    
    # 結果をSupabase Storageにアップロード
    # ZIP化してアップロード
    # ...
    
    # ステータスを完了に更新
    supabase.table('scrape_tasks').update({
        'status': 'completed',
        'result_url': zip_url
    }).eq('id', task_id).execute()

# ポーリングでタスクを取得
while True:
    tasks = supabase.table('scrape_tasks').select('*').eq('status', 'pending').limit(1).execute()
    if tasks.data:
        task = tasks.data[0]
        process_task(task['id'], task['urls'])
    time.sleep(5)  # 5秒ごとにチェック
```

---

## 📝 まとめ

### なぜ既存アプリは無料で動くのか

1. **実行時間が短い**（1秒未満）
   - Vercelの10秒制限内
   
2. **メモリ消費が少ない**（50-200MB）
   - Vercelの1GB制限内
   
3. **ファイルサイズが小さい**（数KB-数MB）
   - Vercelの4.5MB制限内
   
4. **ブラウザエンジンが不要**
   - 追加リソース不要

### なぜ画像取得システムはコストがかかるのか

1. **実行時間が長い**（2-5分/URL）
   - Vercelの10秒制限を**大幅に超過**
   
2. **メモリ消費が多い**（350-1,000MB）
   - Vercelの1GB制限と**ギリギリ**
   
3. **ファイルサイズが大きい**（5-500MB）
   - Vercelの4.5MB制限を**大幅に超過**
   
4. **ブラウザエンジンが必要**（150-300MB）
   - 追加リソースが必要

### 推奨ソリューション

**ハイブリッド構成**:
- Vercel + Supabase（無料）: フロントエンド、API、データベース、ストレージ
- VPS（¥1,000/月）: Playwright実行用ワーカー

**月額コスト**: ¥1,000/月（既存アプリと同じインフラを活用）

---

**最終更新**: 2025年1月
