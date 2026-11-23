# 案例納排與來源

資料以公開可取得性取樣。這份名單在正式推論前定下。對公司名比對工作區與本機既有評測案例索引，沒有把新批的發行人放入過去的回歸或訓練流程。發行人站點上的同日新聞稿及股東信，優先使用包含全年、Q3 指引與完整合併累計表的版本。

| 判定 | 發行人 | 依據 |
|---|---|---|
| 納入 | Dynatrace、GoDaddy、Informatica、Qualys、Vertex、Workiva、Yext | 兩側同口徑且全部所需數值及其財期、單位都可定位 |
| 排除 | C3 AI、Klaviyo、Semrush、CyberArk | 取得的公開新聞頁缺本任務所需的完整本期財務表 |
| 排除 | Olo、Box、Braze、Asana、nCino、Five9、BigCommerce、Domo、Rubrik、Nutanix、Datadog | 候選來源在本批回傳 403／429，未取得可驗證的成對全文 |
| 初篩排除 | Freshworks、DigitalOcean、Fastly、Sprout Social、PagerDuty、SentinelOne、Cloudflare | 已出現在既有專案案例 |

原始 URL 試查保存在鄰接 TSV。最終納入的來源、日期和完整轉寫以 [封存案例](../results/cases.json) 為準。Vertex 使用新聞頁直接連結的 PDF，Yext 使用新聞稿指向的股東信。Informatica 的頁面把早期季度附表嵌在折疊區，本批的轉寫只去掉這些折疊區，保留當期正文、營收表和附表。PDF 以 `pdftotext -layout` 轉寫。HTML 顯示來源和封存區塊／列，便於在完整文本核對。
