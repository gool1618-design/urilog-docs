---
title: STADIUM プロキシ設計
published: false
---

# STADIUM プロキシ設計

作成日: 2026年9月20日
前提: データ源は TheSportsDB Premium(v1 API、キーは URL に含める)。プロキシは Cloudflare Workers + KV を想定。アプリはプロキシだけを見る。

> 実装は別の非公開リポジトリに置く。この文書は設計だけで、キーや URL は書かない。

---

## 0. 目的

1. TheSportsDB のキーをアプリに埋め込まない。
2. リクエスト上限(Premium は毎分100)を全ユーザーで食い合わない。
3. 対応リーグの追加・変更をアプリの更新なしで行う。
4. 順位表を自前で計算し、API 側の欠落(J1 2026-27)に依存しない。
5. 上流が落ちても、最後に取れたデータを返し続ける。
6. 試合中のスコアを約2分遅れで配る。精度・速さの競争はしない。

---

## 1. 構成

```
iPhone アプリ ──GET──▶ Worker(読み取り API) ──▶ KV(キャッシュ)
                                                  ▲
        Cron Trigger ──▶ Worker(取得ジョブ) ──▶ TheSportsDB v1 ──┘
```

- **読み取り API**: KV から JSON を返すだけ。上流には行かない。
- **取得ジョブ**: Cron で起動し、対応リーグごとに上流を叩いて KV を更新する。順位表もここで計算する。
- **KV**: リーグ・シーズン単位の JSON。1キーあたり最大 25MB なので、1シーズン380試合の JSON(数百KB)は余裕で収まる。
- **設定**: 対応リーグの一覧は KV の `config/competitions` に置き、ダッシュボードから編集する。アプリの更新は不要。

---

## 2. 読み取り API

すべて GET、JSON、UTF-8。日時は ISO 8601 の UTC(`2026-09-20T13:00:00Z`)。`Cache-Control: public, max-age=300` と `ETag` を付け、アプリは `If-None-Match` を送る。

| パス | 内容 | 更新頻度 |
|---|---|---|
| `/v1/meta` | API バージョン、帰属表示の文言、アプリの最低対応バージョン、全体の最終更新時刻 | 随時 |
| `/v1/competitions` | 対応リーグの一覧 | 設定変更時 |
| `/v1/competitions/{id}/teams?season=` | そのシーズンのチーム一覧 | 1日1回 |
| `/v1/competitions/{id}/matches?season=` | そのシーズンの全試合(日程と結果) | 1日1回 + 試合日は1時間おき |
| `/v1/competitions/{id}/standings?season=` | 順位表(自前計算) | matches 更新のたび |
| `/v1/teams/{teamId}/matches?season=` | チーム視点の試合一覧(matches から抽出。アプリの主経路) | 同上 |
| `/v1/live` | 対応リーグで進行中の試合のスコアと経過 | 試合中は2分おき。`max-age=60` |

`id` はプロキシ側の安定した ID(例 `eng-pl`, `esp-ll`, `ger-bl`, `ned-ed`, `jpn-j1`, `jpn-j2`, `jpn-j3`, `sau-pl`)。TheSportsDB の数値 ID は内部にだけ持ち、上流を差し替えても API は変えない。

### レスポンスの形

`/v1/competitions`

```json
{
  "updatedAt": "2026-09-20T03:00:12Z",
  "competitions": [
    {
      "id": "jpn-j1",
      "name": "J1リーグ",
      "nameEn": "J1 League",
      "country": "JP",
      "currentSeason": "2026-2027",
      "seasonStartMonth": 8,
      "tier": 1
    }
  ]
}
```

`/v1/competitions/{id}/teams`

```json
{
  "competitionId": "jpn-j1",
  "season": "2026-2027",
  "updatedAt": "...",
  "teams": [
    { "id": "tsdb-133604", "name": "Kashima Antlers", "nameJa": "鹿島アントラーズ", "shortName": "鹿島",
      "colors": { "primary": "#B8202E", "secondary": "#0A2240" } }
  ]
}
```

- `nameJa`、`shortName`、`colors` はプロキシ側の対訳・色テーブルから付ける(TheSportsDB には日本語名がない)。無ければ省略し、アプリは英語名を出す。
- チーム ID は上流の ID に接頭辞を付ける。上流を替えたときは対応表で引き継ぐ。

`/v1/competitions/{id}/matches`

```json
{
  "competitionId": "jpn-j1",
  "season": "2026-2027",
  "updatedAt": "...",
  "matches": [
    {
      "id": "tsdb-2231455",
      "round": 8,
      "kickoffAt": "2026-09-20T08:00:00Z",
      "kickoffTimeKnown": true,
      "homeTeamId": "tsdb-133604",
      "awayTeamId": "tsdb-133605",
      "homeGoals": null,
      "awayGoals": null,
      "status": "scheduled",
      "venue": "Panasonic Stadium Suita"
    }
  ]
}
```

