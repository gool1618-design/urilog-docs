# ピクモグ Supabase テーブル設計(グループ機能)

- 対象: 本体仕様 第3版 §5「ふたり・家族モード」と「週の献立の共有とリクエスト」。1人モードはサーバーを使わないので対象外
- 前提: 契約済みの Supabase。Auth は「Appleでサインイン」。クライアントは iOS アプリのみ
- 方針: **同梱の料理データはDBに置かない。** アプリ同梱のJSON(`dish_id` と `data_version`)を参照するだけ。DBに入るのは「誰が・いつ・どれを選んだか」、共有物、メンバーが登録したマイ料理だけ
- 容量の目安: 1グループ1日あたり 1〜2KB。1,000グループが1年使って 500MB 未満

---

## 1. 全体像

```
auth.users (Appleでサインイン)
   │
   ▼
profiles ──────────────┐
                       │
groups ── group_members(端末あり / 端末なし=代理)
   │        │
   │        └── cook_assignments(その日の作る人)
   │
   ├── daily_sessions(その日の6枚・条件・締め切り・状態)
   │      ├── session_answers(メンバーごとの二択結果)
   │      └── decisions(決まった料理)
   │
   ├── weekly_plans(週の献立)
   │      ├── weekly_plan_days(曜日ごとの料理)
   │      └── change_requests(「変えたい」)
   │
   ├── custom_dishes(メンバーのマイ料理。写真は Storage)
   ├── shopping_items(共有の買い物リスト = 材料名)
   ├── eaten_history(共有の食べた履歴)
   ├── signals(疲れた / 私が作る)
   └── invites(招待リンク)
```

読み書きの原則は「自分が属するグループの行だけ読める。書けるのは自分の行と、作る人だけが書ける行」。すべて Row Level Security(RLS)で守る。

---

## 2. テーブル定義(SQL)

### 2.1 共通

```sql
create extension if not exists pgcrypto;

-- 更新日時を自動で入れる
create or replace function set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
```

### 2.2 profiles(ユーザー)

```sql
create table profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  display_name  text not null default '',            -- アプリ内の表示名。Apple から名前が来ないこともあるので必須にしない
  data_version  int  not null default 1,             -- 端末に入っている料理データの版
  apns_token    text,                                -- プッシュ通知用。端末ごとに上書き(1ユーザー1端末を前提。複数端末は v2)
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create trigger trg_profiles_updated before update on profiles for each row execute function set_updated_at();

-- サインアップ時に自動作成
create or replace function handle_new_user() returns trigger language plpgsql security definer as $$
begin insert into profiles (id) values (new.id); return new; end $$;
create trigger on_auth_user_created after insert on auth.users for each row execute function handle_new_user();
```

- メールアドレスは `auth.users` にしか置かない。アプリのテーブルには持たない(Apple の非公開メールが来るだけで、使い道がない)。

### 2.3 groups / group_members(グループとメンバー)

```sql
create table groups (
  id          uuid primary key default gen_random_uuid(),
  name        text not null default 'うち',
  owner_id    uuid not null references profiles(id),  -- グループを作った人 = Pro を買った人
  deadline_local_time time not null default '18:00',  -- 締め切りの既定値。グループ単位
  timezone    text not null default 'Asia/Tokyo',
  max_members int  not null default 6,
  created_at  timestamptz not null default now()
);

create table group_members (
  id            uuid primary key default gen_random_uuid(),
  group_id      uuid not null references groups(id) on delete cascade,
  user_id       uuid references profiles(id) on delete set null,  -- 端末なしメンバーは null
  display_name  text not null,                                    -- 「パパ」「はるちゃん」
  is_proxy      boolean not null default false,                   -- true = 端末なし(代理回答)
  managed_by    uuid references group_members(id),                -- 代理回答する保護者のメンバーid(is_proxy のとき必須)
  exclude_tags  text[] not null default '{}',                     -- この人の除外食材タグ(egg, pork ...)
  joined_at     timestamptz not null default now(),
  left_at       timestamptz,                                      -- 退出。行は消さず履歴を保つ
  check (not is_proxy or managed_by is not null),
  check (is_proxy or user_id is not null)
);
create unique index uq_group_members_user on group_members(group_id, user_id) where user_id is not null and left_at is null;
create index ix_group_members_group on group_members(group_id);
```

