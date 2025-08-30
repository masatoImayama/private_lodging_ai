いいですね。PoC（実現性検証）向けに、**“最小で動く”**構成にグッと絞って準備→実装指示まで一本化します。UIなし、**/ingest** と **/chat** だけで回す版です。

---

# ① 事前準備（GCP）

**A. プロジェクト & 認証**

* 新規GCPプロジェクト作成（例：`proj-rag-poc`）
* オーナー権限のあるアカウントで`gcloud init`
* サービスアカウント：`sa-rag-api@<project>.iam.gserviceaccount.com`

**B. API有効化**

* Vertex AI, Vertex AI Vector Search
* Cloud Run, Cloud Build
* Cloud Storage, Secret Manager
* (非同期を後で使うなら) Pub/Sub or Cloud Run Jobs

```bash
gcloud services enable aiplatform.googleapis.com run.googleapis.com \
  storage.googleapis.com secretmanager.googleapis.com
```

**C. ストレージ & 権限**

* GCSバケット：`gs://<project>-rag-poc`

  * パス構造：`tenants/<tenant_id>/raw/`（原本）, `tenants/<tenant_id>/index/`（メタ）
* サービスアカウントに付与（最小）

  * Storage Object Admin（PoC簡略化のため）
  * Vertex AI User
  * Secret Manager Secret Accessor
  * (Vector Search用) Vertex AI Administrator でも可（PoC簡易化）

**D. Vector Search インデックス作成（単一index＋namespace運用）**

* 名前：`rag_poc_index`
* ディメンション：`768`（`text-embedding-004`想定）
* 距離：コサイン
* Namespace（＝tenant\_id）で分離

※初回はConsoleからウィザードで作成→IDを控える（`INDEX_ID` & `INDEX_ENDPOINT_ID`）

**E. シークレット（.env相当）**

* `PROJECT_ID`, `LOCATION`（例：`asia-northeast1`）, `BUCKET_NAME`, `INDEX_ID`, `INDEX_ENDPOINT_ID`
* 必要に応じて`ALLOWED_ORIGINS`等

---

# ② 最小実装の仕様（API＋バックエンド）

## エンドポイント

1. `POST /ingest`

* 入力：`{ "tenant_id": "t_001", "gcs_uri": "gs://.../file.pdf", "doc_id": "doc-2025-001" }`
* 処理：抽出（PDF→テキスト）→ 分割（`chunk_size=1400, overlap=160`）→ 重複検知（checksum）→ 埋め込み生成（`text-embedding-004`）→ Vertex Vector Search に *upsert*（namespace=tenant）
* 出力：`{ "job_id": "<uuid>", "doc_id": "...", "chunks": <n> }`
* 成否は同期でOK（PoC）。5MB以上や巨大PDFは後で非同期に切替。

2. `POST /chat`

* 入力：`{ "tenant_id": "t_001", "query": "○○の手順は？", "top_k": 15 }`
* 処理：Vector Search（namespace=tenant, top\_k=30）→ MMR/RRFで10〜15に圧縮 → Gemini 1.5 Proで回答生成（`temperature=0.3, max_tokens=800`）**＋引用必須**
* 出力：

```json
{
  "answer": "…",
  "citations": [
    { "doc_id": "doc-2025-001", "page": 3, "path": "gs://.../file.pdf", "chunk_id": "c-00012", "checksum": "sha256:..." }
  ],
  "latency_ms": 4200
}
```

## コード構成（PoC最小）

```
/app
  /api
    main.py            # FastAPI: /ingest /chat /healthz
  /rag
    indexer.py         # extract→split→embed→upsert
    retriever.py       # vector search (namespace filter)
    generator.py       # Gemini呼び出し＋構造化出力
  /schemas
    dto.py             # Pydanticモデル（リクエスト/レスポンス）
  /utils
    pdf.py             # pypdfでテキスト抽出
    chunks.py          # chunk関数
    hash.py            # sha256チェックサム
```

## 依存ライブラリ（例）

* `fastapi`, `uvicorn`, `pydantic`
* `google-cloud-aiplatform`（Gemini/Embeddings/Vector Search）
* `google-cloud-storage`
* `pypdf`（PoCの抽出用／スキャンPDFは対象外）
* （お好みで）`tenacity`（リトライ）

---

# ③ AIに書かせる「指示書（プロンプト）」

下記を**そのままAIコーディング用の指示**として使えます。
（リポジトリの初回コミットに向けた明確なゴールと受入条件を含みます）

---

## ■ ゴール

GCP（Vertex AI + Vector Search）で、**/ingest** と **/chat** が動作する最小RAG APIをPython（FastAPI）で構築する。UIなし。**tenant\_idでデータを分離**し、**引用を必ず返す**。

## ■ 制約と前提

* ランタイム：Python 3.11 / FastAPI（Cloud Run向け）
* Embedding：`text-embedding-004`（768次元）
* 生成：`gemini-1.5-pro`
* ベクタ検索：Vertex AI Vector Search（index/endpointは既存）
* ストレージ：GCS（原本PDF/テキスト）
* 分割：`chunk_size=1400, overlap=160`
* 文字コード：UTF-8
* PoCのため**同期処理**でOK（将来非同期に切替可能な関数設計）

## ■ 受入基準（Acceptance Criteria）