- `status`: `scheduled` / `finished` / `postponed` / `cancelled` / `unknown`。
- `kickoffTimeKnown`: 上流に時刻が無い(日付だけ)場合は false。アプリは「時刻未定」と出し、通知を登録しない。
- `matches` には試合中の状態を持たない。進行中の試合は `/v1/live` で別に配り、アプリはそちらを優先する。`/v1/live` が取れないときは、キックオフから2時間半を「試合中」として扱う。

`/v1/live`

```json
{
  "fetchedAt": "2026-09-20T13:31:05Z",
  "delayNote": "約2分遅れ",
  "matches": [
    { "id": "tsdb-2231455", "competitionId": "jpn-j1",
      "homeGoals": 1, "awayGoals": 0, "period": "2H", "minute": 67, "status": "inPlay" }
  ]
}
```

- `period`: `1H` / `HT` / `2H` / `ET` / `PEN` / `FT`。`minute` は上流に無ければ null。
- 終了(`FT`)になった試合は、次の結果ジョブで `matches` 側に確定値が入るまで `/v1/live` に残す。

`/v1/competitions/{id}/standings`

```json
{
  "competitionId": "jpn-j1",
  "season": "2026-2027",
  "computedAt": "...",
  "basis": "computed-from-results",
  "rows": [
    { "position": 1, "teamId": "tsdb-133604", "played": 7, "won": 5, "drawn": 1, "lost": 1,
      "goalsFor": 14, "goalsAgainst": 6, "goalDifference": 8, "points": 16 }
  ]
}
```

---

## 3. 取得ジョブ

### スケジュール

| ジョブ | Cron(UTC) | 内容 |
|---|---|---|
| 日程・チーム | 毎日 03:00 | 全対応リーグの `eventsseason` と チーム一覧を取得し、KV を丸ごと置き換える。順位表を再計算 |
| 結果 | 毎時 05分 | 「直近36時間にキックオフがある試合」を持つリーグだけ `eventsseason` を再取得。変化があれば順位表を再計算 |
| ライブ | 2分おき | `matches` のキャッシュに「キックオフから3時間以内の試合」が1つでもあるときだけ上流のライブスコアを取得。対応リーグ分だけ抜き出して `/v1/live` を更新。無いときは何もしない |

- 毎時ジョブが上流を叩くのは試合日のみ。7リーグで週末に集中しても1時間に7回。
- ライブジョブは1回の呼び出しで全試合が返る(リーグ単位ではない)ので、試合がある時間帯に2分おきで1回ずつ。1日中どこかで試合があっても最大720回。
- 1日の上流リクエスト数は最大でも 180 + 720 ≒ 900。Premium の毎分100に対して余裕がある。
- Cloudflare 無料プランの Cron Trigger は 5 本まで。3 本で足りる。
- **KV の書き込みは無料枠が1日1,000回。** ライブジョブは内容が変わったときだけ書き、試合が無い時間帯は動かさないので、週末でも数百回に収まる見込み。超えそうなら `/v1/live` だけ KV ではなく Cache API に置く。

### 上流(TheSportsDB v1)との対応

| 目的 | エンドポイント | 備考 |
|---|---|---|
| シーズン全試合 | `eventsseason.php?id={league}&s={season}` | 検証で 380/306 件が取れた。これを唯一の試合ソースにする |
| チーム一覧 | `search_all_teams.php?l={league name}`、失敗時は全試合の home/away から集める | 有料キーで `lookup_all_teams` が 404 だった |
| リーグ情報 | `lookupleague.php?id=` | `strCurrentSeason` は J1 で「2027」と誤っていたので信用しない。シーズン文字列は設定で持つ |
| ライブスコア | v2 `livescore/soccer`(ヘッダ `X-API-KEY`)。無ければ v1 `latestsoccer.php` | Premium 限定。応答は全リーグの進行中試合なので、`idLeague` で対応リーグ分だけ抜く。実際の遅れは検証スクリプトで確認する |

フィールド対応:

| プロキシ | TheSportsDB |
|---|---|
| `id` | `idEvent` |
| `round` | `intRound`(数値化。無ければ null) |
| `kickoffAt` | `strTimestamp`(UTC)。無ければ `dateEvent` + `strTime`。両方無ければ `dateEvent` の 00:00Z で `kickoffTimeKnown = false` |
| `homeTeamId` / `awayTeamId` | `idHomeTeam` / `idAwayTeam` |
| `homeGoals` / `awayGoals` | `intHomeScore` / `intAwayScore`(空文字は null) |
| `status` | `strPostponed == "yes"` → postponed。`strStatus` に Cancelled → cancelled。スコアが両方入っていて `kickoffAt` が過去 → finished。それ以外 → scheduled |
| `venue` | `strVenue` |

