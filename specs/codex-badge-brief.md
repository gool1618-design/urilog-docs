---
title: STADIUM 代用エンブレム デザイン依頼(CODEX 向け)
published: false
---

# STADIUM 代用エンブレム デザイン依頼

作成日: 2026年9月22日
宛先: CODEX(デザイン担当)
依頼者: STADIUM 開発者

## 目的

サッカー推し活アプリ「STADIUM」で、クラブの公式エンブレムの**代わり**に使う「代用エンブレム」を、対象の全クラブ分デザインしてほしい。公式エンブレム・選手画像は権利の都合で一切使わない。

サンプル(アーセナル)は添付の画像。この見た目を全クラブに展開する。

## 絶対に守ること(権利)

- 公式エンブレムの形、マスコット、ワードマーク、紋章の要素(大砲、ライオン、船、盾の形など)を**一切使わない**。
- 使ってよいのは「色」と「3文字の略号」と「幾何学的な円と帯」だけ。
- 公式エンブレムと見間違えるほど似せない。色を拾うのは可、形を拾うのは不可。
- 略号は放送で使われる一般的な3文字(ARS、MCI など)。クラブの登録商標そのものは避ける(例: "Spurs" の文字は使わず TOT)。

## 見た目の仕様(サンプルから)

| 要素 | 内容 |
|---|---|
| 形 | 正円。外側から「太い外周リング(サブ色)」「細い内周リング(アクセント色)」「中央の円盤(メイン色)」の3層 |
| 中央の円盤 | メイン色。右側の約1/3を一段暗い同系色で縦に塗り分け、平面的な陰影を付ける(サンプルの右側の暗い帯) |
| 文字 | 3文字の略号を中央に。白(メイン色が明るい場合は黒)、太いサンセリフ、わずかに字間を詰める。円盤の直径の約55%の幅 |
| 比率 | 外周リング 8%、内周リング 2.5%、円盤 残り(直径比) |
| 背景 | 透過 |
| 質感 | 平面。グラデーション、影、光沢、テクスチャは使わない |

## 色のルール

