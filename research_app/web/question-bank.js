export const questionBank = [
  {
    title: "截止時點的認證", example: "shutdown", action: "question",
    question: "截至 2025 年 1 月 15 日，能確認客戶 X 已認證乙公司的先進封裝產品嗎？當時可用的證據支持到哪裡？",
  },
  {
    title: "認證公開後的證據", example: "shutdown", action: "question", asOf: "2025-01-21T09:00:00+08:00",
    question: "截至台北時間 2025 年 1 月 21 日上午 9 點，能確認 X 的先進封裝認證嗎？這份公告也能證明轉單或出貨嗎？",
  },
  {
    title: "批量減半的 EPS", example: "shutdown", action: "scenario", lots: 300,
    question: "若本季全數交付並認列 300 批，增量營業利益和稀釋 EPS 各是多少？與 600 批母版差多少？",
  },
  {
    title: "損益兩平後的第一批", example: "shutdown", action: "scenario", lots: 401,
    question: "若本季全數交付並認列 401 批，增量營業利益和稀釋 EPS 各是多少？為何和 400 批不同？",
  },
  {
    title: "指引與實績", example: "demand", action: "question",
    question: "丙公司的公告確認了什麼？這能否證明當季實際出貨、營收或 EPS 已下滑？",
  },
  {
    title: "公開多空查核點", example: "demand", action: "question",
    question: "下一次何時有公開資料可查？用同一個指標和比較基準，說明哪種觀察會支持需求改善或持續轉弱。",
  },
  {
    title: "上游供應商曝險", example: "supply-chain", action: "question", tab: "opportunities",
    question: "第一份報告是否主動找出未被點名的上游公司？新澤設備交付改期可能如何傳導到零件需求與供應商收入？",
  },
  {
    title: "下游客戶與事件歸因", example: "supply-chain", action: "question", tab: "opportunities",
    question: "報告能找出哪一家下游客戶？既有設備採購紀錄是否足以證明它就是此次改期的客戶？",
  },
  {
    title: "替代來源的證據門檻", example: "supply-chain", action: "question", tab: "opportunities",
    question: "目前能確認具名替代供應商嗎？如果證據不足，需要查到哪類產品規格、客戶認證或產能資料？",
  },
  {
    title: "延伸交易機會", example: "supply-chain", action: "question", tab: "opportunities",
    question: "從原事件未點名的供應鏈公司中列出可觀察的交易候選。哪些公開訊號會觸發或推翻判斷？還缺哪些資料才能量化？",
  },
];

export const exampleLabels = {
  shutdown: "封裝線停工",
  demand: "需求指引下修",
  "supply-chain": "供應鏈曝險",
};