- 上流のフィールド名や意味が変わったときの影響をここで吸収する。アプリ側の形は変えない。

### 順位表の計算

- 対象: `status == finished` の試合のみ。
- 勝ち3点、引き分け1点。
- 並び: 勝点 → 得失点差 → 総得点 → チーム名(英語)の順。リーグ固有の規則(直接対決、勝利数)は v1 では扱わない。順位表は「推しチームの周辺を見る」用途なので、この簡略化で足りる。
- チーム一覧に載っているが試合が無いチームは 0 で行を作る(開幕前)。
- 計算結果に `basis: "computed-from-results"` を付け、上流の順位表を使っていないことをアプリから分かるようにする。

### 差分と保存

- 取得した JSON を正規化し、前回の KV と比較して変化があったときだけ書き込む(KV の無料枠は1日1,000書き込み)。
- `updatedAt` は書き込んだ時刻、`fetchedAt` は上流を叩いた時刻。アプリの「最終更新」は `fetchedAt` を出す。
- 上流がエラーや空応答を返したときは KV を触らない。空のシーズンで上書きしてしまう事故を防ぐため、「前回より試合数が3割以上減った」場合も書き込まず、警告ログを出す。

---

## 4. 設定(KV `config/competitions`)

```json
[
  { "id": "eng-pl", "tsdbLeagueId": 4328, "tsdbLeagueName": "English Premier League",
    "name": "プレミアリーグ", "nameEn": "Premier League", "country": "GB",
    "currentSeason": "2026-2027", "seasonStartMonth": 8, "tier": 1, "enabled": true },
  { "id": "esp-ll", "tsdbLeagueId": 4335, "...": "..." },
  { "id": "ger-bl", "tsdbLeagueId": 4331 },
  { "id": "ned-ed", "tsdbLeagueId": 4337 },
  { "id": "jpn-j1", "tsdbLeagueId": 4633, "currentSeason": "2026-2027" },
  { "id": "jpn-j2", "tsdbLeagueId": 4824 },
  { "id": "jpn-j3", "tsdbLeagueId": 4967 },
  { "id": "sau-pl", "tsdbLeagueId": 4668, "enabled": false }
]
```

- `enabled: false` のリーグは取得もせず、`/v1/competitions` にも出さない。順次追加するときはここを true にするだけ。
- シーズンの切り替え(例: 2027-2028)は `currentSeason` を書き換える。前シーズンの KV は残し、アプリは過去シーズンをそのまま参照できる。
- チームの日本語名・略称・色は別の KV `config/teams` に持つ。無い分は英語名のまま出す。

---

## 5. セキュリティと運用

- TheSportsDB のキーは Worker の Secret に置く。ログに出さない。
- アプリからプロキシへは、固定のアプリトークンをヘッダで送る(秘密ではなく、他者が気軽に叩くのを避けるための識別子)。Cloudflare のレート制限を IP あたり毎分60に設定する。
- 個人情報は扱わない。アクセスログは Cloudflare 標準のもの以外に残さない。プライバシーポリシーには「試合データの取得のために、端末の IP アドレスが当方のサーバーに送信される」旨を書く。
- 障害時: 読み取り API は KV があれば常に返る。取得ジョブの失敗は Worker のログとメール通知で気づけるようにする。
- コスト: Workers 無料枠(1日10万リクエスト)、KV 無料枠(1日10万読み取り、1,000書き込み)、Cron 無料。1日10万リクエストは「1人が1日20回開く」として5,000人分。超えたら Workers 有料(月 $5)。

---

## 6. アプリ側の同期

1. 起動時とフォアグラウンド復帰時、前回同期から15分以上経っていれば `/v1/teams/{teamId}/matches` と `/v1/competitions/{id}/standings` を取得。
2. `ETag` が一致すれば何もしない。
3. 取得した試合を `externalId` で突き合わせ、`manuallyEdited == false` の行だけ更新する。新しい試合は追加、上流から消えた試合は `status = unknown` にして残す(ユーザーの記録が付いている可能性があるため削除しない)。
4. 日程が変わった試合の通知を登録し直す。
5. 手動登録の試合(`source = manual`)には触らない。

---

## 7. 実装前に決めること

- Worker の言語: TypeScript。テストは Vitest。ローカルは `wrangler dev`。
- プロキシのリポジトリ名と、KV の名前空間の命名。
- チームの日本語名・色テーブルの初期データを誰が作るか(7リーグで約140クラブ。初期は J1〜J3 と欧州の主要クラブだけ日本語名を用意し、残りは英語名でよい)。
- TheSportsDB の利用規約の原文確認(キャッシュして配ることの扱い、帰属表示の文言)。
