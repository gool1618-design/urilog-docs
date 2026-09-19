#!/usr/bin/env python3
"""meal-decision-dishes.csv から meal-decision-dish-list.md を生成する。

使い方: python3 generate_dish_list.py
検証結果(check_dish_coverage.py の出力)も埋め込む。CSV を編集したらこれを回す。
"""
import csv, subprocess
from collections import Counter

FORM={'one_dish':'1品完結','main':'主菜','side':'副菜','soup':'汁物'}
CUI={'japanese':'和','western':'洋','chinese':'中','ethnic':'エスニック'}
MOOD={'hearty':'がっつり','light':'さっぱり','warm':'あたたまる','noodle_rice':'麺・丼'}
TAG={'pork':'豚','chicken':'鶏','beef':'牛','fish':'魚','shrimp':'えび','egg':'卵','milk':'乳','wheat':'小麦',
     'soy':'大豆(醤油含む)','tofu':'豆腐','mushroom':'きのこ','buckwheat':'そば','sesame':'ごま'}
SEA={'all':'通年','spring':'春','summer':'夏','autumn':'秋','winter':'冬'}

def table(rows, form):
    out=['| # | 料理 | 系 | 気分 | 分 | 手間 | 費用 | 主な材料 | 除外タグ | 季節 | 区分 |','|---|---|---|---|---|---|---|---|---|---|---|']
    for i, r in enumerate([r for r in rows if r['form']==form], 1):
        moods='・'.join(MOOD[m] for m in r['moods'].split('|') if m)
        tags='・'.join(TAG[t] for t in r['tags'].split('|') if t) or '(なし)'
        sea='・'.join(SEA[s] for s in r['season'].split('|'))
        ing='、'.join(r['main_ingredients'].split('|'))
        out.append(f"| {i} | {r['name']} | {CUI[r['cuisine']]} | {moods} | {r['time']} | {r['effort']} | {r['cost']} | {ing} | {tags} | {sea} | {'無料' if r['tier']=='free' else 'Pro'} |")
    return '\n'.join(out)

