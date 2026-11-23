# 指引修正算術：確定性評分

驗證 Harness 能否在公司營收指引的修正算術上比純 Astra 更準。每個輸入數字都引用封存公告的段落與原文；程式核對雜湊、原文與數值後，用 Decimal 算出標準答案，不由人工填寫。評分完全確定：金額與百分比在標準答案 1% 內為對，方向須完全一致，案件所有題目全對才算全對。

兩組使用同一個 `gpt-6.2-astra` medium、同一份封存公告、各一次呼叫及 180 秒上限，停用搜尋。純 Astra 直接作答；Harness 只請 Astra 定位所需數字的原文，由程式核對引文並計算，核對失敗的題目記為 unknown。

## 先導 v1：明示基準的單步算術

8 案取自先前 benchmark 已封存的公告，包括區間收窄但中點上修、點估計對區間、加減區間寫法、季度與全年並列、表格單位為千元等情形。每案兩組各跑 3 次。

| | 純 Astra | Harness |
|---|---:|---:|
| 全對執行 | 24/24 | 24/24 |
| 題目答對 | 96/96 | 96/96 |
| 失敗呼叫 | 0 | 0 |
| 中位耗時 | 11.1 秒 | 11.7 秒 |
| 輸入詞元 | 541,884 | 541,291 |

**結論：題目明示比較基準、新舊指引寫在同一句時，純 Astra 已達滿分，Harness 沒有領先空間。**Harness 的 48 次數字引用全部通過機械核對，成本與純 Astra 相當。依預註冊規則，兩組沒有任何不一致案件，不開保留集。

封存時間 2026-11-23T12:07:32Z。[預註冊](pilot-v1/protocol.json) · [封存案例與標準答案](pilot-v1/cases.json) · [逐次結果](pilot-v1/summary-pilot.json)

```bash
python -m benchmarks.guidance_arithmetic --phase check
python -m benchmarks.guidance_arithmetic --out output/guidance-arithmetic --phase seal
python -m benchmarks.guidance_arithmetic --out output/guidance-arithmetic --phase pilot
python -m benchmarks.guidance_arithmetic --out output/guidance-arithmetic --phase report
```

下一輪改測兩種較難的情形：舊指引在前一份公告、實績在本次表格的跨文件隱含季度推算；以及不說明比較基準的開放式問法。
