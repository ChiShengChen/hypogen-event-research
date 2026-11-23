"""Post-hoc serialization sensitivity. Never alters sealed scoring or receipts."""

from copy import deepcopy
import json

from study import DEPS, OUT, grade_reply, number, read


def strip_json_string(raw):
    if not isinstance(raw, str) or not raw.startswith('"'):
        return raw
    try:
        parsed = json.loads(raw)
    except ValueError:
        return raw
    return parsed if isinstance(parsed, str) and number(parsed) is not None else raw


def main():
    cases = read(OUT / "cases.json")
    scores = read(OUT / "scores.json")
    print("# 額外診斷 · 金額字串多一層引號\n")
    print("這份敏感度分析在發現格式問題後建立。只去除 JSON 金額多包的一層引號，"
          "保留相同標註、取證、金額精度、政策和原始回傳。正式結果保留原格式評分。\n")
    print("| 呼叫 | 套用修正的欄位 | 數值正確增加 | 有證據正確增加 |")
    print("|---|---|---:|---:|")
    for s in scores:
        candidate = deepcopy(s["response"])
        fields = []
        for field in ("prior_q4", "latest_q4", "change"):
            normalized = strip_json_string(candidate[field])
            if normalized != candidate[field]:
                candidate[field] = normalized
                fields.append(field)
        if not fields:
            continue
        grades = grade_reply(cases[s["case"]], candidate)["grades"]["direct"]
        original = s["grades"]["direct"]
        numeric = sum(grades[k]["numeric_exact"] - original[k]["numeric_exact"] for k in DEPS)
        grounded = sum(grades[k]["grounded_correct"] - original[k]["grounded_correct"] for k in DEPS)
        print(f"| {s['id']} | {', '.join(fields)} | {numeric} | {grounded} |")


if __name__ == "__main__":
    main()