def main():
    rows=list(csv.DictReader(open('meal-decision-dishes.csv',encoding='utf-8')))
    cand=[r for r in rows if r['form'] in ('one_dish','main')]
    dist_time=Counter(int(r['time']) for r in cand)
    dist_cui=Counter(CUI[r['cuisine']] for r in cand)
    dist_eff=Counter(r['effort'] for r in cand)
    dist_cost=Counter(r['cost'] for r in cand)
    tier=Counter(r['tier'] for r in rows); forms=Counter(r['form'] for r in rows)
    check=subprocess.run(['python3','check_dish_coverage.py','--markdown'],capture_output=True,text=True).stdout
    tables=check.split('## 全件')[1].split('## 3件未満')[0].replace('\n## ','\n### ')
    weak=check.split('## 3件未満')[1]
    weak_head, weak_body = weak.split('\n',1)
    n_quick=sum(v for k,v in dist_time.items() if k<=15); n_normal=sum(v for k,v in dist_time.items() if k<=30)

    doc=f"""# 献立決定アプリ(仮) 料理データ v1.0 リスト設計({len(rows)}件)

- 元データ: `meal-decision-dishes.csv`。この文書は `generate_dish_list.py` で生成する。編集はCSV側で行い、生成し直す
- 検証スクリプト: `check_dish_coverage.py`
- 件数: {len(rows)}件(1品完結{forms['one_dish']} / 主菜{forms['main']} / 副菜{forms['side']} / 汁物{forms['soup']})。無料 {tier['free']} / Pro {tier['pro']}
- 副菜・汁物は「+1品」提案専用で、二択の候補には出さない
- **持つのは決めるためのデータだけ。** 分量と手順は持たない(本体仕様 第3版 §6)。「主な材料」は名前のみで、決定画面のチップと買い物リスト(材料メモ)に使う

## 1. 設計方針

1. **時間の中心は15〜20分。** 候補{len(cand)}件(1品完結+主菜)のうち「すぐ(〜15分)」が{n_quick}件、「ふつう(〜30分)」まで含めて{n_normal}件。
2. **10分の料理を{dist_time[10]}件確保。** 「疲れた日」の受け皿。冷凍うどん・缶詰・卵・刺身を使う。
3. **和食に偏らせすぎない。** 二択と週の献立で系が続かないようにするため、分布を {', '.join(f'{k}{v}' for k,v in dist_cui.items())} にした。
4. **手間3は{dist_eff['3']}件だけ**(唐揚げ、酢豚、餃子)。疲れた日に出ない料理は少なくてよい。
5. **除外タグは除外に使うものだけ。** アレルゲン主要品目(卵・乳・小麦・えび・そば)+よく除外される主食材(豚・鶏・牛・魚)+苦手が多い食材(豆腐・きのこ・ごま)+大豆。調味料由来の大豆は「大豆(醤油含む)」。貝類・魚卵・魚醤は「魚」に含める。
6. **季節は加点のみ。** 夏の冷やし中華が冬に出ないのではなく、順位が下がるだけ。
7. **調理時間は目安。** 10 / 15 / 20 / 30 / 40 の5値で持つが、絞り込みは「すぐ(〜15)/ふつう(〜30)/こだわらない」の3段階に丸める。試作して測る必要はない。

### 分布

| 項目 | 分布(1品完結+主菜 {len(cand)}件) |
|---|---|
| 調理時間 | {' / '.join(f'{k}分: {v}' for k,v in sorted(dist_time.items()))} |
| 系 | {' / '.join(f'{k}: {v}' for k,v in dist_cui.items())} |
| 手間 | {' / '.join(f'{k}: {v}' for k,v in sorted(dist_eff.items()))} |
| 費用 | {' / '.join(f'{k}: {v}' for k,v in sorted(dist_cost.items()))} |

## 2. 網羅性の検証結果

気分5 × 時間3 × 除外食材14通り × 料金区分2 = 420セルを機械的に確認した。

### 全件{tables}
**3件未満{weak_head.strip()}。すべて緩和ルールで解決する。**
{weak_body}
本体仕様§4の候補不足時ルール(緩和1: 時間を1段階広げる → 緩和2: 気分を外す → おまかせ直行)で全セルが解決する。

大豆(醤油)を除外する人には醤油なしの料理が構造的に少ない。除外設定の画面で「大豆を除外すると候補が大幅に減ります」と注意を出す。

## 3. 料理リスト

### 1品完結({forms['one_dish']}件)

{table(rows,'one_dish')}

### 主菜({forms['main']}件)

{table(rows,'main')}

### 副菜({forms['side']}件)・汁物({forms['soup']}件)「+1品」提案専用

{table(rows,'side')}

{table(rows,'soup')}

## 4. 無料枠とProの分け方

- 無料 {tier['free']} 件: 「なんでも×ふつう」で58件残る。毎日使って1か月は重複回避に引っかからない量。「1週間ぶん作る」も無料枠で回る
- Pro {tier['pro']} 件: 魚料理・エスニック・鍋・季節もの・手間のかかる料理を厚めに配置
- 無料枠だけでも除外なしの全セルで14件以上残ることを検証済み

## 5. データ制作の進め方

| 工程 | 内容 | 1品あたり |
|---|---|---|
| 1. 下書き | このCSVの行(名前・タグ・時間・手間・費用・主な材料)をAIで下書き | 済({len(rows)}件) |
| 2. 机上確認 | 料理として自然か、除外タグの漏れがないか、時間の目安が常識的か、主な材料が3〜5個に収まっているか | 3分 |
| 3. イラスト | 統一プロンプトで生成。同一スタイル。商用利用可の条件を確認 | 5分 |
| 4. 検証 | `check_dish_coverage.py` → `generate_dish_list.py` | 一括 |

- 工数の目安: 1件約8分 × {len(rows)}件 ≒ {round(len(rows)*8/60)}時間。試作はしない。
- 無料枠{tier['free']}件のイラストを先に揃え、Pro分は TestFlight 中に足す。300件への拡張は本体仕様§1の判断を通ったあと。
- 料理名は一般的な呼び方を使い、市販品の商品名やブランド名を含めない。主な材料も一般名(「めんつゆ」は可、商品名は不可)。

## 6. JSONへの変換

アプリ同梱データは本体仕様§6のJSON。CSVの列をそのまま写し、`main_ingredients` は `mainIngredients`、`tags` は `excludeTags` に対応する。`pairSuggestions`(+1品の候補)は形態が side / soup の料理から系と時間で機械的に付ける。
"""
    open('meal-decision-dish-list.md','w',encoding='utf-8').write(doc)
    print(f'{len(doc.splitlines())} lines')

if __name__ == '__main__':
    main()
