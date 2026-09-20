# ピクモグ 実装計画 v1.0

- リポジトリ: `gool1618-design/pikumogu`(**非公開**。作成待ち)。公開文書はこの `urilog-docs` に置く
- 構成: バイヤーノート(UriLog)と同じ。XcodeGen の `project.yml`、SwiftUI、iOS 17、SwiftData、Supabase Swift(v1.1 から)。日本語コメント、`HANDOFF.md` で引き継ぎ
- Bundle ID: `com.ryuya0816.Pikumogu`。表示名「ピクモグ」
- 開発環境: Xcode でビルドする。Claude のクラウド環境では Swift のコンパイルができないため、コードは Xcode 側でビルドして確認する

## 1. v1.0 の範囲(仕様 第3版 §9)

| 画面 / 機能 | 実装 |
| --- | --- |
| ホーム | 今日の予定 or 決まった料理、「今日の献立を決める」「疲れた日」「1週間ぶん作る」 |
| 気分・時間 | チップ2組、省略可 |
| 10件グリッド | 2列×5行、いまの候補の固定、最大3回、どれも違う、緩和表示 |
| 決定 | 料理、好み、主な材料チップ、これにする / 別の候補 / おまかせ |
| おまかせ | 上位6件のルーレット |
| 決まった | 材料メモ→買い物、+1品、自分のレシピメモ、レシピを見る(検索先設定)、食べた |
| 1週間ぶん作る | 7日、週の制約、別の料理に、当日の予定 |
| 買い物リスト | 材料名、料理別、チェック |
| 履歴 | 食べた日付順、好きな料理 |
| マイ料理 | 写真・料理名・時間・形・気分・材料。無料10件 |
| 料理の好み | 一覧、好き/ふつう/苦手/出さない |
| 設定 | 標準の時間、苦手食材、予算、検索先、Pro |
| 課金 | StoreKit 2、非消耗型 `com.ryuya0816.Pikumogu.pro`、500円 |
| 計測 | 端末内のみ(v1.0 は送信しない) |

グループ機能(v1.1)は入れない。ただしデータモデルは `dish_id` 参照にして、あとから Supabase を足せる形にする。

## 2. ファイル構成

```
pikumogu/
  project.yml
  HANDOFF.md
  Pikumogu/
    PikumoguApp.swift          エントリ。SwiftData コンテナ
    ContentView.swift          タブ(決める / 買い物 / 履歴 / 設定)と決定フローのフルスクリーン
    Theme/AppTheme.swift       色・角丸・フォント
    Data/
      Dishes.json              同梱の料理150件(planning/meal-decision-dishes.csv から生成)
      Dish.swift               同梱料理の構造体(Codable)。マイ料理も同じ型に変換して扱う
      DishCatalog.swift        JSON 読み込み、id 検索、マイ料理との合成
    Models/                    SwiftData @Model(CloudKit 同期に備えて全プロパティに既定値)
      EatenRecord.swift        食べた {dishId, date}
      SoftNoRecord.swift       今日は違う {dishId, date}
      DishPreference.swift     好み {dishId, level: like/dislike/hidden}
      CustomDish.swift         マイ料理
      ShoppingItem.swift       買い物 {name, dishId, checked}
      RecipeMemo.swift         自分のレシピメモ {dishId, memo, url}
      WeeklyPlan.swift         週の献立 {weekStart, days:[{date, dishId, locked}]}
      DecisionLog.swift        自己テスト用の計測 {startedAt, decidedAt, taps, method, satisfied}
    Engine/
      Conditions.swift         Mood / TimeLimit / 設定値
      CandidateEngine.swift    フィルタ・スコア・緩和・多様性(仕様§4)。純粋関数、テスト可能
      PickSession.swift        グリッドの状態機械(round, champ, passed, shown, redraws)
      WeeklyPlanner.swift      週の制約付き生成
      PlusOneSuggester.swift   +1品
    Views/
      HomeView.swift
      MoodView.swift
      PickGridView.swift
      DecidedView.swift
      OmakaseView.swift
      DoneView.swift
      WeekView.swift
      ShoppingView.swift
      HistoryView.swift
      SettingsView.swift
      MyDishesView.swift / MyDishEditView.swift
      PreferencesView.swift
      Components/DishCard.swift, Chips.swift, DishArt.swift(イラスト or 写真 or 絵文字)
    Store/
      UserSettings.swift       @AppStorage(標準の時間、除外食材、検索先、Pro)
      ProStore.swift           StoreKit 2
    Assets.xcassets            AppIcon、AccentColor、料理イラスト(dish_<id>)
  PikumoguTests/
    CandidateEngineTests.swift  スコア・緩和・多様性の単体テスト
    WeeklyPlannerTests.swift
```

## 3. 実装順(マイルストーン)

| # | 内容 | 確認 |
| --- | --- | --- |
| M1 | project.yml、App、Dish/DishCatalog、Dishes.json、CandidateEngine + テスト | `xcodegen` → ビルド → テストが通る |
| M2 | ホーム → 気分 → グリッド → 決定 → 決まった(材料メモ、レシピを見る、食べた)。イラストは絵文字で代用 | 実機で30秒・3タップを自分で確認 |
| M3 | おまかせ、疲れた日、別の候補、緩和、好み(決まった画面)、履歴 | |
| M4 | 買い物リスト、+1品、レシピメモ、検索先、設定(除外食材・標準の時間) | |
| M5 | 1週間ぶん作る、当日の予定 | |
| M6 | マイ料理(写真は PhotosPicker、640px に縮小)、料理の好み一覧、無料上限 | |
| M7 | StoreKit 2(Pro)、計測ログ、オンボーディング1画面 | TestFlight |
| M8 | イラスト150枚を差し替え、App Store メタデータ、プライバシーポリシー(urilog-docs に追加) | 審査提出 |

M1〜M2 を先に通して1週間の自己テスト(プロトタイプ仕様§5)を挟む。M3 以降は自己テストの結果を見て順番を入れ替えてよい。

## 4. 設計上の決めごと

- 同梱料理は `Dish`(struct, Codable)。マイ料理は SwiftData の `CustomDish` だが、候補選定では `Dish` に変換して同じ配列に混ぜる。エンジンは SwiftData を知らない
- 学習データ(食べた・今日は違う・好み)は `dishId: String` で持つ。同梱料理もマイ料理も同じ id 空間(マイ料理は `my_` 接頭辞)
- CloudKit 同期は v1.0 では無効。ただし @Model の全プロパティに既定値を付けておく(UriLog と同じ理由)
- スコアの乱数は `SystemRandomNumberGenerator` だが、テストでは差し替えられるようエンジンに注入する
- 画像は `Assets.xcassets` の `dish_<id>`。無ければ絵文字にフォールバック(`DishArt`)
- 「レシピを見る」は `UIApplication.shared.open` で検索 URL を開くだけ。外部コンテンツを取り込まない
- 計測は `DecisionLog` に端末内保存。設定画面に中央値と納得率を出す。送信は v1.1 以降で同意を取ってから

## 5. 名前の確認(提出前に)

バイヤーノートで同名アプリが先に出ていた経験があるので、提出前に次を確認する。

- App Store で「ピクモグ」「ぴくもぐ」「pikumogu」を検索し、同名・類似名がないこと
- J-PlatPat で商標(称呼「ピクモグ」)を検索。空いていれば出願を検討
- SNS のアカウント名とドメインの空き
