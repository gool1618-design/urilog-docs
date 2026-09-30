#!/usr/bin/env python3
"""料理データの網羅性チェック。

気分 × 時間 × 除外食材 × 料金区分 のすべての組み合わせで、
候補(1品完結+主菜)が3件以上残るかを確認する。
3件未満のセルは、時間を1段階緩めて解決するかも判定する。

使い方: python3 check_dish_coverage.py [--markdown]
"""
import csv, sys
from collections import Counter

MOODS = [("なんでも", None), ("がっつり", "hearty"), ("さっぱり", "light"),
         ("あたたまる", "warm"), ("麺・丼", "noodle_rice")]
# 時間選択(3段階) → 許容する調理時間の上限。既定値は設定の「標準」(初期値ふつう)。
TIMES = [("すぐ(〜15分)", 15), ("ふつう(〜30分)", 30), ("こだわらない", 999)]
RELAX = {15: 30, 30: 999, 999: 999}
EXCLUDES = [None, "pork", "chicken", "beef", "fish", "shrimp", "egg",
            "milk", "wheat", "soy", "tofu", "mushroom", "buckwheat", "sesame"]
TIERS = [("全件", None), ("無料枠", "free")]
MIN_CANDIDATES = 3

def load(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["moods"] = set(filter(None, r["moods"].split("|")))
        r["tags"] = set(filter(None, r["tags"].split("|")))
        r["time"] = int(r["time"])
    return rows

def candidates(rows, mood, tmax, exclude, tier):
    out = []
    for r in rows:
        if r["form"] not in ("one_dish", "main"):
            continue
        if tier and r["tier"] != tier:
            continue
        if exclude and exclude in r["tags"]:
            continue
        if r["time"] > tmax:
            continue
        if mood and mood not in r["moods"]:
            continue
        if mood == "noodle_rice" and r["form"] != "one_dish":
            continue
        out.append(r)
    return out

def main():
    rows = load(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "meal-decision-dishes.csv")
    md = "--markdown" in sys.argv
    print(f"収録: {len(rows)}件 / 形態: {dict(Counter(r['form'] for r in rows))}")
    print(f"料金区分: {dict(Counter(r['tier'] for r in rows))}")
    print(f"時間分布(1品完結+主菜): {dict(sorted(Counter(r['time'] for r in rows if r['form'] in ('one_dish','main')).items()))}")
    print()

    weak, unresolved = [], []
    for tier_label, tier in TIERS:
        print(f"## {tier_label}: 除外なしのとき、気分×時間で残る件数")
        if md:
            print("| 気分 | " + " | ".join(t for t, _ in TIMES) + " |")
            print("|---|" + "---|" * len(TIMES))
        for mood_label, mood in MOODS:
            cells = []
            for time_label, tmax in TIMES:
                n = len(candidates(rows, mood, tmax, None, tier))
                cells.append(str(n) if n >= MIN_CANDIDATES else f"**{n}**")
            print(("| " + mood_label + " | " + " | ".join(cells) + " |") if md else f"  {mood_label:6s} " + " ".join(f"{c:>6s}" for c in cells))
        print()
        for mood_label, mood in MOODS:
            for time_label, tmax in TIMES:
                for ex in EXCLUDES:
                    n = len(candidates(rows, mood, tmax, ex, tier))
                    if n < MIN_CANDIDATES:
                        n2 = len(candidates(rows, mood, RELAX[tmax], ex, tier))      # 緩和1: 時間を1段階
                        n3 = len(candidates(rows, None, RELAX[tmax], ex, tier))      # 緩和2: 気分も外す
                        entry = (tier_label, mood_label, time_label, ex or "なし", n, n2, n3)
                        (weak if n2 >= MIN_CANDIDATES else unresolved).append(entry)

    print(f"## 3件未満のセル: {len(weak) + len(unresolved)} (時間を1段階緩めて解決: {len(weak)}, 未解決: {len(unresolved)})")
    print()
    print("### 時間を1段階緩めて解決するもの")
    for e in weak:
        print(f"- {e[0]} / {e[1]} / {e[2]} / 除外={e[3]}: {e[4]}件 → 緩和後 {e[5]}件")
    print()
    print("### 時間緩和では足りず、気分も外す2段階目の緩和が必要なもの")
    for e in unresolved:
        mark = "" if e[6] >= MIN_CANDIDATES else "  ← 2段階でも不足。おまかせ直行"
        print(f"- {e[0]} / {e[1]} / {e[2]} / 除外={e[3]}: {e[4]}件 → 時間緩和 {e[5]}件 → 気分も外す {e[6]}件{mark}")

if __name__ == "__main__":
    main()