- 1ユーザーが複数グループに入ることは許す(実家と自宅など)。ただし v1.1 の画面は1グループ固定。
- `exclude_tags` はメンバー単位。候補の選定時に全員分を合わせてかける。端末なしの子どもも自分の分を持てる。
- 「作る人」は日ごとに変わるので、メンバーの属性ではなく次のテーブルで持つ。

### 2.4 cook_assignments(その日の作る人)

```sql
create table cook_assignments (
  group_id   uuid not null references groups(id) on delete cascade,
  date       date not null,
  member_id  uuid not null references group_members(id),
  set_by     uuid not null references group_members(id),
  set_at     timestamptz not null default now(),
  primary key (group_id, date)
);
```

- その日の行が無ければ「直近の日の作る人」を引き継ぐ(クライアント側で解決。無ければ owner)。
- 「今日は私が作る」の合図はこの行を upsert する。

### 2.5 daily_sessions / session_answers / decisions(その日の決定)

```sql
create type session_status as enum ('collecting', 'tallied', 'decided', 'cancelled');

create table daily_sessions (
  id             uuid primary key default gen_random_uuid(),
  group_id       uuid not null references groups(id) on delete cascade,
  date           date not null,
  started_by     uuid not null references group_members(id),
  mood           text,                          -- hearty / light / warm / noodle_rice / null(なんでも)
  time_limit     text not null default 'normal',-- quick / normal / any
  deck           text[] not null,               -- その日の6枚の dish_id。全員が同じ6枚を見る
  data_version   int  not null,                 -- deck を選んだ端末の料理データの版
  deadline_at    timestamptz not null,          -- グループの既定時刻からその日の値を計算して保存
  status         session_status not null default 'collecting',
  created_at     timestamptz not null default now(),
  unique (group_id, date)                       -- 1日1セッション。やり直しは cancelled にして新規作成
);

create table session_answers (
  session_id   uuid not null references daily_sessions(id) on delete cascade,
  member_id    uuid not null references group_members(id),
  answered_by  uuid not null references group_members(id),   -- 代理回答なら保護者のメンバーid
  wins         jsonb not null,    -- {"oyakodon": 3, "gyudon": 1, ...}  勝ち数。負けのみは 0
  rejected     text[] not null default '{}',                 -- 「どちらも違う」で外した dish_id
  answered_at  timestamptz not null default now(),
  primary key (session_id, member_id)
);

create table decisions (
  session_id     uuid primary key references daily_sessions(id) on delete cascade,
  dish_id        text not null,
  decided_by     uuid not null references group_members(id),  -- 作る人
  method         text not null,        -- top2_pick / coin_toss / yield / both / omakase / solo
  runner_up      text,                 -- 最終二択のもう一方(歩み寄りの記録用)
  yielded_by     uuid references group_members(id),           -- 「今日は譲る」を押した人
  decided_at     timestamptz not null default now()
);
```

- **集計はサーバー側の関数で行う**(§4)。クライアントが各自計算すると端末間で結果がずれる。
- `deck` に入っている `dish_id` を端末の料理データが知らない場合(版が古い)は、その料理を「アプリを更新すると表示されます」と出す。回答はできる。

### 2.6 weekly_plans / weekly_plan_days / change_requests(週の献立)

