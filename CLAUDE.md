# システム構成

## エンドポイント

### POST `/ingest`

- **入力例**  
    ```json
    {
        "tenant_id": "t_001",
        "gcs_uri": "gs://.../file.pdf",
        "doc_id": "doc-2025-001"
    }
    ```

- **処理フロー**  
    抽出（PDF→テキスト）  
    → 分割（chunk_size=1400, overlap=160）  
    → 重複検知（checksum）  
    → 埋め込み生成（text-embedding-004）  
    → Vertex Vector Search に upsert（namespace=tenant）

- **出力例**  
    ```json
    {
        "job_id": "<uuid>",
        "doc_id": "...",
        "chunks": <n>
    }
    ```

- 成否は同期でOK（PoC）。5MB以上や巨大PDFは後で非同期に切替。

---

### POST `/chat`

- **入力例**  
    ```json
    {
        "tenant_id": "t_001",
        "query": "○○の手順は？",
        "top_k": 15
    }
    ```

- **処理フロー**  
    Vector Search（namespace=tenant, top_k=30）  
    → MMR/RRFで10〜15に圧縮  
    → Gemini 1.5 Proで回答生成（temperature=0.3, max_tokens=800）＋引用必須

- **出力例**  
    ```json
    {
        "answer": "…",
        "citations": [
            {
                "doc_id": "doc-2025-001",
                "page": 3,
                "path": "gs://.../file.pdf",
                "chunk_id": "c-00012",
                "checksum": "sha256:..."
            }
        ],
        "latency_ms": 4200
    }
    ```

---

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

---

## 依存ライブラリ（例）

- fastapi, uvicorn, pydantic
- google-cloud-aiplatform（Gemini/Embeddings/Vector Search）
- google-cloud-storage
- pypdf（PoCの抽出用／スキャンPDFは対象外）
- tenacity（リトライ, 任意）

---

# コーディング指示書

## ゴール

GCP（Vertex AI + Vector Search）で、`/ingest` と `/chat` が動作する最小RAG APIをPython（FastAPI）で構築する。UIなし。tenant_idでデータを分離し、引用を必ず返す。

## 制約と前提

- ランタイム：Python 3.11 / FastAPI（Cloud Run向け）
- Embedding：text-embedding-004（768次元）
- 生成：gemini-1.5-pro
- ベクタ検索：Vertex AI Vector Search（index/endpointは既存）
- ストレージ：GCS（原本PDF/テキスト）
- 分割：chunk_size=1400, overlap=160
- 文字コード：UTF-8
- PoCのため同期処理でOK（将来非同期に切替可能な関数設計）

## 受入基準（Acceptance Criteria）

- POST `/ingest` にPDFのGCSパスを渡すと、N件以上のチャンクがindexに登録される（1件以上でOK）。
- POST `/chat` にtenant_idと質問を渡すと、10秒以内に
    - 回答本文（自然文）
    - 引用配列（doc_id, page, path, chunk_id, checksum）
    - レイテンシ
    を返す。
- ベクタ登録・検索はnamespace=tenant_idで分離され、他テナントの文書は出ない。
- 生成プロンプトで引用必須が担保される（引用ゼロのときは再試行 or エラー）。
- ローカル実行（uvicorn）とCloud Runデプロイの両方で動作。

## 実装タスク

1. **環境・設定**  
     `.env`（またはSecret Manager）から以下を読み込む：  
     - PROJECT_ID, LOCATION, BUCKET_NAME, INDEX_ID, INDEX_ENDPOINT_ID  
     - `aiplatform.init(project=..., location=...)` 初期化関数

2. **スキーマ（/schemas/dto.py）**  
     - `IngestRequest { tenant_id: str, gcs_uri: str, doc_id: str }`
     - `IngestResponse { job_id: str, doc_id: str, chunks: int }`
     - `ChatRequest { tenant_id: str, query: str, top_k: int=15 }`
     - `Citation { doc_id: str, page: int, path: str, chunk_id: str, checksum: str }`
     - `ChatResponse { answer: str, citations: List[Citation], latency_ms: int }`

3. **抽出・分割（/utils/pdf.py, /utils/chunks.py）**  
     - `extract_text_from_pdf(gcs_uri) -> List[PageText]`  
         GCSからローカルへ一時ダウンロード → pypdfでページ文字列
     - `make_chunks(pages: List[str], size=1400, overlap=160) -> List[Chunk]`  
         chunk_idは連番、page情報を保持

4. **埋め込み & upsert（/rag/indexer.py）**  
     - `embed_texts(texts: List[str]) -> List[List[float]]`（text-embedding-004）
     - `upsert_vectors(tenant_id, doc_id, chunks, embeddings)`  
         Vector Searchへnamespace=tenant_idでupsert  
         payload（最小）：tenant_id, doc_id, chunk_id, page, path, checksum, preview_text(先頭200字)

5. **検索（/rag/retriever.py）**  
     - `search(tenant_id, query, top_k_vector=30) -> List[ChunkHit]`  
         Embedding生成 → Vector Searchに対してnamespace指定で検索  
         MMR（単純でOK）で10〜15件に圧縮

6. **生成（/rag/generator.py）**  
     - `generate_answer(query, hits) -> (answer: str, citations: List[Citation])`  
         プロンプト（システム）例：  
         ```
         あなたは社内ドキュメントに基づいて回答するアシスタントです。
         回答は登録文書の根拠に厳密に依拠してください。根拠が不十分な場合は「不明」と述べ、想像で補完しないでください。
         出力には、回答本文に加えて参照したチャンクの {doc_id, page, path, chunk_id, checksum} を必ず含めます。
         ```
         - コンテキスト整形：hit.preview_textではなくフルチャンクテキストをプロンプト投入  
             （payloadに全文は持たせないので、必要に応じてGCSから当該ページテキストをメモリ展開）

7. **API（/api/main.py）**  
     - POST `/ingest`：上記フローを直列に実行、結果返却
     - POST `/chat`：search→generate_answer、`time.perf_counter()`でlatency計測
     - GET `/healthz`：`{"status":"ok"}`

8. **例外処理・バリデーション**  
     - GCSパス不正、PDF抽出失敗、embedding/生成API失敗時のHTTP 4xx/5xx
     - tenant_id空を400で弾く
     - 引用0件時は409か422（PoCの方針に合わせて）

9. **ローカル動作 & デプロイ**  
     - ローカル：`uvicorn app.api.main:app --reload --port 8080`
     - Dockerfile（シンプルに）→ Cloud Build → Cloud Run デプロイ
     - 環境変数はRunのリビジョンに設定（本番はSecret Manager）

## テスト（最低限）

- ingest→chat通し：サンプルPDF（3〜5ページ）を投入→質問→引用あり回答
- tenant分離：t_001に入れた文書が、t_002の質問で出ない
- 性能：/chatが10秒未満で返る（3〜5回平均）
- エラー：存在しないGCSパスで/ingest→4xx

## モック機能の実装について
- 基本的に指示するまで、今後一切のモック機能の実装を禁じます。モックで動いたように見せても何も意味がないため、常に本体実装を正常化するように努めてください。