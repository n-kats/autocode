# Repository Guidelines

## プロジェクト概要
- nk_autocode: 実行時コード生成の中核。主要APIは `autocode()` と `setup_autocode()`。
  - OpenAI（既定 `gpt-4.1`）で関数コードを生成し、`exec` により関数の存在・呼び出し性を検証。
  - 対話モードでの承認/再編集（`EDITOR` 起動）/否認→フィードバック再生成に対応。
  - キャッシュ保存と再利用（`_cache/autocode/{ids,structure}`）。`id` 優先、次に呼び出し元パス+関数名。
  - デコレータ利用、dry-run（`return_value`/`print_and_exception`）、外部関数での上書き（`override="pkg.mod:func"`）。
- nk_autodoc: 自動ドキュメント生成のユーティリティ。
  - `Writer`/`Compressor`/`OpenAIModel` を用いて計画と文章を段階生成。
  - `auto_type()` で LLM に pydantic モデル定義を生成させ、構造化出力をパース。
- サンプル: `samples/` に最小例（simple/decorator/dry_run/typing/setup）。
- 環境変数: `OPENAI_API_KEY` 必須、`EDITOR` 任意。`.env` を `setup_autocode(dotenv_path=...)` で読込可能。
- 開発運用: `make lint`/`format`/`test`、Python 3.12、ruff/mypy/pytest に準拠。

### 詳細ドキュメント
- リポジトリ構造や設計のより詳しい情報は `docs/README.md` を参照してください。

## プロジェクト構成とモジュール
- `nk_autocode/`: 実行時コード生成のコア（API、プリセット、編集ユーティリティ）。
- `nk_autodoc/`: 自動ドキュメント生成ユーティリティ（writers、compressors、presets）。
- `samples/`: 最小例。ライブラリ本体からは import しないこと。
- `docker/`・`_tmp/`・`_cache/`: 運用/作業用。ロジックやテスト対象外。
- ルート: `Makefile`、`pyproject.toml`、`README.md` などのメタ/設定。

## ビルド・テスト・開発コマンド
- `make lint`: Ruff による静的解析/インポート整形 + MyPy 型チェック。
- `make format`: Ruff で整形し、自動修正可能な指摘を反映。
- `make test`: `pytest` によるテスト実行。
- セットアップ（どちらか）:
  - `uv sync` の後に `uv run make test`
  - もしくは `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev] && make test`

## コーディングスタイルと命名
- Python 3.12、行長 120、ダブルクォート、インデント 4 スペース。
- 公開関数は型ヒント必須（`mypy` で検証）。
- 命名: モジュール/関数は `snake_case`、クラスは `PascalCase`、定数は `UPPER_SNAKE_CASE`。
- 体裁は `ruff` を唯一の基準とし、コミット前に `make format` 実行。

## テスト指針
- フレームワーク: `pytest`。
- 配置: `tests/` にパッケージ構成を反映（例: `tests/nk_autocode/test_editor.py`）。
- 命名: ファイルは `test_*.py`、テストは `test_*` 関数または `Test*` クラス。
- 速く再現性の高いテストを優先。グローバルより fixture を使用。必要な例は `samples/` に最小限追加。

## コミットとプルリクエスト
- メッセージは短く現在形。履歴の慣例（例: 「README更新」「編集機能を追加」）に合わせる。
- 変更は小さく粒度を保つ。必要なら理由/背景を簡潔に記載。Issue 連携: `Fixes #123`。
- PR には概要、動機、UX/CLI 変更のログ/スクリーンショット、テスト観点を含める。ユーザー影響は `README.md` を更新。

## セキュリティと設定
- 必須環境変数: `OPENAI_API_KEY`。任意: `EDITOR`。
- `.env` や鍵はコミットしない。キー未設定時もビルド/テストが落ちない実装にする。

## 言語ポリシー（日本語を基本）
- ドキュメント、コードコメント、コミット/PR 本文は原則「日本語」を基本とする。
- 外部公開や国際的やり取りが想定される箇所は英語併記を推奨。
- 公開 API の識別子（関数名/引数名など）は可読性維持のため英語を用いる。

## エージェント向け指示
- 本ガイドの構成・スタイル・コマンドに従うこと。
- 無関係な変更を避け、差分は最小限・焦点化すること。