```sql
create table weekly_plans (
  id          uuid primary key default gen_random_uuid(),
  group_id    uuid not null references groups(id) on delete cascade,
  week_start  date not null,                 -- 月曜
  created_by  uuid not null references group_members(id),  -- 作る人
  status      text not null default 'active',              -- active / replaced
  created_at  timestamptz not null default now(),
  unique (group_id, week_start, status) deferrable initially deferred
);

create table weekly_plan_days (
  plan_id     uuid not null references weekly_plans(id) on delete cascade,
  date        date not null,
  dish_id     text not null,
  time_limit  text not null default 'normal',   -- その日の時間条件(平日 normal / 土日 any が既定)
  locked      boolean not null default false,   -- 「別の料理に」で入れ替わらないように固定
  updated_at  timestamptz not null default now(),
  primary key (plan_id, date)
);
create trigger trg_plan_days_updated before update on weekly_plan_days for each row execute function set_updated_at();

create type request_status as enum ('open', 'accepted', 'declined');

create table change_requests (
  id             uuid primary key default gen_random_uuid(),
  plan_id        uuid not null references weekly_plans(id) on delete cascade,
  date           date not null,
  requested_by   uuid not null references group_members(id),   -- 端末なしの子なら保護者が代理で
  reason         text not null,            -- recent / not_in_mood / want_this
  proposed_dish  text,                     -- reason = want_this のとき。3候補から選んだ dish_id
  status         request_status not null default 'open',
  resolved_by    uuid references group_members(id),
  resolved_at    timestamptz,
  created_at     timestamptz not null default now()
);
create index ix_change_requests_plan on change_requests(plan_id, status);
```

- 「1人あたり週2回まで」は RLS ではなく挿入前の関数で数える(§4)。
- 当日、週の献立の料理を「これでいく」にした場合も `daily_sessions` + `decisions`(method = 'plan')を作る。履歴と買い物リストの扱いを一本にするため。

### 2.7 shopping_items(共有の買い物リスト)

```sql
create table shopping_items (
  id          uuid primary key default gen_random_uuid(),
  group_id    uuid not null references groups(id) on delete cascade,
  name        text not null,                 -- 材料名(「鶏もも肉」)。分量は持たない
  source_dish text,                          -- どの料理から入ったか。手動追加は null
  source_date date,                          -- どの日の献立から
  checked     boolean not null default false,
  checked_by  uuid references group_members(id),
  added_by    uuid not null references group_members(id),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index ix_shopping_group on shopping_items(group_id, checked);
create trigger trg_shopping_updated before update on shopping_items for each row execute function set_updated_at();
```

- 同じ材料名が複数の料理から入ったら、クライアント側で1行にまとめて表示する(DBは料理ごとに持つ。献立を変えたときにその料理の分だけ消せるように)。
- チェック済みは7日後に削除(pg_cron)。

### 2.8 eaten_history(共有の食べた履歴)

```sql
create table eaten_history (
  id         uuid primary key default gen_random_uuid(),
  group_id   uuid not null references groups(id) on delete cascade,
  date       date not null,
  dish_id    text not null,
  marked_by  uuid not null references group_members(id),
  photo_path text,                                   -- Storage のパス。任意
  created_at timestamptz not null default now(),
  unique (group_id, date, dish_id)
);
create index ix_eaten_group_date on eaten_history(group_id, date desc);
```

- 重複回避(直近7日・14日)はこの表をクライアントが読んで計算する。
- 写真は Supabase Storage のグループ専用バケットに置く。v1.1 では端末内のみでよく、共有は v1.2 で判断。

### 2.9 signals(合図)

```sql
create table signals (
  id         uuid primary key default gen_random_uuid(),
  group_id   uuid not null references groups(id) on delete cascade,
  date       date not null,
  member_id  uuid not null references group_members(id),
  kind       text not null,           -- tired / i_cook
  created_at timestamptz not null default now(),
  unique (group_id, date, member_id, kind)
);
```

- `tired` を作る人が出したら、その日の候補選定を「すぐ・1品完結・手間1」に固定する(クライアントが読んで反映)。
- `i_cook` は `cook_assignments` の upsert と同時に入れる。通知の元になる。

### 2.10 custom_dishes(マイ料理の共有)

```sql
create table custom_dishes (
  id           text primary key,                 -- 'my_' + uuid。端末で採番し、同梱料理の id と衝突しない
  group_id     uuid not null references groups(id) on delete cascade,
  owner        uuid not null references group_members(id),
  name         text not null,
  form         text not null default 'main',     -- main / one_dish
  cook_time    int  not null default 20,
  mood_tags    text[] not null default '{}',
  exclude_tags text[] not null default '{}',
  ingredients  text[] not null default '{}',     -- 名前のみ
  photo_path   text,                             -- Storage: custom-dishes/<group_id>/<id>.jpg
  created_at   timestamptz not null default now(),
  deleted_at   timestamptz
);
create index ix_custom_dishes_group on custom_dishes(group_id) where deleted_at is null;
```

