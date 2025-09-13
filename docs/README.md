# プロジェクトドキュメント

本ドキュメントは、リポジトリ構成、各モジュールの役割、主要な利用フロー、開発・運用のコマンドを詳細にまとめたものです。日常の作業方針やコーディング規約は AGENTS.md を参照し、構造や仕様の詳細は本ドキュメントを参照してください。

## 目的
- nk_autocode: 実行時に LLM を用いて関数コードを生成し、キャッシュ・対話編集・エラーフィードバックを通じて安定化する仕組みを提供します。
- nk_autodoc: 文章生成・計画立案・コンテキスト圧縮を構成し、段階的にドキュメントを組み立てるためのユーティリティを提供します。

## ディレクトリ構成
```
.
├── nk_autocode/                 # 実行時コード生成コア
│   ├── __init__.py             # 公開API: autocode, setup_autocode ほか
│   ├── editor.py               # 外部エディタ連携（$EDITOR）
│   ├── framework.py            # 型・抽象基底（Context, BaseAgent など）
│   └── presets/
│       ├── assistant.py        # Assistant 実装（対話・キャッシュ・検証）
│       ├── default.py          # 既定のエントリ（autocode/setup_autocode の実体）
│       └── openai_agent.py     # OpenAI API を使うエージェント
│
├── nk_autodoc/                 # 自動ドキュメント生成
│   ├── __init__.py
│   ├── framework.py            # Writer/Compressor/Model 抽象と Context
│   ├── presets/
│   │   ├── compressors.py      # コンテキスト圧縮（スコープ対応）
│   │   ├── default.py          # 既定プリセット（Writer, Compressor 構築）
│   │   ├── models.py           # OpenAI Responses API ラッパ
│   │   ├── outputs.py          # 出力先（IO/ファイル）
│   │   └── writers.py          # Writer 実装（文章/計画生成）
│   └── utils/
│       └── auto_type.py        # LLM で pydantic モデル定義を生成・パース
│
├── samples/                    # 最小実行例（ライブラリからは import しない）
│   ├── simple_sample.py        # 単純な関数生成と実行
│   ├── decorator_sample.py     # デコレータによる生成
│   ├── dry_run_sample.py       # dry-run の挙動
│   ├── typing_sample.py        # 型・可変長引数の指定例
│   └── setup_sample.py         # 設定変更とキャッシュ再利用
│
├── _cache/                     # 実行時キャッシュ（autocode が生成）
│   └── autocode/
│       ├── ids/                # id ベースのキャッシュ
│       └── structure/          # 呼び出し元パス+関数名ベース
│
├── README.md                   # クイックな使い方の例
├── AGENTS.md                   # 作業ガイドライン（ビルド/規約/方針）
├── Makefile                    # lint/format/test タスク
└── pyproject.toml              # パッケージ/ツール設定
```

## nk_autocode の詳細
- 主要API
  - `autocode(description, args, kwargs, name, id, ...) -> BaseGeneratedCode`
    - OpenAI によるコード生成 → `exec` でロード → 関数存在/呼び出し性を検証。
    - 対話モードでは承認/編集/否認（フィードバック）を繰り返し、合格時にキャッシュ保存。
    - キャッシュキー: `id` 優先、なければ「呼出元パス + 関数名」。
  - `setup_autocode(dotenv_path=None, verbose=False, interactive=False, regenerate=False, ...)`
    - 既定エージェント（`OpenAIAgent`）、対話/冗長ログ/再生成、`EDITOR` 連携、dry-run 既定関数を設定。
- エージェント
  - `OpenAIAgent(model="gpt-4.1", temperature=0)` が既定。`Context` からプロンプトを構成し Responses API を呼び出し。
  - コードブロックを抽出（```python ... ``` 優先）し、検証のうえ保存・実行。
- 対話・編集
  - 生成コードの表示 → `y/n/e` 選択。`e` で `$EDITOR` を起動し、保存後の内容を採用。
  - 否認時はフィードバック文を収集し、次回プロンプトに付与。
- dry-run
  - 生成を行わず、`return_value()`/`print_and_exception()` などの関数で挙動を仮置き。
- デコレータ/上書き
  - `@autocode(decorator=True)` で型付き関数宣言から生成。
  - `override="pkg.module:func"` で既存実装を利用可能。

## nk_autodoc の詳細
- Writer / Compressor / Model の三層で構成
  - `Writer`: 文章生成・計画立案。`sub_writer()` で分割し、`add_context()` で統合。
  - `Compressor`: スコープを考慮して文脈を圧縮。`compress()` で Writer の文脈を縮約。
  - `OpenAIModel`: テキスト/画像混在入力に対応。構造化が必要な場合は pydantic でパース。
- 型自動生成
  - `utils/auto_type.py` の `auto_type()` が、型記述から pydantic モデル定義（コード+クラス名）を LLM に生成させ、パースして `Type[BaseModel]` を返却。

## 環境変数と設定
- 必須: `OPENAI_API_KEY`
- 任意: `EDITOR`（対話編集）
- `.env` はコミットしない。`setup_autocode(dotenv_path=".env")` で読込可。
- キー未設定時でもビルド/テストが失敗しない設計（実行時に API 呼出を行う箇所のみ依存）。

## セットアップと開発コマンド
- セットアップ（例）
  - `uv sync && uv run make test`
  - または `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev] && make test`
- タスク
  - `make lint`: ruff による静的解析/整形チェック + mypy 型検査
  - `make format`: ruff で整形＋自動修正
  - `make test`: pytest 実行
- コーディング規約
  - Python 3.12、行長 120、ダブルクォート、4スペースインデント
  - 公開関数は型ヒント必須（mypy で検証）

## サンプルの使い方
- 実際のユースケースは `samples/` を参照。ライブラリ本体からは import しないこと。
  - `simple_sample.py`: 最小の関数生成と実行
  - `decorator_sample.py`: デコレータによる生成
  - `dry_run_sample.py`: dry-run 検証
  - `typing_sample.py`: 型・可変長引数の指定
  - `setup_sample.py`: 設定の切替とキャッシュ再利用

## キャッシュ仕様（autocode）
- ルート: `_cache/autocode`
  - `ids/{id}.py`: `id` 指定時の保存先
  - `structure/{caller_no_ext}/{name}.py`: 呼び出し元パス（拡張子除去）+ 関数名指定時
- 参照順: `id` → `caller_path + name`
- 保存条件: 生成が承認・検証通過した時点で書き出し

詳細は `docs/autocode_cache.md` を参照してください。

## セキュリティ/注意事項
- APIキーや `.env` はコミットしない。
- 実行時に `exec` を用いるため、不審な入力や改変コードの実行に注意（対話編集時は特に確認すること）。
