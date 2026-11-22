export const questionBank = [
  { title: "原訂與實際財報日", example: "asml-q3", question: "ASML 原訂哪天公布 2024 Q3 財報？實際發布日為何，為什麼提前？請引用官方行事曆和公告。" },
  { title: "接單季減與 EUV 占比", example: "asml-q3", question: "以財報表列金額，計算 ASML Q3 淨新增訂單季減幅及 EUV 占比。哪個數字只能視為近似？" },
  { title: "財報截止時點", example: "asml-q3", question: "2024 年 10 月 15 日能得知 ASML Q4 實際接單嗎？同一份證據能支持哪些 2025 年指引？" },
  { title: "供應鏈交易候選", example: "asml-q3", tab: "opportunities", question: "從首稿挑選未點名的供應鏈公司。請區分光學件供應、客戶採購及 DUV 同業，並列可啟動或推翻交易假說的公開訊號。" },
  { title: "出口許可與費用預估", example: "nvidia-h20", question: "NVIDIA 在 4 月 15 日申報了什麼？許可通知、申報日期以及最高 55 億美元費用預估分別代表什麼？" },
  { title: "H20 費用與毛利實績", example: "nvidia-h20", asOf: "2025-05-28T23:59:59Z", question: "以 NVIDIA 5 月 28 日財報比較 4 月費用預估和實際 H20 費用。請分別列出 GAAP、non-GAAP 與排除 H20 費用後的 non-GAAP 毛利率。" },
  { title: "H20 上游曝險", example: "nvidia-h20", tab: "opportunities", question: "年報具名哪些晶圓代工和記憶體公司？哪些關係只適用於 NVIDIA 整體供應鏈？請說明 H20 公司別曝險還缺什麼。" },
  { title: "High-NA 採購單", example: "intel-high-na", question: "2022 年的聯合公告涉及哪一款機型？採購單能確認到哪個階段，量產及收入認列還需要什麼證據？" },
  { title: "首批模組與機型差異", example: "intel-high-na", question: "ASML 說明 2023 年 12 月交付的是哪個型號、哪個階段？它和 2022 年採購的型號是否相同？" },
  { title: "設備商與客戶的公開訊號", example: "intel-high-na", tab: "opportunities", question: "針對 Intel 與首稿找到的供應鏈公司，各提出一項可公開查核的交付或量產訊號，並說明如何區分營收、資本支出及成本影響。" },
];

export const exampleLabels = {
  "asml-q3": "ASML Q3 財報",
  "asml-earnings": "ASML 盈利預測",
  "nvidia-h20": "NVIDIA H20",
  "intel-high-na": "Intel High-NA EUV",
};