- 1人モードのマイ料理は端末内だけ。グループに入ったとき、本人が「家族にも出す」を選んだ料理だけをここに置く。
- 他のメンバーの端末は、起動時と Realtime でこの表を読み、同梱の料理データに合成して候補に出す。`daily_sessions.deck` に `my_...` の id が入っていても、この表から名前と写真を引けるので表示できる。
- 写真は長辺640pxのJPEG(100KB前後)。Storage のバケットはグループ単位のフォルダにし、RLS と同じ条件で読める。
- 削除は `deleted_at` を立てるだけ。過去の decisions / eaten_history から名前を引けるようにする。

### 2.11 invites(招待)

```sql
create table invites (
  code        text primary key,          -- 8文字。リンクに埋め込む
  group_id    uuid not null references groups(id) on delete cascade,
  created_by  uuid not null references group_members(id),
  expires_at  timestamptz not null default now() + interval '7 days',
  used_by     uuid references profiles(id),
  used_at     timestamptz
);
```

- 招待の受け入れはサーバー関数 `accept_invite(code)` で行う(§4)。クライアントに `groups` への直接 insert 権限を与えない。

---

## 3. Row Level Security

すべてのテーブルで `enable row level security` する。判定の中心は「自分がそのグループの現メンバーか」。

```sql
-- 自分が属するグループ(退出していないもの)
create or replace function my_group_ids() returns setof uuid language sql stable security definer as $$
  select group_id from group_members where user_id = auth.uid() and left_at is null
$$;

-- 自分のメンバーid(そのグループでの)
create or replace function my_member_id(g uuid) returns uuid language sql stable security definer as $$
  select id from group_members where group_id = g and user_id = auth.uid() and left_at is null limit 1
$$;

-- その日の作る人か
create or replace function is_cook(g uuid, d date) returns boolean language sql stable security definer as $$
  select coalesce(
    (select member_id = my_member_id(g) from cook_assignments where group_id = g and date <= d order by date desc limit 1),
    (select owner_id = auth.uid() from groups where id = g)
  )
$$;
```

| テーブル | select | insert | update | delete |
| --- | --- | --- | --- | --- |
| profiles | 自分の行 + 同じグループの人の `display_name` (view 経由) | トリガーのみ | 自分の行 | なし |
| groups | `id in my_group_ids()` | 関数 `create_group` のみ | owner のみ(name, deadline) | owner のみ |
| group_members | 同じグループ | 関数 `accept_invite` / `add_proxy_member` のみ | 自分の行(display_name, exclude_tags)。代理メンバーは managed_by 本人 | なし(left_at を立てる) |
| cook_assignments | 同じグループ | 同じグループのメンバー | 同じグループのメンバー | なし |
| daily_sessions | 同じグループ | 同じグループのメンバー | 作る人(status) | なし |
| session_answers | **集計前は自分の行だけ**、tallied 以降は同じグループ | 自分の行、または managed_by の代理メンバーの行 | 集計前の自分の行 | なし |
| decisions | 同じグループ | 作る人 | 作る人 | なし |
| weekly_plans / weekly_plan_days | 同じグループ | 作る人 | 作る人 | 作る人 |
| change_requests | 同じグループ | 同じグループのメンバー(週2回の上限は関数で) | 作る人(status) | 出した本人(open のみ) |
| shopping_items | 同じグループ | 同じグループ | 同じグループ | 同じグループ |
| eaten_history | 同じグループ | 同じグループ | なし | marked_by 本人 |
| signals | 同じグループ | 自分の行 | なし | 自分の行 |
| custom_dishes | 同じグループ | 同じグループ(owner = 自分) | owner 本人 | owner 本人(deleted_at) |
| invites | 同じグループ | 作成は関数のみ | なし | created_by 本人 |

代表的なポリシーの書き方:

```sql
alter table daily_sessions enable row level security;

create policy "members read sessions" on daily_sessions
  for select using (group_id in (select my_group_ids()));

create policy "members start session" on daily_sessions
  for insert with check (group_id in (select my_group_ids()) and started_by = my_member_id(group_id));

create policy "cook updates session" on daily_sessions
  for update using (is_cook(group_id, date));

alter table session_answers enable row level security;

-- 他人の回答は集計が終わるまで見えない(先に見ると引っ張られるため)
create policy "read own or tallied answers" on session_answers
  for select using (
    exists (select 1 from daily_sessions s where s.id = session_id and s.group_id in (select my_group_ids()))
    and (
      member_id = (select my_member_id(s.group_id) from daily_sessions s where s.id = session_id)
      or exists (select 1 from daily_sessions s where s.id = session_id and s.status <> 'collecting')
    )
  );

create policy "answer for self or proxy" on session_answers
  for insert with check (
    exists (
      select 1 from daily_sessions s
      join group_members m on m.group_id = s.group_id
      where s.id = session_id and s.status = 'collecting' and m.id = member_id and m.left_at is null
        and (m.user_id = auth.uid() or m.managed_by = my_member_id(s.group_id))
    )
    and answered_by = (select my_member_id(s.group_id) from daily_sessions s where s.id = session_id)
  );
```

---

## 4. サーバー側の関数(RPC)

クライアントから `supabase.rpc()` で呼ぶ。複数テーブルにまたがる書き込みと、ルールの強制はここに寄せる。

| 関数 | 役割 |
| --- | --- |
| `create_group(name)` | groups を作り、呼び出し者を owner かつ最初のメンバーにする。Pro の購入確認は App Store のレシート検証を Edge Function で行い、その結果を `profiles.is_pro` に持たせて確認する(v1.1 で追加する列) |
| `create_invite(group_id)` | 8文字のコードを作る。メンバー数が `max_members` 未満のときだけ |
| `accept_invite(code)` | 期限内・未使用なら呼び出し者を group_members に追加し、`used_by` を埋める |
| `add_proxy_member(group_id, display_name, exclude_tags)` | 端末なしメンバーを追加。`managed_by` は呼び出し者 |
| `tally_session(session_id)` | 下記。全員回答時と締め切り時に呼ばれる |
| `create_change_request(plan_id, date, reason, proposed_dish)` | 「1人あたり週2回まで」を数えてから insert |
| `replace_plan_day(plan_id, date, dish_id)` | 作る人が日を差し替え、その日に由来する shopping_items を差し替える |

### 集計 `tally_session`

```sql
create or replace function tally_session(p_session uuid)
returns table (dish_id text, score int) language plpgsql security definer as $$
begin
  -- 勝ち数の合計 − 拒否×2。回答者が1人でも動く
  return query
  with w as (
    select (kv).key as dish_id, sum((kv).value::int) as pts
    from session_answers a, jsonb_each_text(a.wins) kv
    where a.session_id = p_session group by 1
  ), r as (
    select unnest(rejected) as dish_id, count(*) * 2 as penalty
    from session_answers where session_id = p_session group by 1
  )
  select coalesce(w.dish_id, r.dish_id), coalesce(w.pts,0)::int - coalesce(r.penalty,0)::int
  from w full outer join r on w.dish_id = r.dish_id
  order by 2 desc, 1;

  update daily_sessions set status = 'tallied' where id = p_session and status = 'collecting';
end $$;
```

- 二人のときの「一致した料理を優先」は、集計結果の中で「全回答者の wins に含まれる料理」を上位2品に押し上げる処理をクライアントの表示側で行う(得点は同じ関数)。
- 作る人は上位2品を見て `decisions` を書く。同点で決められないときの「コイントス」も `method` に記録する。

### 締め切りの自動集計

```sql
select cron.schedule('tally-deadlines', '*/5 * * * *', $$
  select tally_session(id) from daily_sessions
  where status = 'collecting' and deadline_at <= now()
$$);
```

- 5分おきに締め切りを過ぎたセッションを集計する。集計後、作る人に「決めてください」の通知(§5)。
- 全員が答えた時点での即時集計は、`session_answers` の insert トリガーで人数を数えて `tally_session` を呼ぶ。

