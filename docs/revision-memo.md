# 財報預估修正稿

同一頁顯示事件前內估、各提供者的點時共識、舊指引、新披露、母版及目前封存預估。已有版本可直接比較，保留同財季、幣別、會計基礎與合併口徑的數字。共識使用有權使用的 CSV 匯出與原擷取時間。範例採用已封存的歷史公告及研究模型假設，授權市場共識欄保留待查。

## 從對話啟動

先以 `report_find` 選帶有盈利計畫的報告。用 `revision_memo_create` 指定季度及版本，若有新公告可先用 `attachment_add` 加入原始 HTML。`revision_memo_export` 輸出一頁 HTML 和可編輯的 Excel。`revision_memo_get` 查目前覆核狀態和該版次同季的預測實績。對話沿用既有 Codex 模型與資料庫。

API 以 `/reports/{id}/revisions/{v}/revision-memos` 建立稿件。可傳 `period_end`、`baseline_revision`，以及 `quotes` 或 `filing`。用 `/revision-memos/{memo_id}` 讀凍結內容，`/exports/html` 及 `/exports/xlsx` 取檔。`cross_page` 可指定既有 `guidance-table` 或 `guidance-ytd` 案例作為同發行人、同事件的原文對照。倒推中點另列，既有完整公告試算仍使用經核對的公司區間。

XLSX 的藍色模型欄位可修改。營收與毛利率和費用連至營業利益，稅前業外、有效稅率、虧損稅益、一次性稅額及股數連至 EPS。估值頁分解原報告的盈利與倍數影響。編輯 Excel 之後若要重走內部簽核，應把採用的數字與假設另存為研究子版，再建立新的修正稿。

## 內部覆核

`RESEARCH_MEMO_IDENTITIES` 設定具名身分到角色與高熵權杖 SHA-256 的映射，每個身分使用各自的權杖。角色包括 `author`、`reviewer`、`approver`。使用者從受信任的本機 HTTP 客戶端以 `Authorization: Bearer` 驗證身分，`POST /reports/{id}/revisions/{v}/revision-memos/{memo_id}/signoffs` 提交 `decision`、`conflict_check`、`note` 和可選的 `duration_seconds`。透過 MCP 建稿的作者身分可從該服務私有環境的 `RESEARCH_MEMO_AUTHOR_TOKEN` 載入。

分析師覆核與最終內部核准分開記錄。最終內部核准需要具名作者、不同覆核身分和完整關鍵證據。核准稿件凍結。多租戶帳號管理、企業 SSO、利益衝突資料來源和對客發布流程須由部署方接入。

## 評測進度

```bash
python -m benchmarks.revision_memo_review --phase seal
python -m benchmarks.revision_memo_review --phase report --calibration-ratings /path/to/fill.csv
python -m benchmarks.revision_memo_review --phase run --calibration-ratings /path/to/fill.csv
```

已匯出 UPS、Disney、Novo Nordisk、Ford 的四個既有完整配對作人工校準。評分表與匿名稿在 `output/revision-memo-review/calibration/`，對照鍵留在上層本機資料夾。正式八案採用原本已封存且未開跑的 V9 發行人，測量主要傳導、替代解釋和公開反證。兩組看同樣的點時證據，使用相同 Astra、一次呼叫、180 秒、停用搜尋，記錄實際使用量。這八案沒有一致的點時完整財務模型及共識，量化修正稿的整體可用率仍需另收資料評測。

正式 `run` 在四案人工校準均收到成對評分後才開始。通過門檻是八案齊全、Harness 至少六案可用、比純 Astra 多兩案，且重大錯誤總數不高於 Astra。修稿秒數另計。用 `--holdout-ratings` 匯入評分，只有完整的人工配對會納入。

本輪已備妥人工校準 **4/4**，實收 **0/4**。正式保留集封存 **8 案**，啟動 **0 案**。三個既有前瞻隊列各有 **3 案** 已封存預測，已回填實績各 **0 筆**。
