# バイヤーノート 公開ページ

iOSアプリ「バイヤーノート」(旧「ウリログ」)のプライバシーポリシー・利用規約・サポートページです。

リポジトリ名とURLは `urilog-docs` のままにしてある。App Store Connect に登録済みの
プライバシーポリシーURLがこのパスを指しており、変えるとリンクが切れるため。
GitHub Pages で公開しています。

- [サポート](https://gool1618-design.github.io/urilog-docs/)
- [プライバシーポリシー](https://gool1618-design.github.io/urilog-docs/privacy-policy.html)
- [利用規約](https://gool1618-design.github.io/urilog-docs/terms.html)

アプリ本体のソースは別のリポジトリ(非公開)にあります。
このリポジトリは、App Store が要求する公開URLを用意するためだけのものです。

文面を変更するときは、アプリの実装と食い違わないか確認してください。
同意画面・設定画面に書かれている「何を送信するか」の説明と、
プライバシーポリシーの記述は一致している必要があります。

## planning/

新しいアプリの企画・仕様メモを置く場所。`_config.yml` の `exclude` で Pages のビルド対象から外している。
公開URLには出ないが、リポジトリは公開なので、非公開にしたい内容(未発表の名称、収益の実数など)は書かない。

- [献立決定アプリ(仮) 企画・仕様 第3版](planning/meal-decision-app-spec.md)
- [献立決定アプリ(仮) 料理データ リスト設計(150件)](planning/meal-decision-dish-list.md)(元表: `planning/meal-decision-dishes.csv`、検証: `planning/check_dish_coverage.py`、生成: `planning/generate_dish_list.py`)
- [献立決定アプリ(仮) プロトタイプ仕様](planning/meal-decision-prototype-spec.md)
- [献立決定アプリ(仮) Supabase テーブル設計](planning/meal-decision-supabase-schema.md)
