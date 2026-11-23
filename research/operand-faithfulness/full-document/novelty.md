# 研究缺口與可反駁的主張

論文範圍縮為兩件事。第一，在雙公告的數值差額任務中，用保持差額和改變差額的成對介入，辨別取證錯誤被算式掩蓋的頻率。第二，在同一份模型取證回傳上，測試有依賴關係的欄位能否各自發布。金融公告是第一個驗證場景。

| 原始論文 | 已有證據 | 本研究須額外證明 | 會使貢獻站不住腳的結果 |
|---|---|---|---|
| [FinQA](https://aclanthology.org/2021.emnlp-main.300/) | 金融表格與文字的專家標註和數值程式。論文指出單看執行結果會計入碰巧正確，程式一致也會排除等價解。 | 對同一雙公告任務做有方向且可重算的介入，分開報精確抵消、容差掩蓋及錯列引用。 | 量到的差異只來自任意容差，或有文件支持的等價路徑被誤判。 |
| [DocFinQA](https://aclanthology.org/2024.acl-short.42/) | 將 FinQA 題目擴至完整財報，研究長文證據檢索及數值推理。 | 對同一發行人的兩個公告版本標註不同時點的欄位及部分可答性。 | 控制文件長度及版面後，跨版本案例沒有實質增加另類失敗或資訊。 |
| [MultiHiertt](https://aclanthology.org/2022.acl-long.454/) | 多階層表格、文字、支撐事實與推理標註。 | 保留實體頁面、資產列欄及不同公告的披露歷史，以保持差額的改動測驗來源依賴。 | 模型在匹配的公告對上幾乎都選對原欄，或介入只測到改寫痕跡。 |
| [FinanceReasoning](https://aclanthology.org/2025.acl-long.766/) | 多類金融計算問題、細分難度與錯誤分析。 | 控制同一算式，交換原文位置、時期或單位，並量出等終值錯誤的頻率。 | 模型失分幾乎全是算術，給定人工欄位仍無改善且選欄指標沒有新增資訊。 |
| [FinLFQA](https://aclanthology.org/2025.findings-emnlp.908/) · [FinRAGBench-V](https://aclanthology.org/2025.emnlp-main.211/) | 金融長文的事實與中間運算歸因，以及原文件的視覺引用。 | 問證據歸因影響哪個可獨立發布的值，做同候選政策比較及控制區間。 | 等風險的部分發布沒有實用增益。 |
| [TempFinRAG](https://www.mdpi.com/2073-8994/18/9/1498) · [BuySideFlow](https://arxiv.org/abs/2611.12966) | 點時文件檢索及證據形態。BuySideFlow 已明確量到答案一致但時點違規。 | 把主張限於同一次算術內部的錯誤抵消，測原表格的跨公告取值及部分可答結果。 | 新方法僅重現一般的時點違規率，或去除時點違規後沒有可測的抵消。 |
| [Definitional or Computational?](https://aclanthology.org/2026.finnlp-1.1/) | XBRL 依賴圖、逐指標驗證、固定來源標記的 oracle，以及數值正確與來源歸因分離。 | 在未結構化公告中做保持終值／改變終值雙介入，以相同候選測逐欄發布政策。這篇是最接近的數值診斷對照。 | 只做 XBRL／人工固定事實的重算就足以取得相同結果，或規則只在已見版面成立。 |
| [Conformal Language Modeling](https://proceedings.iclr.cc/paper_files/paper/2024/hash/31421b112e5f7faf4fc577b74e45dab2-Abstract-Conference.html) · [AbstentionBench](https://proceedings.neurips.cc/paper_files/paper/2025/hash/fb122bfc3f0127a94ded048b5b03496f-Abstract-Datasets_and_Benchmarks_Track.html) | 已有部分組件驗證、風險校準及不可答題評測。 | 拆出有依賴關係的可答欄、不可答欄和不可計算差額，測同一取證候選能保留多少有效輸出。 | 留下的只是排除困難欄位的必然收益，或在先封存的風險界線下無法重現。 |

**目前研究定位**　部分發布在確定性且正確的證據結構上本來就能保留更多欄位。論文要驗證的是，在真實來源定位和語義核對有錯誤的條件下，覆蓋率與誤發布如何變動。不能從這輪觀測到的零誤報推得 conformal 保證。受控介入衡量輸出對證據的反應，無法直接觀察模型內部推理。