- **メイン色**: そのクラブの公式エンブレムの主要色を拾う(下の表に候補値。エンブレムを見て補正してよい)。
- **サブ色(外周リング)**: エンブレムの2番目の色。無ければメイン色の暗い同系色か、ネイビー。
- **アクセント色(内周リング)**: エンブレムに金や第3色があればそれ。無ければ白かクリーム(#F1E3B3 のような)。
- **同じリーグの中で見分けがつくこと。** 同じメイン色のクラブ同士(例: プレミアの赤系、Jリーグの青系)は、サブ色・アクセント色・暗い帯の色相で差を付ける。並べたときに一目で区別できるかを、リーグごとに全クラブ並べて確認する。
- ダーク背景(#0C1220)の上に置くので、外周リングが背景に溶けないこと。ネイビーの外周を使う場合は内周のアクセントを明るくする。

## 略号のルール

- 3文字の大文字。同じリーグの中で重複しない(下の表は重複が無いように付けてある)。
- Jリーグは J1〜J3 間でクラブが昇降格するので、J の全クラブで重複しないようにしてある。
- 表の略号は変えてよいが、変えたら重複を再確認すること。

## 納品の形

- **1クラブ1ファイル、PNG、1024×1024、背景透過。** 可能なら SVG も。
- ファイル名: `badge-<略号小文字>.png`(例: `badge-ars.png`)。
- あわせて `badges.json` を1つ: `[{"name": "Arsenal", "code": "ARS", "primary": "#EF0107", "secondary": "#0A2240", "accent": "#C9A24C", "file": "badge-ars.png"}, ...]`。`name` は下の表の「TheSportsDB 名」をそのまま使う(アプリはこの名前で照合する)。
- リーグごとに全クラブを並べた一覧画像(確認用)も1枚ずつ。

## 対象クラブの決め方

対象は、プレミアリーグ、ラ・リーガ、ブンデスリーガ、エールディヴィジ、J1、J2、J3 の **2026-27 シーズンの所属クラブ**。下の表は昇降格の候補を含めた広めの一覧なので、実際の所属は次で確認する。

- `~/Downloads/thesportsdb_raw/season_<リーグID>_2026-2027.json` にシーズン全試合が入っている。`strHomeTeam` の一意な値が所属クラブ。リーグ ID: プレミア 4328、ブンデス 4331、J1 4633、J2 4824、J3 4967。
- ラ・リーガ(4335)とエールディヴィジ(4337)はまだ取得できていない。`python3 verify_thesportsdb.py --key <キー> --leagues ラ・リーガ,エールディヴィジ` を実行すると JSON ができる。
- 表に無いクラブが所属していたら追加し、略号と色を新たに決める。

## クラブ一覧(略号と色の候補)

色は開発者側で用意した候補値。公式エンブレムを見て補正してよい。

### プレミアリーグ

| TheSportsDB 名 | 日本語 | 略号 | メイン | サブ |
|---|---|---|---|---|
| Arsenal | アーセナル | ARS | #EF0107 | #FFFFFF |
| Aston Villa | アストン・ヴィラ | AVL | #670E36 | #95BFE5 |
| Bournemouth | ボーンマス | BOU | #DA291C | #000000 |
| Brentford | ブレントフォード | BRE | #E30613 | #FFFFFF |
| Brighton and Hove Albion | ブライトン | BHA | #0057B8 | #FFFFFF |
| Burnley | バーンリー | BUR | #6C1D45 | #99D6EA |
| Chelsea | チェルシー | CHE | #034694 | #FFFFFF |
| Coventry City | コヴェントリー | COV | #4B92DB | #FFFFFF |
| Crystal Palace | クリスタル・パレス | CRY | #1B458F | #C4122E |
| Everton | エヴァートン | EVE | #003399 | #FFFFFF |
| Fulham | フラム | FUL | #FFFFFF | #000000 |
| Hull City | ハル・シティ | HUL | #F5A12D | #000000 |
| Ipswich Town | イプスウィッチ | IPS | #0044A9 | #FFFFFF |
| Leeds United | リーズ | LEE | #FFFFFF | #1D428A |
| Leicester City | レスター | LEI | #003090 | #FDBE11 |
| Liverpool | リヴァプール | LIV | #C8102E | #00B2A9 |
| Luton Town | ルートン | LUT | #F78F1E | #002D62 |
| Manchester City | マンチェスター・シティ | MCI | #6CABDD | #1C2C5B |
| Manchester United | マンチェスター・ユナイテッド | MUN | #DA291C | #FBE122 |
| Middlesbrough | ミドルズブラ | MID | #E11B22 | #FFFFFF |
| Newcastle United | ニューカッスル | NEW | #241F20 | #FFFFFF |
| Norwich City | ノリッジ | NOR | #00A650 | #FFF200 |
| Nottingham Forest | ノッティンガム・フォレスト | NFO | #DD0000 | #FFFFFF |
| Sheffield United | シェフィールド・ユナイテッド | SHU | #EE2737 | #000000 |
| Southampton | サウサンプトン | SOU | #D71920 | #FFFFFF |
| Sunderland | サンダーランド | SUN | #EB172B | #FFFFFF |
| Tottenham Hotspur | トッテナム | TOT | #132257 | #FFFFFF |
| Watford | ワトフォード | WAT | #FBEE23 | #ED2127 |
| West Bromwich Albion | ウェスト・ブロムウィッチ | WBA | #122F67 | #FFFFFF |
| West Ham United | ウェストハム | WHU | #7A263A | #1BB1E7 |
| Wolverhampton Wanderers | ウルヴァーハンプトン | WOL | #FDB913 | #231F20 |

### ラ・リーガ

| TheSportsDB 名 | 日本語 | 略号 | メイン | サブ |
|---|---|---|---|---|
| Alavés | アラベス | ALA | #0761AF | #FFFFFF |
| Almería | アルメリア | ALM | #EE1119 | #FFFFFF |
| Athletic Bilbao | アスレティック・ビルバオ | ATH | #EE2523 | #FFFFFF |
| Atlético Madrid | アトレティコ・マドリード | ATM | #CB3524 | #FFFFFF |
| Barcelona | バルセロナ | BAR | #A50044 | #004D98 |
| Cádiz | カディス | CAD | #FFE500 | #0033A0 |
| Celta Vigo | セルタ | CEL | #8AC3EE | #FFFFFF |
| Deportivo La Coruña | デポルティーボ | DEP | #1E5AA8 | #FFFFFF |
| Elche | エルチェ | ELC | #0A5C2B | #FFFFFF |
| Espanyol | エスパニョール | ESP | #0066B3 | #FFFFFF |
| Getafe | ヘタフェ | GET | #0A4A9F | #FFFFFF |
| Girona | ジローナ | GIR | #CD2534 | #FFFFFF |
| Granada | グラナダ | GRA | #C60D1F | #FFFFFF |
| Las Palmas | ラス・パルマス | LPA | #FFE400 | #0B5FA9 |
| Leganés | レガネス | LEG | #00539F | #FFFFFF |
| Levante | レバンテ | LEV | #B4053B | #0A4A9F |
| Málaga | マラガ | MAL | #0072BC | #FFFFFF |
| Mallorca | マジョルカ | MLL | #E20613 | #000000 |
| Osasuna | オサスナ | OSA | #D91A21 | #0A1F5C |
| Racing de Santander | ラシン・サンタンデール | RAC | #009A44 | #FFFFFF |
| Rayo Vallecano | ラージョ・バジェカーノ | RAY | #FFFFFF | #E53027 |
| Real Betis | ベティス | BET | #00954C | #FFFFFF |
| Real Madrid | レアル・マドリード | RMA | #FFFFFF | #FEBE10 |
| Real Oviedo | オビエド | OVI | #0033A0 | #FFFFFF |
| Real Sociedad | レアル・ソシエダ | RSO | #0067B1 | #FFFFFF |
| Real Valladolid | バジャドリー | VLL | #921B88 | #FFFFFF |
| Real Zaragoza | サラゴサ | ZAR | #FFFFFF | #0C5AA6 |
| Sevilla | セビージャ | SEV | #FFFFFF | #D4021D |
| Sporting Gijón | スポルティング・ヒホン | SPG | #E4001C | #FFFFFF |
| Valencia | バレンシア | VAL | #FFFFFF | #F18E00 |
| Villarreal | ビジャレアル | VIL | #FFE667 | #005187 |

### ブンデスリーガ

| TheSportsDB 名 | 日本語 | 略号 | メイン | サブ |
|---|---|---|---|---|
| Augsburg | アウクスブルク | FCA | #BA3733 | #46714D |
| Bayer Leverkusen | レバークーゼン | B04 | #E32221 | #000000 |
| Bayern Munich | バイエルン・ミュンヘン | FCB | #DC052D | #0066B2 |
| Bochum | ボーフム | BOC | #005CA9 | #FFFFFF |
| Borussia Dortmund | ドルトムント | BVB | #FDE100 | #000000 |
| Borussia Mönchengladbach | ボルシアMG | BMG | #000000 | #1A9F4E |
| Darmstadt | ダルムシュタット | SVD | #004A9B | #FFFFFF |
| Eintracht Frankfurt | フランクフルト | SGE | #E1000F | #000000 |
| Elversberg | エルファースベルク | ELV | #1A3F94 | #FFFFFF |
| Fortuna Düsseldorf | デュッセルドルフ | F95 | #DA251D | #FFFFFF |
| Freiburg | フライブルク | SCF | #000000 | #E30613 |
| Hamburg | ハンブルガーSV | HSV | #0A5AA8 | #FFFFFF |
| Hannover 96 | ハノーファー | H96 | #1A9F4E | #000000 |
| Heidenheim | ハイデンハイム | FCH | #E2001A | #003F8C |
| Hertha Berlin | ヘルタ・ベルリン | BSC | #005CA9 | #FFFFFF |
| Hoffenheim | ホッフェンハイム | TSG | #1C63B7 | #FFFFFF |
| Holstein Kiel | ホルシュタイン・キール | KIE | #0A5AA8 | #E30613 |
| Kaiserslautern | カイザースラウテルン | FCK | #E30613 | #FFFFFF |
| Karlsruher SC | カールスルーエ | KSC | #004A9B | #FFFFFF |
| Köln | ケルン | KOE | #ED1C24 | #FFFFFF |
| Mainz | マインツ | M05 | #C3141E | #FFFFFF |
| Nürnberg | ニュルンベルク | FCN | #AD1F2D | #000000 |
| Paderborn | パーダーボルン | SCP | #0F3F97 | #FFFFFF |
| RB Leipzig | ライプツィヒ | RBL | #DD0741 | #FFFFFF |
| Schalke 04 | シャルケ | S04 | #004D9D | #FFFFFF |
| St. Pauli | ザンクト・パウリ | STP | #5C3A2E | #FFFFFF |
| Stuttgart | シュトゥットガルト | VFB | #FFFFFF | #E32219 |
| Union Berlin | ウニオン・ベルリン | FCU | #EB1923 | #FFFFFF |
| Werder Bremen | ブレーメン | SVW | #1D9053 | #FFFFFF |
| Wolfsburg | ヴォルフスブルク | WOB | #65B32E | #FFFFFF |

### エールディヴィジ

| TheSportsDB 名 | 日本語 | 略号 | メイン | サブ |
|---|---|---|---|---|
| Ajax | アヤックス | AJA | #D2122E | #FFFFFF |
| Almere City | アルメレ・シティ | ALC | #E4002B | #000000 |
| AZ Alkmaar | AZ | AZA | #DD0000 | #FFFFFF |
| Cambuur | カンブール | CAM | #FFD200 | #0033A0 |
| De Graafschap | デ・フラーフスハップ | DGR | #0033A0 | #FFFFFF |
| Excelsior | エクセルシオール | EXC | #000000 | #E4002B |
| FC Emmen | エメン | EMM | #E4002B | #FFFFFF |
| FC Groningen | フローニンゲン | GRO | #00A651 | #FFFFFF |
| FC Twente | トゥエンテ | TWE | #E4002B | #FFFFFF |
| FC Utrecht | ユトレヒト | UTR | #E4002B | #FFFFFF |
| FC Volendam | フォレンダム | VOL | #F58220 | #000000 |
| Feyenoord | フェイエノールト | FEY | #E4002B | #FFFFFF |
| Fortuna Sittard | フォルトゥナ・シッタート | FOR | #FFD200 | #00843D |
| Go Ahead Eagles | ゴー・アヘッド・イーグルス | GAE | #E4002B | #FFD200 |
| Heracles Almelo | ヘラクレス | HER | #000000 | #FFFFFF |
| NAC Breda | NACブレダ | NAC | #FFD200 | #000000 |
| NEC Nijmegen | NEC | NEC | #E4002B | #00843D |
| PEC Zwolle | PECズヴォレ | PEC | #0033A0 | #FFFFFF |
| PSV Eindhoven | PSV | PSV | #ED1C24 | #FFFFFF |
| RKC Waalwijk | RKCヴァールヴァイク | RKC | #FFD200 | #0033A0 |
| SC Heerenveen | ヘーレンフェーン | HEE | #0033A0 | #FFFFFF |
| Sparta Rotterdam | スパルタ・ロッテルダム | SPR | #E4002B | #FFFFFF |
| Telstar | テルスター | TEL | #FFFFFF | #000000 |
| Vitesse | フィテッセ | VIT | #FFD200 | #000000 |
| Willem II | ヴィレムII | WIL | #E4002B | #0033A0 |

### Jリーグ(J1〜J3)

| TheSportsDB 名 | 日本語 | 略号 | メイン | サブ |
|---|---|---|---|---|
| Albirex Niigata | アルビレックス新潟 | NGT | #F39800 | #0068B7 |
| Avispa Fukuoka | アビスパ福岡 | FUK | #003F8C | #A0A0A0 |
| Azul Claro Numazu | アスルクラロ沼津 | NUM | #00A0E9 | #FFFFFF |
| Blaublitz Akita | ブラウブリッツ秋田 | AKT | #0068B7 | #FFFFFF |
| Cerezo Osaka | セレッソ大阪 | COS | #E5007F | #1B1464 |
| Consadole Sapporo | 北海道コンサドーレ札幌 | SAP | #E60012 | #000000 |
| Ehime FC | 愛媛FC | EHM | #F39800 | #FFFFFF |
| Fagiano Okayama | ファジアーノ岡山 | OKA | #B8202E | #FFFFFF |
| FC Gifu | FC岐阜 | GIF | #006934 | #FFFFFF |
| FC Imabari | FC今治 | IMA | #1D2088 | #FFFFFF |
| FC Osaka | FC大阪 | OSK | #004098 | #FFFFFF |
| FC Ryukyu | FC琉球 | RYU | #B5122B | #F7B52C |
| FC Tokyo | FC東京 | FCT | #0066B3 | #E60012 |
| Fujieda MYFC | 藤枝MYFC | FJE | #8B1A8C | #FFFFFF |
| Fukushima United | 福島ユナイテッドFC | FKS | #E60012 | #FFFFFF |
| Gainare Tottori | ガイナーレ鳥取 | TTR | #00A650 | #0068B7 |
| Gamba Osaka | ガンバ大阪 | GOS | #004098 | #000000 |
| Giravanz Kitakyushu | ギラヴァンツ北九州 | KTQ | #FFD800 | #E60012 |
| Iwaki FC | いわきFC | IWK | #E60012 | #0068B7 |
| Iwate Grulla Morioka | いわてグルージャ盛岡 | MOR | #6C1D45 | #FFFFFF |
| JEF United Chiba | ジェフユナイテッド千葉 | CHB | #FFE100 | #00913A |
| Júbilo Iwata | ジュビロ磐田 | IWT | #5AB0E1 | #004098 |
| Kagoshima United | 鹿児島ユナイテッドFC | KGS | #0068B7 | #E60012 |
| Kamatamare Sanuki | カマタマーレ讃岐 | SNK | #00A0E9 | #FFD800 |
| Kashima Antlers | 鹿島アントラーズ | KSM | #B8202E | #0A2240 |
| Kashiwa Reysol | 柏レイソル | KSW | #FFE100 | #000000 |
| Kataller Toyama | カターレ富山 | TYM | #0068B7 | #FFFFFF |
| Kawasaki Frontale | 川崎フロンターレ | KWF | #00A0E9 | #000000 |
| Kochi United | 高知ユナイテッドSC | KOC | #E60012 | #FFFFFF |
| Kyoto Sanga | 京都サンガF.C. | KYT | #7B1D8C | #FFFFFF |
| Machida Zelvia | FC町田ゼルビア | MCD | #004098 | #FFFFFF |
| Matsumoto Yamaga | 松本山雅FC | MTM | #00913A | #FFFFFF |
| Mito HollyHock | 水戸ホーリーホック | MIT | #004098 | #FFFFFF |
| Montedio Yamagata | モンテディオ山形 | YAM | #0068B7 | #FFFFFF |
| Nagano Parceiro | AC長野パルセイロ | NGN | #F39800 | #FFFFFF |
| Nagoya Grampus | 名古屋グランパス | NGY | #E60012 | #FFE100 |
| Nara Club | 奈良クラブ | NAR | #0068B7 | #FFFFFF |
| Oita Trinita | 大分トリニータ | OIT | #0068B7 | #FFE100 |
| RB Omiya Ardija | RB大宮アルディージャ | OMY | #F39800 | #0068B7 |
| Reilac Shiga | レイラック滋賀FC | SHG | #0068B7 | #FFFFFF |
| Renofa Yamaguchi | レノファ山口FC | YGC | #F39800 | #FFFFFF |
| Roasso Kumamoto | ロアッソ熊本 | KUM | #E60012 | #FFFFFF |
| Sagamihara | SC相模原 | SGM | #00913A | #FFFFFF |
| Sagan Tosu | サガン鳥栖 | TOS | #00A0E9 | #E5007F |
| Sanfrecce Hiroshima | サンフレッチェ広島 | HIR | #6A3E9B | #FFFFFF |
| Shimizu S-Pulse | 清水エスパルス | SMZ | #F39800 | #FFFFFF |
| Shonan Bellmare | 湘南ベルマーレ | SHO | #8DC63F | #00A0E9 |
| Tegevajaro Miyazaki | テゲバジャーロ宮崎 | MYZ | #0068B7 | #FFFFFF |
| Thespa Gunma | ザスパ群馬 | GUN | #0068B7 | #FFE100 |
| Tochigi City | 栃木シティ | TCC | #004098 | #FFFFFF |
| Tochigi SC | 栃木SC | TCS | #FFE100 | #0068B7 |
| Tokushima Vortis | 徳島ヴォルティス | TKS | #0068B7 | #FFFFFF |
| Tokyo Verdy | 東京ヴェルディ | TKV | #00913A | #FFFFFF |
| Urawa Red Diamonds | 浦和レッズ | URA | #E60012 | #000000 |
| V-Varen Nagasaki | V・ファーレン長崎 | NGS | #0068B7 | #F39800 |
| Vanraure Hachinohe | ヴァンラーレ八戸 | HAC | #00913A | #FFFFFF |
| Vegalta Sendai | ベガルタ仙台 | SEN | #FFE100 | #004098 |
| Ventforet Kofu | ヴァンフォーレ甲府 | KOF | #004098 | #E60012 |
| Vissel Kobe | ヴィッセル神戸 | KBE | #B5122B | #000000 |
| Yokohama F Marinos | 横浜F・マリノス | YFM | #0068B7 | #E60012 |
| Yokohama FC | 横浜FC | YFC | #00A0E9 | #FFFFFF |
| YSCC Yokohama | Y.S.C.C.横浜 | YSC | #0068B7 | #FFFFFF |
| Zweigen Kanazawa | ツエーゲン金沢 | KNZ | #E60012 | #000000 |
## 確認の観点(納品前)

1. 各リーグの一覧画像で、隣り合うクラブが一目で区別できるか。
2. 公式エンブレムと並べて「形が似ていない」ことを確認したか。
3. ダーク背景で外周リングが見えるか。
4. 略号の重複が無いか(リーグ内、J は全体)。
5. `badges.json` の `name` が表の TheSportsDB 名と一致しているか。