---

## 5. 通知(Edge Function)

Postgres の変更を Database Webhook で Edge Function に流し、Edge Function が APNs(Apple のプッシュ通知)に投げる。Supabase の枠内で完結する。

| きっかけ | 宛先 | 文面の例 |
| --- | --- | --- |
| daily_sessions insert | 開始者以外のメンバー(端末あり) | 「〇〇さんが今日の候補を選びました」 |
| status → tallied | 作る人 | 「みんなの回答が揃いました。決めてください」 |
| decisions insert | 作る人以外 | 「今日は 生姜焼き に決まりました」 |
| change_requests insert | 作る人 | 「〇〇さんが木曜を変えたいそうです」 |
| change_requests update(status) | 出した人 | 「木曜が 麻婆豆腐 に変わりました」/「木曜はそのままになりました」 |
| signals insert(tired) | 作る人以外 | 「〇〇さんが今日は疲れているそうです」 |
| cook_assignments upsert | 新しい作る人以外 | 「今日は〇〇さんが作ります」 |

- APNs のトークンは `profiles.apns_token`。Edge Function は APNs の認証キー(.p8)を Supabase の secrets に置いて使う。
- 通知は1日あたり多くても5〜6通。まとめや抑制は v1.2 で考える。

---

## 6. Realtime(画面の即時反映)

アプリを開いている間は Realtime でグループの変更を購読する。閉じているときはプッシュ通知だけ。

| 購読するテーブル | 反映する画面 |
| --- | --- |
| daily_sessions, session_answers(自分の行と tallied 以降), decisions | ホームの「〇〇さんの回答待ち」→「今日はこれ」 |
| weekly_plan_days, change_requests | 今週の献立 |
| shopping_items | 買い物リストのチェック |
| signals, cook_assignments | ホームの状況表示 |

- Realtime は RLS を尊重するので、購読しても他人の集計前の回答は届かない。

---

## 7. データ保持と削除

| データ | 保持 |
| --- | --- |
| session_answers | 集計後90日で削除(pg_cron)。集計結果は decisions に残る |
| shopping_items(checked) | 7日で削除 |
| signals | 30日で削除 |
| invites | 期限切れ後に削除 |
| decisions, eaten_history, weekly_plans | グループが存在する限り保持(履歴と重複回避に使う) |
| グループの削除 | owner が削除すると cascade で全部消える。メンバーの退出は `left_at` を立てるだけ |
| アカウントの削除 | `auth.users` の削除で profiles が消え、group_members.user_id は null になる(そのグループの履歴は残る)。App Store の「アカウント削除」要件に対応 |

---

## 8. クライアント側の責務との切り分け

| 処理 | どこで |
| --- | --- |
| 候補6枚の選定(フィルタ・スコア・多様性) | クライアント。料理データは端末にしかない。全員分の `exclude_tags` と共有の `eaten_history` を読んで計算 |
| 週の献立の生成 | クライアント(作る人の端末)。結果だけ weekly_plan_days に書く |
| 得点の集計 | サーバー(`tally_session`)。端末間で結果を揃えるため |
| 一致した料理の優先(二人) | クライアントの表示 |
| 「変えたい」の3候補生成 | クライアント(出す人の端末)。選んだ1つだけ `proposed_dish` に書く |
| 通知 | サーバー(Edge Function) |
| 締め切り | サーバー(pg_cron) |

料理データがサーバーに無いことで、選定ロジックはすべて端末側になる。データの版がメンバー間でずれても、deck は `dish_id` の配列なので古い端末は「更新すると表示されます」と出して回答を続けられる。

---

## 9. 実装順(v1.1)

1. Apple でサインイン、profiles、groups、group_members、invites と RPC(`create_group`、`create_invite`、`accept_invite`)
2. daily_sessions、session_answers、decisions、`tally_session`、RLS
3. Realtime 購読とホームの状況表示
4. shopping_items、eaten_history、signals、cook_assignments
5. Edge Function と APNs
6. weekly_plans、weekly_plan_days、change_requests(v1.1 後半)
7. add_proxy_member と代理回答(v1.2)