1. `POST /ingest` に PDFのGCSパスを渡すと、**N件以上のチャンクがindexに登録**される（1件以上でOK）。
2. `POST /chat` に `tenant_id` と質問を渡すと、**10秒以内**に

   * 回答本文（自然文）
   * **引用配列**（doc\_id, page, path, chunk\_id, checksum）
   * レイテンシ
     を返す。
3. ベクタ登録・検索は**namespace=tenant\_id**で分離され、**他テナントの文書は出ない**。
4. 生成プロンプトで**引用必須**が担保される（引用ゼロのときは再試行 or エラー）。
5. ローカル実行（`uvicorn`）とCloud Runデプロイの両方で動作。

## ■ 実装タスク

### 1. 環境・設定

* `.env`（またはSecret Manager）から以下を読み込む：

  * `PROJECT_ID`, `LOCATION`, `BUCKET_NAME`, `INDEX_ID`, `INDEX_ENDPOINT_ID`
* `aiplatform.init(project=..., location=...)` 初期化関数

### 2. スキーマ（/schemas/dto.py）

* `IngestRequest { tenant_id: str, gcs_uri: str, doc_id: str }`
* `IngestResponse { job_id: str, doc_id: str, chunks: int }`
* `ChatRequest { tenant_id: str, query: str, top_k: int=15 }`
* `Citation { doc_id: str, page: int, path: str, chunk_id: str, checksum: str }`
* `ChatResponse { answer: str, citations: List[Citation], latency_ms: int }`

### 3. 抽出・分割（/utils/pdf.py, /utils/chunks.py）

* `extract_text_from_pdf(gcs_uri) -> List[PageText]`

  * GCSからローカルへ一時ダウンロード → pypdfでページ文字列
* `make_chunks(pages: List[str], size=1400, overlap=160) -> List[Chunk]`

  * `chunk_id`は連番
  * `page`情報を保持

### 4. 埋め込み & upsert（/rag/indexer.py）

* `embed_texts(texts: List[str]) -> List[List[float]]`（`text-embedding-004`）
* `upsert_vectors(tenant_id, doc_id, chunks, embeddings)`

  * Vector Searchへ**namespace=tenant\_id**でupsert
  * payload（最小）：`tenant_id, doc_id, chunk_id, page, path, checksum, preview_text(先頭200字)`

### 5. 検索（/rag/retriever.py）

* `search(tenant_id, query, top_k_vector=30) -> List[ChunkHit]`

  * Embedding生成 → Vector Searchに対してnamespace指定で検索
  * MMR（単純でOK）で**10〜15件**に圧縮

### 6. 生成（/rag/generator.py）

* `generate_answer(query, hits) -> (answer: str, citations: List[Citation])`
* プロンプト（システム）例：

  ```
  あなたは社内ドキュメントに基づいて回答するアシスタントです。
  回答は登録文書の根拠に厳密に依拠してください。根拠が不十分な場合は「不明」と述べ、想像で補完しないでください。
  出力には、回答本文に加えて参照したチャンクの {doc_id, page, path, chunk_id, checksum} を必ず含めます。
  ```
* コンテキスト整形： `hit.preview_text` ではなく**フルチャンクテキスト**をプロンプト投入
  （payloadに全文は持たせないので、必要に応じてGCSから当該ページテキストをメモリ展開）

### 7. API（/api/main.py）

* `POST /ingest`：上記フローを直列に実行、結果返却
* `POST /chat`：`search`→`generate_answer`、`time.perf_counter()`でlatency計測
* `GET /healthz`：`{"status":"ok"}`

### 8. 例外処理・バリデーション

* GCSパス不正、PDF抽出失敗、embedding/生成API失敗時のHTTP 4xx/5xx
* `tenant_id`空を**400**で弾く
* 引用0件時は**409**か**422**（PoCの方針に合わせて）

### 9. ローカル動作 & デプロイ

* ローカル：`uvicorn app.api.main:app --reload --port 8080`
* Dockerfile（シンプルに）→ Cloud Build → Cloud Run デプロイ
* 環境変数はRunのリビジョンに設定（本番はSecret Manager）

## ■ テスト（最低限）

1. **ingest→chat通し**：サンプルPDF（3〜5ページ）を投入→質問→引用あり回答
2. **tenant分離**：`t_001`に入れた文書が、`t_002`の質問で出ない
3. **性能**：`/chat`が**10秒未満**で返る（3〜5回平均）
4. **エラー**：存在しないGCSパスで`/ingest`→4xx

---

# ④ 動作確認の手順（超要約）

1. GCSにPDFを置く：`gs://<project>-rag-poc/tenants/t_001/raw/sample.pdf`
2. `/ingest` を叩く：

```json
{ "tenant_id": "t_001", "gcs_uri": "gs://<...>/sample.pdf", "doc_id": "doc-001" }
```

3. `/chat` を叩く：

```json
{ "tenant_id": "t_001", "query": "sample.pdfの○○について教えて" }
```

4. `answer` と `citations[]` が返ること、`citations[].path` がGCSの原本を指すことを確認。

---

# ⑤ ここまでで足りないときの“つまみ”

* スキャンPDFが混ざる → **Document AI** を抽出に差し替え
* 引用の正確性を上げたい → `generate_answer`前に**要約整形**（チャンクの圧縮）を挟む
* 低コスト化 → 既知FAQは**キャッシュ**（query正規化キー）

---

これで**最小PoC**は走らせられます。
必要なら、この指示書をもとに\*\*テンプレのFastAPIリポジトリ（Docker対応）\*\*の雛形テキストも一括で出します。
