# autocode キャッシュ仕様詳細

本ドキュメントは、`nk_autocode` のキャッシュ保存・読込に関する詳細仕様を示します。README の概要に対する補足です。

## 保存場所の構造
- ルート: `_cache/autocode/`
  - ID ベース: `_cache/autocode/ids/{id}.py`
  - 構造ベース: `_cache/autocode/structure/{caller_no_ext}/{function_name}.py`
    - `caller_no_ext`: 呼び出し元ファイルの相対パスから拡張子を除いたもの（例: `samples/simple_sample.py` → `samples/simple_sample`）。

## 正規化ルール
- 呼び出し元パスは、現在のカレントディレクトリ（CWD）からの相対パスを使用します。
- 構造キャッシュでは、呼び出し元ファイルの拡張子（`.py`）を除去してディレクトリとし、その下に `{function_name}.py` を保存します。
- 例:
  - 呼び出し元: `samples/simple_sample.py`
  - 関数名: `my_add`
  - 保存先: `_cache/autocode/structure/samples/simple_sample/my_add.py`

## 読込の優先順位
1. ID 指定がある場合: `_cache/autocode/ids/{id}.py`
2. 構造キャッシュ: `_cache/autocode/structure/{caller_no_ext}/{function_name}.py`

※ 旧形式（`_cache/autocode/structure/{function_name}.py`）からのフォールバック読込は廃止しています。

## 再生成と上書き
- `regenerate=True` の場合はキャッシュを無視して再生成します。
- 成功した生成結果のみ、上記の場所に保存します（保存時に親ディレクトリは自動作成）。

## 注意事項 / 今後の改善
- 呼び出し元パスの基準は現在 CWD です。将来的にプロジェクトルート基準への切替を検討しています。
- 並行実行時の排他制御は行っていません。必要に応じてロック機構の導入を検討してください。
