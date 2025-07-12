# autocode
実行時コード生成ライブラリ

## 使い方（構想）
```
from nk_autocode import autocode, setup_autocode

setup_autocode(dotenv_path=".env")  # .envファイルのパスを指定

# 最も簡単な例
fn = autocode("引数を足す", args=["a", "b"])
print(fn(1, 2))  # 3

# デバッグ用に関数を表示
## 全体的に表示する
setup_autocode(dotenv_path=".env", verbose=True)

## 関数毎に表示する
autocode("関数の説明", args=["a", "b"], verbose=True)

# 対話的に関数を生成する
## 全体的に対話的に生成する
setup_autocode(dotenv_path=".env", interactive=True)

## 関数毎に対話的に生成する
autocode("関数の説明", args=["a", "b"], interactive=True)

# 関数名を指定する
autocode("関数の説明", args=["a", "b"], name="my_function")

# IDをつける（ワークスペースでユニークなものを指定（uuidgenコマンドで生成するとよい）
# 関数と生成コードの対応優先度:
# 1. IDが指定されている場合
# 2. ファイルパスと関数名が一致する場合
# 3. ファイルパスと説明が一致する場合
autocode("関数の説明", args=["a", "b"], id="3aaf5a78-0efe-4928-852f-ecec20db1e5a")

# 再生成
## 全体的に再生成する
setup_autocode(dotenv_path=".env", regenerate=True, id="dummy_id")

## 関数毎に再生成する
autocode("関数の説明", args=["a", "b"], regenerate=True, id="dummy_id")

# 他の引数を使う場合
autocode("関数の説明", args=["a", "b"], use_extra_args=True, kwargs=["c", "d"], use_extra_kwargs=True)
# fn(a, b, *args, c, d, **kwargs) のような関数が生成される

# 型を宣言する場合（プロンプトに反映される）
# typeはpydanticの型の場合、jsonschemaでの説明がプロンプトに反映される
autocode(
  "関数の説明", 
  args=[{"var": "a", "type": int}, {"var": "b", "type": int, "default": 0}],
  use_extra_args=True, extra_args_type=int,
  kwargs=[{"var": "c", "type": int, "default": 0}],
  use_extra_kwargs=True, extra_extra_kwargs_type=int,
  return_type=int,
)

# デコレータとして使う（autocodeの引数は関数から補完される）
@autocode(decorator=True)
def add(a: int, b: int) -> int:
    """
    引数を足す関数
    """

# 既存コード関数利用・参照(未実装)
autocode("関数の説明", args=["a", "b"], tools=[calculation_wrapper], refs=["package.module:ref_function", my_ref_function, my_ref_module])])

# 手動関数で上書き
autocode("関数の説明", args=["a", "b"], override="package.module:function")

# dry-run（コードを生成せずに仮置きのコードを実行する）
from nk_autocode import autocode, setup_autocode, return_value, print_and_exception
setup_autocode(dry_run=True)  # autocodeの引数でもdry_run=Trueを指定可能
fn = autocode("引数を足す", args=["a", "b"], dry_run_fn=return_value(3))
print(fn(1, 2))  # 3
fn = autocode("引数を足す", args=["a", "b"], dry_run_fn=print_and_exception)
try:
    fn(1, 2)  # 引数を表示して例外を発生させる
except Exception as e:
    print(e)
fn = autocode("引数を足す", args=["a", "b"], dry_run=False)  # autocodeの引数でdry_run=Falseを指定するとsetup_autocodeより優先される
```

## autodoc - 自動ドキュメント生成

```python
from nk_autodoc.presets.default import writer, compressor

# シンプルな文章生成
writer("ツールの概要")

# 計画を立てる
plan = writer.plan("機能一覧作成", type_auto='{"items": [..., ...]}')

# 計画に基づいた詳細な文章生成
for item in plan.items:
    context = compressor(writer.context)
    context.add(item)
    sub_writer = writer.sub_writer(context=context)
    sub_writer(f"{item} の機能の説明をする")
    sub_writer.plan(f"{item} の例を考える")
    sub_writer(f"{item} の使い方を説明する")
    writer.add_context(sub_writer.context, compressor=compressor)

# コンテキストの圧縮
writer.compress(compressor=compressor)

# 追加の文章生成
writer("ツールの使い方の注意点")
```

## 環境変数
* OPENAI_API_KEY: （必須）OpenAI APIキー
* EDIOR: （オプション）編集時に用いるエディタ（なければ編集できないだけ）