# 跨頁表頭與合併營收列核對 · 逐案問答

## Freshworks · 先導

研究截止 2024-11-06T23:59:59-05:00。期間、期末與年份分行，營收列和數字用點線分隔。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2024 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [frsh-prior 來源公告](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf)
- [frsh-latest 來源公告](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf)
- prior_reported_in_period　第 3 欄，339,274 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 8 頁第 2 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　Three Months Ended          Six Months Ended。[第 8 頁第 5 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　June 30,                   June 30,。[第 8 頁第 6 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　2024          2023         2024          2023。[第 8 頁第 7 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 倍率　(in thousands, except per share data)。[第 8 頁第 3 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 營收列　Revenue .............................................................................$    174,131 $     145,079 $    339,274 $     282,771。[第 8 頁第 8 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
- reported_in_period　第 3 欄，525,849 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 8 頁第 2 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　Three Months Ended         Nine Months Ended。[第 8 頁第 5 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　September 30,             September 30,。[第 8 頁第 6 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　2024          2023         2024          2023。[第 8 頁第 7 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 倍率　(in thousands, except per share data)。[第 8 頁第 3 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 營收列　Revenue............................................................................ $   186,575 $     153,550 $    525,849 $     436,321。[第 8 頁第 8 行](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
- prior　[$707.0 - $713.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
- prior_interim　[$180.0 - $183.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
- new　[$713.6 - $716.6](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=3)

- extract　completed。[模型原始 JSON](raw/formal/frsh-extract.json)
  模型判讀　財測取自兩次公告的營收列，保留公司公布的區間。7 月公告時已披露第二季實績，11 月公告時第三季實績也已公布。兩份公告均未單列第一季營收，因此省略第一季。
  - new　frsh-latest:p0003 · [$713.6 - $716.6](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=3)
  - prior　frsh-prior:p0003 · [$707.0 - $713.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
  - prior_interim　frsh-prior:p0003 · [$180.0 - $183.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
  - reported_in_period　frsh-prior:p0008 · [$ 174,131](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - reported_in_period　frsh-latest:p0008 · [$ 186,575](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - prior_reported_in_period　frsh-prior:p0008 · [$ 174,131](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
- astra　completed。[模型原始 JSON](raw/formal/frsh-astra.json)
  模型判讀　以美元計，前次全年營收指引中點減去上半年實績及當時的第三季指引中點，得出第四季隱含營收 710000000 − 339274000 − 181500000 = 189226000。最新全年指引中點減去前九個月實績，得出 715100000 − 525849000 = 189251000，較前次上調 25000 美元。
  - prior　frsh-prior:p0003 · [$707.0 - $713.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
  - prior_reported_in_period　frsh-prior:p0008 · [$ 339,274](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - prior_interim　frsh-prior:p0003 · [$180.0 - $183.0](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=3)
  - new　frsh-latest:p0003 · [$713.6 - $716.6](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=3)
  - reported_in_period　frsh-latest:p0008 · [$ 525,849](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 189226000.0 | 錯 |
| 最新隱含 Q4 營收 | unknown | 189251000.0 | 錯 |
| 隱含 Q4 差額 | unknown | 25000.0 | 錯 |
| 隱含 Q4 方向 | unknown | raised | 錯 |

失分　引文不足。

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 189226000.0 | 189226000.0 | 對 |
| 最新隱含 Q4 營收 | 189251000.0 | 189251000.0 | 對 |
| 隱含 Q4 差額 | 25000.0 | 25000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 189226000 | 189226000.0 | 對 |
| 最新隱含 Q4 營收 | 189251000 | 189251000.0 | 對 |
| 隱含 Q4 差額 | 25000 | 25000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 現版待查　reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 現版待查　prior_reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 新版 reported_in_period　公告 2024-11-06T23:59:59-05:00 · 財年 2024 · 第 3 欄 · 原始值 525,849 · 525849000 美元
  - 數值列　Revenue............................................................................ $   186,575 $     153,550 $    525,849 $     436,321。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　(in thousands, except per share data)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　(unaudited)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　Three Months Ended         Nine Months Ended。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　September 30,             September 30,。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 表頭　2024          2023         2024          2023。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 倍率　(in thousands, except per share data)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
  - 幣別　Revenue............................................................................ $   186,575 $     153,550 $    525,849 $     436,321。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf#page=8)
- 新版 prior_reported_in_period　公告 2024-07-30T23:59:59-04:00 · 財年 2024 · 第 3 欄 · 原始值 339,274 · 339274000 美元
  - 數值列　Revenue .............................................................................$    174,131 $     145,079 $    339,274 $     282,771。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　(in thousands, except per share data)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　(unaudited)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　Three Months Ended          Six Months Ended。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　June 30,                   June 30,。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 表頭　2024          2023         2024          2023。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 倍率　(in thousands, except per share data)。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)
  - 幣別　Revenue .............................................................................$    174,131 $     145,079 $    339,274 $     282,771。[原文位置](https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf#page=8)

## Salesforce · 先導

研究截止 2024-12-03T23:59:59-05:00。跨欄期間與年份分行。合併金額涵蓋訂閱支援與專業服務。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2025 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [crm-prior 來源公告](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf)
- [crm-latest 來源公告](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf)
- prior_reported_in_period　第 3 欄，18,458 × 1,000,000 美元
  - 表名　Condensed Consolidated Statements of Operations。[第 6 頁第 2 行](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 表頭　2                                                               Three Months Ended July 31,          Six Months Ended July 31,。[第 6 頁第 5 行](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 表頭　2024              2023              2024              2023。[第 6 頁第 6 行](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 倍率　(in millions, except per share data)。[第 6 頁第 3 行](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 營收列　Total revenues                                                9,325             8,603            18,458            16,850。[第 6 頁第 10 行](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
- reported_in_period　第 3 欄，27,902 × 1,000,000 美元
  - 表名　Condensed Consolidated Statements of Operations。[第 6 頁第 2 行](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 表頭　3                                                              Three Months Ended October 31,        Nine Months Ended October 31,。[第 6 頁第 5 行](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 表頭　2024             2023                2024              2023。[第 6 頁第 6 行](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 倍率　(in millions, except per share data)。[第 6 頁第 3 行](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - 營收列　Total revenues                                               9,444            8,720              27,902            25,570。[第 6 頁第 10 行](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
- prior　[$37.7 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
- prior_interim　[$9.31 Billion to $9.36 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
- new　[$37.8 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=1)

- extract　completed。[模型原始 JSON](raw/formal/crm-extract.json)
  模型判讀　兩份公告均列出全年營收指引區間，第二季公告也列出第三季指引。依各公告發布時點，第二季實績可用於兩次指引，第三季實績僅可用於最新指引。兩份公告均未單列第一季營收，因此省略該季。
  - new　crm-latest:p0001 · [$37.8 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - prior　crm-prior:p0001 · [$37.7 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - prior_interim　crm-prior:p0001 · [$9.31 Billion to $9.36 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - reported_in_period　crm-prior:p0011 · [$ 9,325](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=11)
  - reported_in_period　crm-latest:p0011 · [$ 9,444](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=11)
  - prior_reported_in_period　crm-prior:p0011 · [$ 9,325](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=11)
- astra　completed。[模型原始 JSON](raw/formal/crm-astra.json)
  模型判讀　以百萬美元計，前次全年營收指引中點扣除上半年實績及當時的第三季指引中點，得出第四季隱含營收 37850 − 18458 − 9335 = 10057。最新全年指引中點扣除前九個月實績，得出 37900 − 27902 = 9998。兩者相差 9998 − 10057 = −59，即下修 59000000 美元。
  - prior　crm-prior:p0001 · [Maintains Full Year FY25 Revenue Guidance of $37.7 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - prior_reported_in_period　crm-prior:p0006 · [Total revenues 9,325 8,603 18,458 16,850](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=6)
  - prior_interim　crm-prior:p0001 · [Initiates Third Quarter FY25 Revenue Guidance of $9.31 Billion to $9.36 Billion](https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - new　crm-latest:p0001 · [Raises Low End of Full Year FY25 Revenue Guidance to $37.8 Billion to $38.0 Billion](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=1)
  - reported_in_period　crm-latest:p0006 · [Total revenues 9,444 8,720 27,902 25,570](https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf#page=6)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 10057000000.00 | 10057000000.00 | 對 |
| 最新隱含 Q4 營收 | 9998000000.0 | 9998000000.0 | 對 |
| 隱含 Q4 差額 | -59000000.00 | -59000000.00 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 10057000000.00 | 錯 |
| 最新隱含 Q4 營收 | unknown | 9998000000.0 | 錯 |
| 隱含 Q4 差額 | unknown | -59000000.00 | 錯 |
| 隱含 Q4 方向 | unknown | lowered | 錯 |

失分　單位、單位錯、引文不足。

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 10057000000 | 10057000000.00 | 對 |
| 最新隱含 Q4 營收 | 9998000000 | 9998000000.0 | 對 |
| 隱含 Q4 差額 | -59000000 | -59000000.00 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

失分　引文不足。

- 新版待查　reported_in_period · 所選財務表的美元幣別或金額倍率缺失、不一致或範圍不明。
- 新版待查　prior_reported_in_period · 所選財務表的美元幣別或金額倍率缺失、不一致或範圍不明。

## Lowe’s · 先導

研究截止 2024-11-19T23:59:59-05:00。前次有全年銷售指引，缺第三季合併銷售美元指引。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [low-prior 來源公告](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf)
- [low-latest 來源公告](https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf)
- 缺項核對　[Total sales of $82.7 to $83.2 billion](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=2)

- extract　completed。[模型原始 JSON](raw/formal/low-extract.json)
  模型判讀　全年營收指引取自兩次公告的全年銷售額區間。第二季及第三季實績取自合併損益表的單季淨銷售額欄。公告未單列第一季營收，也未提供第三季營收指引，故省略。
  - new　low-latest:p0002 · [$83.0 to $83.5 billion](https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf#page=2)
  - prior　low-prior:p0002 · [$82.7 to $83.2 billion](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=2)
  - reported_in_period　low-prior:p0004 · [$ 23,586](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=4)
  - reported_in_period　low-latest:p0004 · [$ 20,170](https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf#page=4)
  - prior_reported_in_period　low-prior:p0004 · [$ 23,586](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=4)
- astra　completed。[模型原始 JSON](raw/formal/low-astra.json)
  模型判讀　8 月公告未提供當時的 2024 財年第三季營收指引，無法從下半年合計金額中扣除第三季預估營收。
  - prior　low-prior:p0002 · [Total sales of $82.7 to $83.2 billion](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=2)
  - prior_reported_in_period　low-prior:p0004 · [$ 44,950](https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf#page=4)
  - new　low-latest:p0002 · [Total sales of $83.0 to $83.5 billion](https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf#page=2)
  - reported_in_period　low-latest:p0004 · [$ 65,120](https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf#page=4)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 現版待查　prior_interim · figure not located
- 現版待查　reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 現版待查　prior_reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 新版待查　prior_interim · figure not located
- 新版待查　reported_in_period · 無法唯一證明該列是完整合併營收，或同期間存在多個候選。
- 新版待查　prior_reported_in_period · 無法唯一證明該列是完整合併營收，或同期間存在多個候選。

## Medtronic · 先導

研究截止 2025-02-18T23:59:59-05:00。排除匯率等因素的有機成長率，無法證明同口徑合併營收美元。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [mdt-prior 來源公告](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1)
- [mdt-latest 來源公告](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1)
- 缺項核對　[raised its FY25 organic revenue growth guidance](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1#page=1)

- extract　completed。[模型原始 JSON](raw/formal/mdt-extract.json)
  模型判讀　兩份公告均以成長率表述 2025 財年營收指引，未列全年或第三季的營收預估金額。公告直接列出第二季及第三季的全球營收實績；前次發布指引時，第二季實績已公布。第一季營收須由半年累計額扣除第二季金額推算，故未列入。
  - reported_in_period　mdt-prior:p0001 · [Medtronic reported Q2 worldwide revenue of $8.403 billion](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1#page=1)
  - reported_in_period　mdt-latest:p0001 · [Medtronic reported Q3 worldwide revenue of $8.292 billion](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=1)
  - prior_reported_in_period　mdt-prior:p0001 · [Medtronic reported Q2 worldwide revenue of $8.403 billion](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1#page=1)
- astra　completed。[模型原始 JSON](raw/formal/mdt-astra.json)
  模型判讀　兩份公告均缺少 FY25 全年合併營收的美元指引金額，亦缺少將成長率換算為金額所需的同口徑 FY24 全年營收基數。前次公告另缺少 FY25 第三季合併營收指引，無法從當時的下半年預期中單獨推算第四季。
  - prior　mdt-prior:p0001 · [FY25 revenue growth on an adjusted basis would be in the range of 3.4% to 3.9%.](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1#page=1)
  - prior_reported_in_period　mdt-prior:p0003 · [$ 16,318](https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - new　mdt-latest:p0001 · [FY25 revenue growth would be in the range of 3.4% to 3.8%.](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=1)
  - reported_in_period　mdt-latest:p0003 · [$ 24,610](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 現版待查　new · figure not located
- 現版待查　prior · figure not located
- 現版待查　prior_interim · figure not located
- 新版待查　new · figure not located
- 新版待查　prior · figure not located
- 新版待查　prior_interim · figure not located
- 新版待查　prior_reported_in_period · 表格延續或累計期間與財年無法唯一對應至同一數值欄。
- 新版 reported_in_period　公告 2025-02-18T23:59:59-05:00 · 財年 2025 · 第 3 欄 · 原始值 24,610 · 24610000000 美元
  - 數值列　Net sales                                                              $            8,292    $            8,089       $        24,610          $        23,775。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 表名　CONSOLIDATED STATEMENTS OF INCOME。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 表頭　(Unaudited)。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 表頭　Three months ended                             Nine months ended。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 表頭　January 24,           January 26,              January 24,              January 26,。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 表頭　(in millions, except per share data)                                          2025                     2024                  2025                     2024。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 倍率　(in millions, except per share data)                                          2025                     2024                  2025                     2024。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)
  - 幣別　Net sales                                                              $            8,292    $            8,089       $        24,610          $        23,775。[原文位置](https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1#page=3)

## Backblaze · 保留集

研究截止 2024-11-07T23:59:59-05:00。最新公告的營運表標題與千元倍率在前一實體頁，累計期間和金額在次頁。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2024 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [blze-prior 來源公告](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf)
- [blze-latest 來源公告](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf)
- prior_reported_in_period　第 3 欄，61,253 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 4 頁第 42 行](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表頭　Three Months Ended June 30,                Six Months Ended June 30,。[第 4 頁第 44 行](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表頭　2024                  2023                 2024                2023。[第 4 頁第 45 行](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 倍率　(in thousands, except share and per share data)。[第 4 頁第 43 行](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 營收列　Revenue                                                                    $         31,285    $          24,589     $            61,253    $       47,983。[第 4 頁第 47 行](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
- reported_in_period　第 3 欄，93,842 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE LOSS。[第 5 頁第 49 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=5)
  - 表頭　Three Months Ended              Nine Months Ended。[第 6 頁第 1 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 表頭　September 30,                   September 30,。[第 6 頁第 2 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 表頭　2024         2023               2024        2023。[第 6 頁第 3 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 倍率　(in thousands, except share and per share data)。[第 5 頁第 50 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=5)
  - 營收列　Revenue                                                     $      32,589 $        25,299 $      93,842 $          73,282。[第 6 頁第 5 行](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
- prior　[$126.5 million to $128.5 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
- prior_interim　[$32.4 million to $32.8 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
- new　[$127.0 million to $128.0 million](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=2)

- extract　completed。[模型原始 JSON](raw/formal/blze-extract.json)
  模型判讀　兩份公告均直接列出全年營收指引，前次公告也列出第三季指引。第二季合併營收在兩次指引發布時均已公布，第三季實績則於最新公告公布。所附公告未單列第一季營收，故省略該季。
  - new　blze-latest:p0002 · [between $127.0 million to $128.0 million](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=2)
  - prior　blze-prior:p0002 · [between $126.5 million to $128.5 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
  - prior_interim　blze-prior:p0002 · [between $32.4 million to $32.8 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
  - reported_in_period　blze-prior:p0004 · [$ 31,285](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - reported_in_period　blze-latest:p0006 · [$ 32,589](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - prior_reported_in_period　blze-prior:p0004 · [$ 31,285](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
- astra　completed。[模型原始 JSON](raw/formal/blze-astra.json)
  模型判讀　以千美元計，兩次全年營收指引的中點均為 127500。前次扣除上半年實績及第三季指引中點，第四季隱含營收為 127500 − 61253 − 32600 = 33647。最新指引扣除前九個月實績後為 127500 − 93842 = 33658，較前次增加 11000 美元。
  - prior　blze-prior:p0002 · [For full-year 2024 we expect: Revenue between $126.5 million to $128.5 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
  - prior_reported_in_period　blze-prior:p0004 · [$ 61,253](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - prior_interim　blze-prior:p0002 · [For the third quarter of 2024 we expect: Revenue between $32.4 million to $32.8 million](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=2)
  - new　blze-latest:p0002 · [For full-year 2024 we expect: Revenue between $127.0 million to $128.0 million](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=2)
  - reported_in_period　blze-latest:p0006 · [$ 93,842](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 33647000.0 | 錯 |
| 最新隱含 Q4 營收 | unknown | 33658000.0 | 錯 |
| 隱含 Q4 差額 | unknown | 11000.0 | 錯 |
| 隱含 Q4 方向 | unknown | raised | 錯 |

失分　單位、單位錯、引文不足。

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 33647000.0 | 33647000.0 | 對 |
| 最新隱含 Q4 營收 | 33658000.0 | 33658000.0 | 對 |
| 隱含 Q4 差額 | 11000.0 | 11000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 33647000 | 33647000.0 | 對 |
| 最新隱含 Q4 營收 | 33658000 | 33658000.0 | 對 |
| 隱含 Q4 差額 | 11000 | 11000.0 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 現版待查　reported_in_period · 累計表的幣別或單位無法核對
- 新版 reported_in_period　公告 2024-11-07T23:59:59-05:00 · 財年 2024 · 第 3 欄 · 原始值 93,842 · 93842000 美元
  - 數值列　Revenue                                                     $      32,589 $        25,299 $      93,842 $          73,282。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE LOSS。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=5)
  - 表頭　(in thousands, except share and per share data)。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=5)
  - 表頭　Three Months Ended              Nine Months Ended。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 表頭　September 30,                   September 30,。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 表頭　2024         2023               2024        2023。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
  - 倍率　(in thousands, except share and per share data)。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=5)
  - 幣別　Revenue                                                     $      32,589 $        25,299 $      93,842 $          73,282。[原文位置](https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf#page=6)
- 新版 prior_reported_in_period　公告 2024-08-08T23:59:59-04:00 · 財年 2024 · 第 3 欄 · 原始值 61,253 · 61253000 美元
  - 數值列　Revenue                                                                    $         31,285    $          24,589     $            61,253    $       47,983。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表頭　(in thousands, except share and per share data)。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表頭　Three Months Ended June 30,                Six Months Ended June 30,。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 表頭　2024                  2023                 2024                2023。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 倍率　(in thousands, except share and per share data)。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)
  - 幣別　Revenue                                                                    $         31,285    $          24,589     $            61,253    $       47,983。[原文位置](https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf#page=4)

## DigitalOcean · 保留集

研究截止 2024-11-04T23:59:59-05:00。單季與累計在同表，期間、期末和年份分三行。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2024 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [docn-prior 來源公告](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf)
- [docn-latest 來源公告](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf)
- prior_reported_in_period　第 3 欄，377,206 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 10 頁第 2 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　Three Months Ended                   Six Months Ended。[第 10 頁第 5 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　June 30,                           June 30,。[第 10 頁第 6 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　2024             2023               2024            2023。[第 10 頁第 7 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 倍率　(in thousands, except per share amounts)。[第 10 頁第 3 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 營收列　Revenue                                                                  $         192,476 $        169,814      $     377,206 $        334,948。[第 10 頁第 8 行](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
- reported_in_period　第 3 欄，575,690 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 7 頁第 2 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　Three Months Ended                Nine Months Ended。[第 7 頁第 5 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　September 30,                    September 30,。[第 7 頁第 6 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　2024            2023             2024            2023。[第 7 頁第 7 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 倍率　(in thousands, except per share amounts)。[第 7 頁第 3 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 營收列　Revenue                                                     $        198,484 $        177,062    $     575,690 $       512,010。[第 7 頁第 8 行](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
- prior　[$770 to $775 million](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
- prior_interim　[$196 to $197 million](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
- new　[$775 to $777 million](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=2)

- extract　completed。[模型原始 JSON](raw/formal/docn-extract.json)
  模型判讀　11 月公告調高了 2024 全年營收指引；8 月公告列有前次全年指引及第三季指引。依合併損益表的單季欄位，8 月時可引用第二季實績，11 月時可引用第二季及第三季實績。兩份公告均未單列第一季營收，故省略該季。
  - new　docn-latest:p0002 · [$775 to $777 million](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=2)
  - prior　docn-prior:p0005 · [$770 to $775 million](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
  - prior_interim　docn-prior:p0005 · [$196 to $197 million](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
  - reported_in_period　docn-prior:p0010 · [$ 192,476](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - reported_in_period　docn-latest:p0007 · [$ 198,484](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - prior_reported_in_period　docn-prior:p0010 · [$ 192,476](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
- astra　completed。[模型原始 JSON](raw/formal/docn-astra.json)
  模型判讀　以美元計，前次全年營收指引中點扣除上半年實績及當時的第三季指引中點，得出第四季隱含營收 772500000 − 377206000 − 196500000 = 198794000。最新全年指引中點扣除前九個月實績，得出 776000000 − 575690000 = 200310000，較前次上調 1516000 美元。
  - prior　docn-prior:p0005 · [Total revenue of $770 to $775 million.](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
  - prior_reported_in_period　docn-prior:p0010 · [$ 377,206](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - prior_interim　docn-prior:p0005 · [Total revenue of $196 to $197 million.](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=5)
  - new　docn-latest:p0002 · [Increasing total revenue guidance of $775 to $777 million.](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=2)
  - reported_in_period　docn-latest:p0007 · [$ 575,690](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 198794000 | 198794000 | 對 |
| 最新隱含 Q4 營收 | 200310000 | 200310000 | 對 |
| 隱含 Q4 差額 | 1516000 | 1516000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 198794000 | 198794000 | 對 |
| 最新隱含 Q4 營收 | 200310000 | 200310000 | 對 |
| 隱含 Q4 差額 | 1516000 | 1516000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 198794000 | 198794000 | 對 |
| 最新隱含 Q4 營收 | 200310000 | 200310000 | 對 |
| 隱含 Q4 差額 | 1516000 | 1516000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

- 新版 reported_in_period　公告 2024-11-04T23:59:59-05:00 · 財年 2024 · 第 3 欄 · 原始值 575,690 · 575690000 美元
  - 數值列　Revenue                                                     $        198,484 $        177,062    $     575,690 $       512,010。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　(in thousands, except per share amounts)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　(unaudited)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　Three Months Ended                Nine Months Ended。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　September 30,                    September 30,。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 表頭　2024            2023             2024            2023。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 倍率　(in thousands, except per share amounts)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
  - 幣別　Revenue                                                     $        198,484 $        177,062    $     575,690 $       512,010。[原文位置](https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf#page=7)
- 新版 prior_reported_in_period　公告 2024-08-08T23:59:59-04:00 · 財年 2024 · 第 3 欄 · 原始值 377,206 · 377206000 美元
  - 數值列　Revenue                                                                  $         192,476 $        169,814      $     377,206 $        334,948。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　(in thousands, except per share amounts)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　(unaudited)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　Three Months Ended                   Six Months Ended。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　June 30,                           June 30,。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 表頭　2024             2023               2024            2023。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 倍率　(in thousands, except per share amounts)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)
  - 幣別　Revenue                                                                  $         192,476 $        169,814      $     377,206 $        334,948。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf#page=10)

## Cloudflare · 保留集

研究截止 2024-11-07T23:59:59-05:00。兩個跨欄期間各有第二行截止日和第三行年份。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2024 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [net-prior 來源公告](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf)
- [net-latest 來源公告](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf)
- prior_reported_in_period　第 3 欄，779,598 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 4 頁第 2 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　Three Months Ended                   Six Months Ended。[第 4 頁第 5 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　June 30,                            June 30,。[第 4 頁第 6 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　2024              2023              2024              2023。[第 4 頁第 7 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 倍率　(in thousands, except per share data)。[第 4 頁第 3 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 營收列　Revenue                                                               $    400,996      $    308,494      $    779,598      $    598,669。[第 4 頁第 8 行](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
- reported_in_period　第 3 欄，1,209,680 × 1,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 4 頁第 2 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　Three Months Ended                  Nine Months Ended。[第 4 頁第 5 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　September 30,                      September 30,。[第 4 頁第 6 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　2024              2023              2024              2023。[第 4 頁第 7 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 倍率　(in thousands, except per share data)。[第 4 頁第 3 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 營收列　Revenue                                                               $    430,082      $    335,603      $   1,209,680     $    934,272。[第 4 頁第 8 行](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
- prior　[$1,657.0 to $1,659.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=2)
- prior_interim　[$423.0 to $424.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=1)
- new　[$1,661.0 to $1,662.0 million](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=2)

- extract　completed。[模型原始 JSON](raw/formal/net-extract.json)
  模型判讀　兩份公告均列出 2024 全年營收指引，8 月公告另列第三季指引。8 月公布時已有第二季實績，11 月公布時另有第三季實績，均取自合併損益表的單季營收欄。第一季營收僅能由半年累計額減去第二季金額推算，因此兩組實績均省略第一季。
  - new　net-latest:p0002 · [$1,661.0 to $1,662.0 million](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=2)
  - prior　net-prior:p0002 · [$1,657.0 to $1,659.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=2)
  - prior_interim　net-prior:p0001 · [$423.0 to $424.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=1)
  - reported_in_period　net-prior:p0004 · [$ 400,996](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - reported_in_period　net-latest:p0004 · [$ 430,082](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - prior_reported_in_period　net-prior:p0004 · [$ 400,996](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
- astra　completed。[模型原始 JSON](raw/formal/net-astra.json)
  模型判讀　以百萬美元計，前次全年營收指引中點扣除上半年實績及第三季指引中點，得出第四季隱含營收 1658 − 779.598 − 423.5 = 454.902。最新全年指引中點扣除前九個月實績，得出 1661.5 − 1209.680 = 451.820。因此第四季隱含營收下調 3.082 百萬美元。
  - prior　net-prior:p0002 · [For the full year fiscal 2024, we expect: • Total revenue of $1,657.0 to $1,659.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=2)
  - prior_reported_in_period　net-prior:p0004 · [$ 779,598](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - prior_interim　net-prior:p0001 · [For the third quarter of fiscal 2024, we expect: • Total revenue of $423.0 to $424.0 million](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=1)
  - new　net-latest:p0002 · [For the full year fiscal 2024, we expect: • Total revenue of $1,661.0 to $1,662.0 million](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=2)
  - reported_in_period　net-latest:p0004 · [$ 1,209,680](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 454902000.0 | 454902000.0 | 對 |
| 最新隱含 Q4 營收 | 451820000.0 | 451820000.0 | 對 |
| 隱含 Q4 差額 | -3082000.0 | -3082000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 454902000.0 | 454902000.0 | 對 |
| 最新隱含 Q4 營收 | 451820000.0 | 451820000.0 | 對 |
| 隱含 Q4 差額 | -3082000.0 | -3082000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 454902000 | 454902000.0 | 對 |
| 最新隱含 Q4 營收 | 451820000 | 451820000.0 | 對 |
| 隱含 Q4 差額 | -3082000 | -3082000.0 | 對 |
| 隱含 Q4 方向 | lowered | lowered | 對 |

- 新版 reported_in_period　公告 2024-11-07T23:59:59-05:00 · 財年 2024 · 第 3 欄 · 原始值 1,209,680 · 1209680000 美元
  - 數值列　Revenue                                                               $    430,082      $    335,603      $   1,209,680     $    934,272。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　(in thousands, except per share data)。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　(unaudited)。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　Three Months Ended                  Nine Months Ended。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　September 30,                      September 30,。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 表頭　2024              2023              2024              2023。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 倍率　(in thousands, except per share data)。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
  - 幣別　Revenue                                                               $    430,082      $    335,603      $   1,209,680     $    934,272。[原文位置](https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf#page=4)
- 新版 prior_reported_in_period　公告 2024-08-01T23:59:59-04:00 · 財年 2024 · 第 3 欄 · 原始值 779,598 · 779598000 美元
  - 數值列　Revenue                                                               $    400,996      $    308,494      $    779,598      $    598,669。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　(in thousands, except per share data)。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　(unaudited)。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　Three Months Ended                   Six Months Ended。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　June 30,                            June 30,。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 表頭　2024              2023              2024              2023。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 倍率　(in thousands, except per share data)。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)
  - 幣別　Revenue                                                               $    400,996      $    308,494      $    779,598      $    598,669。[原文位置](https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf#page=4)

## Okta · 保留集

研究截止 2024-12-03T23:59:59-05:00。期間分行，同一表頭把美元百萬與股數千分開聲明。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- What revenue for the fourth quarter of fiscal 2025 is embedded in the company's latest full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [okta-prior 來源公告](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf)
- [okta-latest 來源公告](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf)
- prior_reported_in_period　第 3 欄，1,263 × 1,000,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 7 頁第 2 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　Three Months Ended                  Six Months Ended。[第 7 頁第 5 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　July 31,                           July 31,。[第 7 頁第 6 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　2024            2023               2024            2023。[第 7 頁第 7 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 倍率　(dollars in millions, shares in thousands, except per share data)。[第 7 頁第 3 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 營收列　Total revenue                                                                    646               556            1,263           1,074。[第 7 頁第 11 行](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
- reported_in_period　第 3 欄，1,928 × 1,000,000 美元
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[第 7 頁第 2 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　Three Months Ended                 Nine Months Ended。[第 7 頁第 5 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　October 31,                        October 31,。[第 7 頁第 6 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　2024             2023             2024              2023。[第 7 頁第 7 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 倍率　(dollars in millions, shares in thousands, except per share data)。[第 7 頁第 3 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 營收列　Total revenue                                                                    665                584          1,928             1,658。[第 7 頁第 11 行](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
- prior　[$2.555 billion to $2.565 billion](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
- prior_interim　[$648 million to $650 million](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
- new　[$2.595 billion to $2.597 billion](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=2)

- extract　completed。[模型原始 JSON](raw/formal/okta-extract.json)
  模型判讀　兩次公告均列明 2025 財年全年總營收指引，8 月公告另列第三季指引。8 月時已公布第二季實績，12 月時又已公布第三季實績。兩份公告均未單獨列出第一季總營收，故省略該季。
  - new　okta-latest:p0002 · [$2.595 billion to $2.597 billion](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=2)
  - prior　okta-prior:p0002 · [$2.555 billion to $2.565 billion](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
  - prior_interim　okta-prior:p0002 · [$648 million to $650 million](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
  - reported_in_period　okta-prior:p0001 · [$646 million](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=1)
  - reported_in_period　okta-latest:p0001 · [$665 million](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=1)
  - prior_reported_in_period　okta-prior:p0001 · [$646 million](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=1)
- astra　completed。[模型原始 JSON](raw/formal/okta-astra.json)
  模型判讀　以百萬美元計，前次全年指引中點為 2560，扣除上半年實際營收 1263 及當時第三季指引中點 649，隱含第四季營收為 648。最新全年指引中點為 2596，扣除前九個月實際營收 1928，隱含第四季營收為 668，較前次上調 20。
  - prior　okta-prior:p0002 · [For the full year fiscal 2025, the Company now expects: • Total revenue of $2.555 billion to $2.565 billion](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
  - prior_reported_in_period　okta-prior:p0007 · [Total revenue 646 556 1,263 1,074](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - prior_interim　okta-prior:p0002 · [For the third quarter of fiscal 2025, the Company expects: • Total revenue of $648 million to $650 million](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=2)
  - new　okta-latest:p0002 · [For the full year fiscal 2025, the Company now expects: • Total revenue of $2.595 billion to $2.597 billion](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=2)
  - reported_in_period　okta-latest:p0007 · [Total revenue 665 584 1,928 1,658](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | 648000000.000 | 錯 |
| 最新隱含 Q4 營收 | unknown | 668000000.000 | 錯 |
| 隱含 Q4 差額 | unknown | 20000000.000 | 錯 |
| 隱含 Q4 方向 | unknown | raised | 錯 |

失分　單位、單位錯、引文不足。

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 648000000.000 | 648000000.000 | 對 |
| 最新隱含 Q4 營收 | 668000000.000 | 668000000.000 | 對 |
| 隱含 Q4 差額 | 20000000.000 | 20000000.000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 648000000 | 648000000.000 | 對 |
| 最新隱含 Q4 營收 | 668000000 | 668000000.000 | 對 |
| 隱含 Q4 差額 | 20000000 | 20000000.000 | 對 |
| 隱含 Q4 方向 | raised | raised | 對 |

失分　引文不足。

- 現版待查　reported_in_period · 累計表的幣別或單位無法核對
- 現版待查　prior_reported_in_period · 累計表的幣別或單位無法核對
- 新版 reported_in_period　公告 2024-12-03T23:59:59-05:00 · 財年 2025 · 第 3 欄 · 原始值 1,928 · 1928000000 美元
  - 數值列　Total revenue                                                                    665                584          1,928             1,658。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　(dollars in millions, shares in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　(unaudited)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　Three Months Ended                 Nine Months Ended。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　October 31,                        October 31,。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 表頭　2024             2023             2024              2023。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 倍率　(dollars in millions, shares in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
  - 幣別　Subscription                                                       $           651    $           569   $      1,886    $        1,614。[原文位置](https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf#page=7)
- 新版 prior_reported_in_period　公告 2024-08-28T23:59:59-04:00 · 財年 2025 · 第 3 欄 · 原始值 1,263 · 1263000000 美元
  - 數值列　Total revenue                                                                    646               556            1,263           1,074。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表名　CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　(dollars in millions, shares in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　(unaudited)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　Three Months Ended                  Six Months Ended。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　July 31,                           July 31,。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 表頭　2024            2023               2024            2023。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 倍率　(dollars in millions, shares in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)
  - 幣別　Subscription                                                       $           632    $          542     $      1,235    $      1,045。[原文位置](https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf#page=7)

## UiPath · 保留集

研究截止 2024-12-05T23:59:59-05:00。最新公告只列 Q4 獨立指引，沒有可用累計倒推的新全年營收。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [path-prior 來源公告](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf)
- [path-latest 來源公告](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf)
- 缺項核對　[For the fourth quarter fiscal 2025, UiPath expects](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=1)

- extract　completed。[模型原始 JSON](raw/formal/path-extract.json)
  模型判讀　9 月公告列出 2025 財年全年及第三季營收指引。12 月公告僅提供第四季營收指引，未直接列出更新後的全年金額，因此省略 new。實績採合併營運報表的單季總營收；第二季數字在兩次公告時均已公布，第三季數字於 12 月公布。兩份公告均未單列第一季總營收，因此省略該季。
  - prior　path-prior:p0002 · [Revenue in the range of $1.420 billion to $1.425 billion](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=2)
  - prior_interim　path-prior:p0002 · [Revenue in the range of $345 million to $350 million](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=2)
  - reported_in_period　path-prior:p0008 · [316,253](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - reported_in_period　path-latest:p0007 · [354,653](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - prior_reported_in_period　path-prior:p0008 · [316,253](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
- astra　completed。[模型原始 JSON](raw/formal/path-astra.json)
  模型判讀　缺少 2024 年 12 月 5 日公告中的 2025 財年全年營收指引區間或中點。
  - prior　path-prior:p0002 · [For the fiscal full year 2025, UiPath is updating its guidance and expects: Revenue in the range of $1.420 billion to $1.425 billion](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=2)
  - prior_reported_in_period　path-prior:p0008 · [Total revenue 316,253 287,310 651,365 576,898](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - prior_interim　path-prior:p0002 · [For the third quarter fiscal 2025, UiPath expects: Revenue in the range of $345 million to $350 million](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=2)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 423635000 | unknown | 錯 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

失分　營收口徑。

- 現版待查　new · figure not located
- 新版待查　new · figure not located
- 新版 reported_in_period　公告 2024-12-05T23:59:59-05:00 · 財年 2025 · 第 3 欄 · 原始值 1,006,018 · 1006018000 美元
  - 數值列　Total revenue                                            354,653          325,921             1,006,018         902,819。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 表名　Condensed Consolidated Statements of Operations。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 表頭　in thousands, except per share data。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 表頭　(unaudited)。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 表頭　Three Months Ended October 31,         Nine Months Ended October 31,。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 表頭　2024             2023                  2024            2023。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 倍率　in thousands, except per share data。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
  - 幣別　Licenses                                           $         137,174    $     148,068     $         389,553    $    401,407。[原文位置](https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf#page=7)
- 新版 prior_reported_in_period　公告 2024-09-05T23:59:59-04:00 · 財年 2025 · 第 3 欄 · 原始值 651,365 · 651365000 美元
  - 數值列　Total revenue                                              316,253         287,310        651,365         576,898。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表名　Condensed Consolidated Statements of Operations。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表頭　in thousands, except per share data。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表頭　(unaudited)。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表頭　Three Months Ended              Six Months Ended。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表頭　July 31,                       July 31,。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 表頭　2024           2023            2024           2023。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 倍率　in thousands, except per share data。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)
  - 幣別　Licenses                                                     $   112,251     $   119,300    $   252,379     $   253,339。[原文位置](https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf#page=8)

## Walmart · 保留集

研究截止 2024-11-19T23:59:59-05:00。季度及全年指引為固定匯率的淨銷售增率，無法定位當期合併營收美元。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [wmt-prior 來源公告](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf)
- [wmt-latest 來源公告](https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf)
- 缺項核對　[for Q3 and raises its outlook for FY25](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=1)

- extract　completed。[模型原始 JSON](raw/formal/wmt-extract.json)
  模型判讀　沃爾瑪明列第二季及第三季的合併營收，分別為 1,693 億及 1,696 億美元。兩次指引發布時第二季均已結束，第三季則僅在最新指引發布時已結束。兩份公告均未單列第一季營收。全年及第三季的銷售指引僅列固定匯率淨銷售額成長率，未列合併營收的美元金額或區間。
  - reported_in_period　wmt-prior:p0001 · [$169.3 billion](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=1)
  - reported_in_period　wmt-latest:p0001 · [$169.6 billion](https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf#page=1)
  - prior_reported_in_period　wmt-prior:p0001 · [$169.3 billion](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=1)
- astra　completed。[模型原始 JSON](raw/formal/wmt-astra.json)
  模型判讀　按固定匯率合併淨銷售額計算，以下金額均以十億美元為單位。8 月以全年及第三季指引中點推算，第四季為 642.6 × 1.0425 − 327.637 − 159.4 × 1.0375 = 176.896。11 月以更新後的全年指引中點扣除前九個月實績，得 642.6 × 1.0495 − 496.857 = 177.5517。兩者相減，第四季隱含淨銷售額上調 0.6557。
  - prior　wmt-prior:p0005 · [Net sales: $642.6 billion](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=5)
  - prior　wmt-prior:p0005 · [Consolidated net sales (cc) Increase 3.75% to 4.75%](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=5)
  - prior_reported_in_period　wmt-prior:p0012 · [Net sales (cc) $ 29,884 8.3% $ 168,084 4.9% $ 59,332 9.5% $ 327,637 5.3 %](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=12)
  - prior_interim　wmt-prior:p0005 · [Net Sales: $159.4 billion](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=5)
  - prior_interim　wmt-prior:p0005 · [Consolidated net sales (cc) Increase 3.25% to 4.25%](https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf#page=5)
  - new　wmt-latest:p0005 · [Net sales: $642.6 billion](https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf#page=5)
  - new　wmt-latest:p0005 · [Net sales (cc) Increase 4.8% to 5.1%](https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf#page=5)
  - reported_in_period　wmt-latest:p0012 · [Net sales (cc) $ 31,494 12.4% $ 169,220 6.1% $ 90,826 10.5% $496,857 5.6 %](https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf#page=12)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 176896000000 | unknown | 錯 |
| 隱含 Q4 差額 | 655700000 | unknown | 錯 |
| 隱含 Q4 方向 | raised | unknown | 錯 |

失分　引文不足、營收口徑。

- 現版待查　new · figure not located
- 現版待查　prior · figure not located
- 現版待查　prior_interim · figure not located
- 現版待查　reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 現版待查　prior_reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 新版待查　new · figure not located
- 新版待查　prior · figure not located
- 新版待查　prior_interim · figure not located
- 新版待查　reported_in_period · 表格延續或累計期間與財年無法唯一對應至同一數值欄。
- 新版待查　prior_reported_in_period · 表格延續或累計期間與財年無法唯一對應至同一數值欄。

## CDW · 保留集

研究截止 2024-10-30T23:59:59-04:00。公告列合併實績與調整後業績，缺第三季及全年可比美元營收指引。

### 題目

- What revenue for the fourth quarter of fiscal 2024 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2024 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2024 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [cdw-prior 來源公告](https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf)
- [cdw-latest 來源公告](https://s205.q4cdn.com/557255526/files/doc_financials/2024/q3/CDW-2024-9-30-Earnings-Release.pdf)
- 缺項核對　[announced second quarter 2024 results](https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf#page=1)

- extract　completed。[模型原始 JSON](raw/formal/cdw-extract.json)
  模型判讀　兩份公告均列明當季合併淨銷售額。7 月公告時可引用第二季金額，10 月公告時可引用第二季及第三季金額。第一季金額須由上半年累計額倒算，故略去。CDW 僅披露相對美國 IT 市場的成長目標，未提供 2024 全年或第三季的營收指引金額。
  - reported_in_period　cdw-prior:p0007 · [$ 5,423.4](https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf#page=7)
  - reported_in_period　cdw-latest:p0007 · [$ 5,516.6](https://s205.q4cdn.com/557255526/files/doc_financials/2024/q3/CDW-2024-9-30-Earnings-Release.pdf#page=7)
  - prior_reported_in_period　cdw-prior:p0007 · [$ 5,423.4](https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf#page=7)
- astra　completed。[模型原始 JSON](raw/formal/cdw-astra.json)
  模型判讀　缺少 7 月及 10 月各自的 2024 財年合併營收指引金額或區間，也缺少 7 月對第三季合併營收的指引金額或區間。
  - prior_reported_in_period　cdw-prior:p0006 · [$ 10,296.1](https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf#page=6)
  - reported_in_period　cdw-latest:p0006 · [$ 15,812.7](https://s205.q4cdn.com/557255526/files/doc_financials/2024/q3/CDW-2024-9-30-Earnings-Release.pdf#page=6)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

- 現版待查　new · figure not located
- 現版待查　prior · figure not located
- 現版待查　prior_interim · figure not located
- 現版待查　reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 現版待查　prior_reported_in_period · 指定單季數值無法唯一定位至合併營收欄
- 新版待查　new · figure not located
- 新版待查　prior · figure not located
- 新版待查　prior_interim · figure not located
- 新版待查　reported_in_period · 表格延續或累計期間與財年無法唯一對應至同一數值欄。
- 新版待查　prior_reported_in_period · 表格延續或累計期間與財年無法唯一對應至同一數值欄。

## Snowflake · 保留集

研究截止 2024-11-20T23:59:59-05:00。指引限產品收入，排除合併營收內的專業服務與其他。

### 題目

- What revenue for the fourth quarter of fiscal 2025 was embedded in the company's previous full-year outlook?
- By how much did the revenue embedded for the fourth quarter of fiscal 2025 change?
- Did the revenue embedded in the full-year outlook for the fourth quarter of fiscal 2025 rise, fall, or stay unchanged since the previous release?

### 點時原文與獨立確認欄位

- [snow-prior 來源公告](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf)
- [snow-latest 來源公告](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf)
- 缺項核對　[The following table summarizes our guidance for the full-year fiscal 2025](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=3)

- extract　completed。[模型原始 JSON](raw/formal/snow-extract.json)
  模型判讀　兩份公告的全年指引及先前的第三季指引均僅涵蓋產品營收，未提供合併總營收指引。公告直接列出第二季與第三季的合併總營收；先前公告發布時，第三季尚未結束。第一季的單季金額須由半年累計數扣除第二季金額推算，故省略。
  - reported_in_period　snow-prior:p0001 · [Revenue for the quarter was $868.8 million](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=1)
  - reported_in_period　snow-latest:p0004 · [Revenue for the quarter was $942.1 million](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=4)
  - prior_reported_in_period　snow-prior:p0001 · [Revenue for the quarter was $868.8 million](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=1)
- astra　completed。[模型原始 JSON](raw/formal/snow-astra.json)
  模型判讀　以百萬美元計，前次全年產品營收指引扣除上半年實績及當時第三季指引中點，得出第四季隱含營收 3356 − 1618.837 − (850 + 855) ÷ 2 = 884.663。最新全年指引扣除前九個月實績後為 3430 − 2519.119 = 910.881，因此第四季隱含產品營收上調 26.218 百萬美元。
  - prior　snow-prior:p0003 · [Product revenue $3,356](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=3)
  - prior_reported_in_period　snow-prior:p0013 · [$1,618,837](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=13)
  - prior_interim　snow-prior:p0003 · [Product revenue $850 - $855](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=3)
  - new　snow-latest:p0006 · [Product revenue(2) $3,430](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=6)
  - reported_in_period　snow-latest:p0015 · [$ 2,519,119](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=15)

### 現版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 新版 Harness

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | unknown | unknown | 對 |
| 隱含 Q4 差額 | unknown | unknown | 對 |
| 隱含 Q4 方向 | unknown | unknown | 對 |

### 純 Astra

| 指標 | 實際回覆 | 封存答案 | 數值或方向 |
|---|---:|---:|---|
| 前次隱含 Q4 營收 | 884663000 | unknown | 錯 |
| 隱含 Q4 差額 | 26218000 | unknown | 錯 |
| 隱含 Q4 方向 | raised | unknown | 錯 |

失分　營收口徑。

- 現版待查　new · figure not located
- 現版待查　prior · figure not located
- 現版待查　prior_interim · figure not located
- 新版待查　new · figure not located
- 新版待查　prior · figure not located
- 新版待查　prior_interim · figure not located
- 新版 reported_in_period　公告 2024-11-20T23:59:59-05:00 · 財年 2025 · 第 3 欄 · 原始值 2,639,626 · 2639626000 美元
  - 數值列　Revenue                                                                  $            942,094   $            734,173   $       2,639,626     $       2,031,790。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 表名　Condensed Consolidated Statements of Operations。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 表頭　(in thousands, except per share data)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 表頭　(unaudited)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 表頭　Three Months Ended October 31,               Nine Months Ended October 31,。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 表頭　2024                   2023                  2024                  2023。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 倍率　(in thousands, except per share data)。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
  - 幣別　Revenue                                                                  $            942,094   $            734,173   $       2,639,626     $       2,031,790。[原文位置](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf#page=12)
- 新版 prior_reported_in_period　公告 2024-08-21T23:59:59-04:00 · 財年 2025 · 第 3 欄 · 原始值 1,697,532 · 1697532000 美元
  - 數值列　Revenue                                                        $        868,823    $       674,018     $      1,697,532    $      1,297,617。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 表名　Condensed Consolidated Statements of Operations。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 表頭　(in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 表頭　(unaudited)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 表頭　Three Months Ended July 31,              Six Months Ended July 31,。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 表頭　2024               2023                 2024                2023。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 倍率　(in thousands, except per share data)。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
  - 幣別　Revenue                                                        $        868,823    $       674,018     $      1,697,532    $      1,297,617。[原文位置](https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf#page=9)
