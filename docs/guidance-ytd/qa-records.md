# 累計營收期間核對 · 逐案問答

以下為封存答案、模型實際回覆與新版驗證器選定的原文欄。金額為美元。

## Docusign · 先導

研究截止　2024-12-05T23:59:59-05:00

- [docu-prior 官方完整公告](https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf)
- [docu-latest 官方完整公告](https://s21.q4cdn.com/706790701/files/doc_news/Docusign-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 755333000 |
| 最新隱含 Q4 營收 | 760513000 |
| 隱含 Q4 差額 | 5180000 |
| 隱含 Q4 方向 | raised |

- prior　$2,940 to $2,952。[官方第 5 頁](https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf#page=5)
- prior_interim　$743 to $747。[官方第 5 頁](https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf#page=5)
- new　$2,959 to $2,963。[官方第 4 頁](https://s21.q4cdn.com/706790701/files/doc_news/Docusign-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf#page=4)
- prior_reported_in_period　1,445,667。[官方第 9 頁](https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf#page=9)
- reported_in_period　2,200,487。[官方第 8 頁](https://s21.q4cdn.com/706790701/files/doc_news/Docusign-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf#page=8)

- extract · completed。[模型原始 JSON](raw/formal/docu-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/docu-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 1465000000.0 | 755333000 | 錯 |
| 最新隱含 Q4 營收 | 1470200000.0 | 760513000 | 錯 |
| 隱含 Q4 差額 | 5200000.0 | 5180000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 755333000 | 755333000 | 對 |
| 最新隱含 Q4 營收 | 760513000 | 760513000 | 對 |
| 隱含 Q4 差額 | 5180000 | 5180000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 755333000 | 755333000 | 對 |
| 最新隱含 Q4 營收 | 760513000 | 760513000 | 對 |
| 隱含 Q4 差額 | 5180000 | 5180000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 新版 prior_reported_in_period　財年 2025，涵蓋第 1、2 季，公告 2024-09-05T23:59:59-04:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended July 31,       Six Months Ended July 31, (in thousands, except per share data)                                              2024           2023              2024           2023。第 3 欄，原始值 1,445,667，換算 1445667000 美元。[官方原頁](https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf#page=9)
- 新版 reported_in_period　財年 2025，涵蓋第 1、2、3 季，公告 2024-12-05T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended October          Nine Months Ended October 31,                                 31, (in thousands, except per share data)                    2024           2023                 2024          2023。第 3 欄，原始值 2,200,487，換算 2200487000 美元。[官方原頁](https://s21.q4cdn.com/706790701/files/doc_news/Docusign-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf#page=8)

## Sprout Social · 先導

研究截止　2024-11-07T23:59:59-05:00

- [sprt-prior 官方完整公告](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf)
- [sprt-latest 官方完整公告](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q3/earnings-result/Sprout-Social-3Q24-Earnings-Release.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 107320000.0 |
| 最新隱含 Q4 營收 | 106682000.0 |
| 隱含 Q4 差額 | -638000.0 |
| 隱含 Q4 方向 | lowered |

- prior　between $405.0 million and $406.0 million。[官方第 2 頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf#page=2)
- prior_interim　between $101.9 million and $102.1 million。[官方第 2 頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf#page=2)
- new　between $405.1 million and $405.9 million。[官方第 2 頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q3/earnings-result/Sprout-Social-3Q24-Earnings-Release.pdf#page=2)
- prior_reported_in_period　196,180。[官方第 7 頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf#page=7)
- reported_in_period　298,818。[官方第 8 頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q3/earnings-result/Sprout-Social-3Q24-Earnings-Release.pdf#page=8)

- extract · completed。[模型原始 JSON](raw/formal/sprt-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/sprt-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 204104000.0 | 107320000.0 | 錯 |
| 最新隱含 Q4 營收 | 203466000.0 | 106682000.0 | 錯 |
| 隱含 Q4 差額 | -638000.0 | -638000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 107320000.0 | 107320000.0 | 對 |
| 最新隱含 Q4 營收 | 106682000.0 | 106682000.0 | 對 |
| 隱含 Q4 差額 | -638000.0 | -638000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 107320000 | 107320000.0 | 對 |
| 最新隱含 Q4 營收 | 106682000 | 106682000.0 | 對 |
| 隱含 Q4 差額 | -638000 | -638000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

- 新版 prior_reported_in_period　財年 2024，涵蓋第 1、2 季，公告 2024-08-01T23:59:59-04:00。
  Consolidated Statements of Operations (Unaudited)。Six Months Ended June 30, 2024                     2023。第 1 欄，原始值 196,180，換算 196180000 美元。[官方原頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf#page=7)
- 新版 reported_in_period　財年 2024，涵蓋第 1、2、3 季，公告 2024-11-07T23:59:59-05:00。
  Consolidated Statements of Operations (Unaudited)。Nine Months Ended September 30, 2024                     2023。第 1 欄，原始值 298,818，換算 298818000 美元。[官方原頁](https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q3/earnings-result/Sprout-Social-3Q24-Earnings-Release.pdf#page=8)

## YETI · 先導

研究截止　2024-11-07T23:59:59-05:00

- [yeti-prior 官方完整公告](https://s22.q4cdn.com/322452763/files/doc_financials/2024/q2/YETI-Reports-Second-Quarter-2024-Results-2024.pdf)
- [yeti-latest 官方完整公告](https://s22.q4cdn.com/322452763/files/doc_financials/2024/q3/YETI-Reports-Third-Quarter-2024-Results-2024.pdf)

### 封存裁定

The prior release does not provide a Q3 consolidated net sales dollar outlook. Annual revenue growth rates do not supply it.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/yeti-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/yeti-astra.json)
  原回覆的證據缺口　缺少前次公告當時對2024財年第三季調整後淨銷售額的預測，或當時將下半年預測拆分至第三、四季的資料。

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 新版 prior_reported_in_period　財年 2024，涵蓋第 1、2 季，公告 2024-08-08T23:59:59-04:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended          Six Months Ended June 29,          July 1,  June 29,         July 1, 2024             2023      2024            2023。第 3 欄，原始值 804,893，換算 804893000 美元。[官方原頁](https://s22.q4cdn.com/322452763/files/doc_financials/2024/q2/YETI-Reports-Second-Quarter-2024-Results-2024.pdf#page=10)
- 新版 reported_in_period　財年 2024，涵蓋第 1、2、3 季，公告 2024-11-07T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended       Nine Months Ended September     September September    September 28,           30,       28,          30, 2024          2023      2024         2023。第 3 欄，原始值 1,283,333，換算 1283333000 美元。[官方原頁](https://s22.q4cdn.com/322452763/files/doc_financials/2024/q3/YETI-Reports-Third-Quarter-2024-Results-2024.pdf#page=9)
- 待查 prior　figure prior needs exactly one reference
- 待查 prior_interim　figure not located

## Workday · 先導

研究截止　2024-11-26T23:59:59-05:00

- [wday-prior 官方完整公告](https://s23.q4cdn.com/175719177/files/doc_news/Workday-Announces-Fiscal-2025-Second-Quarter-Financial-Results-2024.pdf)
- [wday-latest 官方完整公告](https://s21.q4cdn.com/950027458/files/doc_news/Workday-Announces-Fiscal-2025-Third-Quarter-Financial-Results-11-26-2024-2024.pdf)

### 封存裁定

The outlook is subscription revenue; it does not establish comparable consolidated total revenue guidance.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/wday-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/wday-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 2038500000 | unknown | 錯 |
| 隱含 Q4 差額 | -13500000 | unknown | 錯 |
| 隱含 Q4 方向 | lowered | unknown | 錯 |

**失分**　口徑不符

- 待查 new　figure not located
- 待查 prior　figure not located
- 待查 prior_interim　figure not located
- 待查 reported_in_period　累計表的幣別或單位無法核對
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## SentinelOne · 保留集

研究截止　2024-12-04T23:59:59-05:00

- [s-prior 官方完整公告](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf)
- [s-latest 官方完整公告](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q3/earnings-result/Q3-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 220208000.0 |
| 最新隱含 Q4 營收 | 222060000 |
| 隱含 Q4 差額 | 1852000.0 |
| 隱含 Q4 方向 | raised |

- prior　$815 million。[官方第 2 頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=2)
- prior_interim　$209.5 million。[官方第 2 頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=2)
- new　$818 million。[官方第 2 頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q3/earnings-result/Q3-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=2)
- prior_reported_in_period　385,292。[官方第 7 頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=7)
- reported_in_period　595,940。[官方第 8 頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q3/earnings-result/Q3-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=8)

- extract · completed。[模型原始 JSON](raw/formal/s-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/s-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 406563000.0 | 220208000.0 | 錯 |
| 最新隱含 Q4 營收 | 408415000 | 222060000 | 錯 |
| 隱含 Q4 差額 | 1852000.0 | 1852000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 220208000.0 | 220208000.0 | 對 |
| 最新隱含 Q4 營收 | 222060000 | 222060000 | 對 |
| 隱含 Q4 差額 | 1852000.0 | 1852000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 220208000 | 220208000.0 | 對 |
| 最新隱含 Q4 營收 | 222060000 | 222060000 | 對 |
| 隱含 Q4 差額 | 1852000 | 1852000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 新版 prior_reported_in_period　財年 2025，涵蓋第 1、2 季，公告 2024-08-27T23:59:59-04:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended July 31,       Six Months Ended July 31, 2024             2023             2024            2023。第 3 欄，原始值 385,292，換算 385292000 美元。[官方原頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=7)
- 新版 reported_in_period　財年 2025，涵蓋第 1、2、3 季，公告 2024-12-04T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended October 31,   Nine Months Ended October 31, 2024            2023             2024            2023。第 3 欄，原始值 595,940，換算 595940000 美元。[官方原頁](https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q3/earnings-result/Q3-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf#page=8)

## Doximity · 保留集

研究截止　2025-02-06T23:59:59-05:00

- [docs-prior 官方完整公告](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf)
- [docs-latest 官方完整公告](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q3/Doximity-3Q25-Earnings-Call-Press-Release.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 121492000 |
| 最新隱含 Q4 營收 | 132989000.0 |
| 隱含 Q4 差額 | 11497000.0 |
| 隱含 Q4 方向 | raised |

- prior　between $535 million and $540 million。[官方第 1 頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf#page=1)
- prior_interim　between $152 million and $153 million。[官方第 1 頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf#page=1)
- new　between $564.6 million and $565.6 million。[官方第 1 頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q3/Doximity-3Q25-Earnings-Call-Press-Release.pdf#page=1)
- prior_reported_in_period　263,508。[官方第 4 頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf#page=4)
- reported_in_period　432,111。[官方第 4 頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q3/Doximity-3Q25-Earnings-Call-Press-Release.pdf#page=4)

- extract · completed。[模型原始 JSON](raw/formal/docs-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/docs-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 248200000.0 | 121492000 | 錯 |
| 最新隱含 Q4 營收 | 259700000.0 | 132989000.0 | 錯 |
| 隱含 Q4 差額 | 11500000.0 | 11497000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 121492000 | 121492000 | 對 |
| 最新隱含 Q4 營收 | 132989000.0 | 132989000.0 | 對 |
| 隱含 Q4 差額 | 11497000.0 | 11497000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 121492000 | 121492000 | 對 |
| 最新隱含 Q4 營收 | 132989000 | 132989000.0 | 對 |
| 隱含 Q4 差額 | 11497000 | 11497000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 新版 prior_reported_in_period　財年 2025，涵蓋第 1、2 季，公告 2024-11-07T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended   Six Months Ended September 30,       September 30, 2024        2023    2024        2023。第 3 欄，原始值 263,508，換算 263508000 美元。[官方原頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf#page=4)
- 新版 reported_in_period　財年 2025，涵蓋第 1、2、3 季，公告 2025-02-06T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three Months Ended   Nine Months Ended December 31,         December 31, 2024        2023     2024        2023。第 3 欄，原始值 432,111，換算 432111000 美元。[官方原頁](https://s201.q4cdn.com/617428576/files/doc_financials/2025/q3/Doximity-3Q25-Earnings-Call-Press-Release.pdf#page=4)

## monday.com · 保留集

研究截止　2024-11-11T23:59:59-05:00

- [mndy-prior 官方完整公告](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001845338/a0415556-b4a7-4c55-88b4-3794d88dbf9c.pdf)
- [mndy-latest 官方完整公告](https://s29.q4cdn.com/881027206/files/doc_financials/2024/q3/Q3-24-PR.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 260481000 |
| 最新隱含 Q4 營收 | 260981000 |
| 隱含 Q4 差額 | 500000 |
| 隱含 Q4 方向 | raised |

- prior　$956 million to $961 million。[官方第 6 頁](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001845338/a0415556-b4a7-4c55-88b4-3794d88dbf9c.pdf#page=6)
- prior_interim　$243 million to $247 million。[官方第 5 頁](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001845338/a0415556-b4a7-4c55-88b4-3794d88dbf9c.pdf#page=5)
- new　$964 million to $966 million。[官方第 2 頁](https://s29.q4cdn.com/881027206/files/doc_financials/2024/q3/Q3-24-PR.pdf#page=2)
- prior_reported_in_period　453,019。[官方第 9 頁](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001845338/a0415556-b4a7-4c55-88b4-3794d88dbf9c.pdf#page=9)
- reported_in_period　704,019。[官方第 6 頁](https://s29.q4cdn.com/881027206/files/doc_financials/2024/q3/Q3-24-PR.pdf#page=6)

- extract · completed。[模型原始 JSON](raw/formal/mndy-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/mndy-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 477400000.0 | 260481000 | 錯 |
| 最新隱含 Q4 營收 | 477900000.0 | 260981000 | 錯 |
| 隱含 Q4 差額 | 500000.0 | 500000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 260481000 | 錯 |
| 最新隱含 Q4 營收 | unknown | 260981000 | 錯 |
| 隱含 Q4 差額 | unknown | 500000 | 錯 |
| 隱含 Q4 方向 | unknown | raised | 錯 |

**失分**　引文不足

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 260481000 | 260481000 | 對 |
| 最新隱含 Q4 營收 | 260981000 | 260981000 | 對 |
| 隱含 Q4 差額 | 500000 | 500000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 新版 reported_in_period　財年 2024，涵蓋第 1、2、3 季，公告 2024-11-11T23:59:59-05:00。
  CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。Three months ended                      Nine months ended September 30,                          September 30, 2024                   2023             2024                 2023。第 3 欄，原始值 704,019，換算 704019000 美元。[官方原頁](https://s29.q4cdn.com/881027206/files/doc_financials/2024/q3/Q3-24-PR.pdf#page=6)
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## JFrog · 保留集

研究截止　2024-11-07T23:59:59-05:00

- [frog-prior 官方完整公告](https://s21.q4cdn.com/528621000/files/doc_news/2024/08/1/JFrog-Q2-2024-Earnings-PR_FINAL.pdf)
- [frog-latest 官方完整公告](https://s21.q4cdn.com/528621000/files/doc_financials/2024/q3/FINAL-JFrog-Q3-2024-Earnings-PR_11-7.pdf)

### 封存裁定

選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | 114146000 |
| 最新隱含 Q4 營收 | 113990000.0 |
| 隱含 Q4 差額 | -156000.0 |
| 隱含 Q4 方向 | lowered |

- prior　$422 million to $424 million。[官方第 2 頁](https://s21.q4cdn.com/528621000/files/doc_news/2024/08/1/JFrog-Q2-2024-Earnings-PR_FINAL.pdf#page=2)
- prior_interim　between $105 million and $106 million。[官方第 2 頁](https://s21.q4cdn.com/528621000/files/doc_news/2024/08/1/JFrog-Q2-2024-Earnings-PR_FINAL.pdf#page=2)
- new　$425.9 million to $ 426.9 million。[官方第 2 頁](https://s21.q4cdn.com/528621000/files/doc_financials/2024/q3/FINAL-JFrog-Q3-2024-Earnings-PR_11-7.pdf#page=2)
- prior_reported_in_period　203,354。[官方第 7 頁](https://s21.q4cdn.com/528621000/files/doc_news/2024/08/1/JFrog-Q2-2024-Earnings-PR_FINAL.pdf#page=7)
- reported_in_period　312,410。[官方第 7 頁](https://s21.q4cdn.com/528621000/files/doc_financials/2024/q3/FINAL-JFrog-Q3-2024-Earnings-PR_11-7.pdf#page=7)

- extract · completed。[模型原始 JSON](raw/formal/frog-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/frog-astra.json)

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 214457000 | 114146000 | 錯 |
| 最新隱含 Q4 營收 | 214301000.0 | 113990000.0 | 錯 |
| 隱含 Q4 差額 | -156000.0 | -156000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

**失分**　期間選錯

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 114146000 | 錯 |
| 最新隱含 Q4 營收 | unknown | 113990000.0 | 錯 |
| 隱含 Q4 差額 | unknown | -156000.0 | 錯 |
| 隱含 Q4 方向 | unknown | lowered | 錯 |

**失分**　引文不足

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 114146000 | 114146000 | 對 |
| 最新隱含 Q4 營收 | 113990000 | 113990000.0 | 對 |
| 隱含 Q4 差額 | -156000 | -156000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

**失分**　引文不足

- 待查 reported_in_period　指定單季數值無法唯一定位至合併營收欄
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## Home Depot · 保留集

研究截止　2024-11-12T23:59:59-05:00

- [hd-prior 官方完整公告](https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/press-release/q2-2024-earning-release.pdf)
- [hd-latest 官方完整公告](https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/press-release/q3-2024-earning-release.pdf)

### 封存裁定

Fiscal-year sales growth guidance and SRS contribution do not establish a prior Q3 USD revenue guidance at the same consolidated scope.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/hd-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/hd-astra.json)
  原回覆的證據缺口　兩份公告均未提供將全年成長率換算為美元金額所需的2023財年全年淨銷售額。前次公告也未提供2024財年第三季營收指引，無法從當時預估的下半年營收中單獨推算第四季。

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 待查 new　figure not located
- 待查 prior　figure not located
- 待查 prior_interim　figure not located
- 待查 reported_in_period　指定單季數值無法唯一定位至合併營收欄
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## Target · 保留集

研究截止　2024-11-20T23:59:59-05:00

- [tgt-prior 官方完整公告](https://corporate.target.com/getmedia/50a20b2e-c394-4ae2-ab73-8afcf99b4e0c/Target-Corporation-Reports-Second-Quarter-Earnings.pdf)
- [tgt-latest 官方完整公告](https://corporate.target.com/getmedia/9bb5f514-fcaf-4097-837d-f08ff31cb089/Target-Corporation-Reports-Third-Quarter-Earnings.pdf)

### 封存裁定

Quarterly comparable sales and diluted EPS outlook are not a Q3 consolidated revenue dollar estimate.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/tgt-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/tgt-astra.json)
  原回覆的證據缺口　前次公告缺少 2024 財年全年及第三季合併營收的美元指引，無法從全年預估扣除上半年實績及第三季預估。最新公告也缺少全年合併營收的美元指引，無法扣除前九個月實績以推算第四季。

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 待查 new　figure not located
- 待查 prior　figure not located
- 待查 prior_interim　figure not located
- 待查 reported_in_period　指定單季數值無法唯一定位至合併營收欄
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## Costco · 保留集

研究截止　2025-05-29T23:59:59-04:00

- [cost-prior 官方完整公告](https://s201.q4cdn.com/287523651/files/doc_news/Costco-Wholesale-Corporation-Reports-Second-Quarter-and-Year-To-Date-Operating-Results-For-Fiscal-2025-and-February-Sales-Results-2025.pdf)
- [cost-latest 官方完整公告](https://s201.q4cdn.com/287523651/files/doc_news/Costco-Wholesale-Corporation-Reports-Third-Quarter-and-Year-To-Date-Operating-Results-for-Fiscal-2025-2025.pdf)

### 封存裁定

Both announcements provide actual net sales and comparisons, without the prior Q3 or comparable full-year revenue outlook.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/cost-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/cost-astra.json)
  原回覆的證據缺口　3月6日公告未提供2025財年全年或第三季的合併總營收指引，5月29日公告也未提供2025財年全年合併總營收指引。

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 待查 new　figure not located
- 待查 prior　figure not located
- 待查 prior_interim　figure not located
- 待查 reported_in_period　指定單季數值無法唯一定位至合併營收欄
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄

## Deckers · 保留集

研究截止　2025-01-30T23:59:59-05:00

- [deck-prior 官方完整公告](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000910521/5cecef8a-b608-488a-8a1c-629f0fd54187.pdf)
- [deck-latest 官方完整公告](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000910521/c55b9dbd-d813-47e6-8399-fce0ecee367d.pdf)

### 封存裁定

Annual net sales can be disclosed, but the prior release does not publish a comparable Q3 total net sales amount.

| 項目 | 答案 |
|---|---|
| 前次隱含 Q4 營收 | unknown |
| 隱含 Q4 差額 | unknown |
| 隱含 Q4 方向 | unknown |


- extract · completed。[模型原始 JSON](raw/formal/deck-extract.json)
- astra · completed。[模型原始 JSON](raw/formal/deck-astra.json)
  原回覆的證據缺口　2024 年 10 月 24 日的公告未提供 2025 財年第三季合併營收指引，也未直接揭露第四季營收預估。第三季實績於次年 1 月才公布。

### 現版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 項目 | 回覆 | 答案 | 對錯 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 待查 prior_interim　figure not located
- 待查 reported_in_period　指定單季數值無法唯一定位至合併營收欄
- 待查 prior_reported_in_period　指定單季數值無法唯一定位至合併營收欄
