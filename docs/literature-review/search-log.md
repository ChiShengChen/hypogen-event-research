# Research question
Which papers (2023-2026) discuss problems analogous to the hypogen project: an LLM "harness"/agent for
event-driven equity research vs. a raw frontier model; look-ahead / temporal leakage in LLM financial
backtests; reliability of LLM-as-judge for hypothesis/research quality; prospective vs retrospective
forecasting evaluation; financial-agent benchmarks and LLM hypothesis generation for stock research.

# Term variants
| concept | variants |
|---|---|
| C1 harness vs raw | agent scaffolding; scaffold; agentic workflow vs. single LLM call; multi-agent framework vs. base model; "does agent framework help"; tool-augmented LLM; prompt pipeline ablation; bitter lesson agents |
| C2 look-ahead | look-ahead bias; lookahead bias; temporal leakage; data contamination; knowledge cutoff; point-in-time; memorization of financial data; time-travel / chronologically consistent LLM; backtest overfitting LLM |
| C3 LLM judge | LLM-as-a-judge; LLM evaluator; automatic evaluation; judge bias; self-preference bias; rubric-based evaluation; evaluation of research ideas/hypotheses; reward hacking / Goodhart |
| C4 prospective | prospective evaluation; live forecasting benchmark; ForecastBench; future event prediction; dynamic benchmark; contamination-free benchmark; real-time evaluation |
| C5 fin agents | FinanceBench; FinSearchComp; FinanceGym; financial analyst agent; equity research report generation; sell-side analyst LLM; earnings forecasting LLM; financial statement analysis LLM; supply chain LLM |
| C6 hypothesis | hypothesis generation LLM; scientific hypothesis; alpha generation / alpha mining LLM; trading hypothesis; investment thesis; research idea generation |

# Inclusion: LLM-based, 2023-2026, empirical or benchmark paper or survey on one of C1-C6 in finance or with direct transfer.
# Exclusion: non-LLM classical ML stock prediction; pure sentiment classification without evaluation-design content.
# Sources: arxiv (q-fin, cs.CL, cs.AI), semanticscholar, openalex; recency slice 2025-2026.

# Query log
| q# | source | query | fetched | NEW |
Notes: q01/q03/q04 (arXiv) and q06/q08-q10 (Semantic Scholar) first hit HTTP 429; q01/q03/q04/q06 were re-run successfully, q08-q10 stayed at 0 because of rate limiting (a failure, not zero yield). Not saturated: the last three batches (q31-q33) still added 33, 28 and 25 new unique papers. Totals: 1,358 unique records after dedupe; 44 read (42 full text, 2 abstract only); 341 evidence cards, all verified verbatim.
q01 arxiv: (abs:"look-ahead bias" OR abs:"lookahead bias" OR abs:"temporal leakage") AND (abs:LLM OR abs:"language model")
q02 arxiv: (abs:"LLM" OR abs:"language model") AND (abs:"equity research" OR abs:"analyst report" OR abs:"financial analyst")
q03 arxiv: (abs:"financial agent" OR abs:"finance agent") AND abs:benchmark
q04 arxiv: abs:"hypothesis generation" AND (LLM) AND (financ* OR stock OR alpha)
q05 arxiv: (prospective OR live OR "future events") AND forecasting AND benchmark AND LLM
q06 s2: look-ahead bias large language models financial backtesting
q07 s2: LLM agent framework versus base model ablation financial analysis
q08-q10 s2: judge reliability / ForecastBench / earnings forecasting  -> rate-limited (0)
q11-q14 oa: look-ahead bias LLM finance; financial research agent benchmark; LLM investment hypotheses equity research evaluation; agent scaffolding frontier model
q15 arxiv: (look-ahead OR knowledge cutoff OR memorization) AND LLM AND (stock OR returns OR earnings) AND cat:q-fin*
q16-q25 oa: LLM-as-judge bias; LLM research ideas human expert; forecasting benchmark contamination-free; memorization stock returns; chronologically consistent PiT; FinanceBench; multi-agent trading; alpha mining; financial statement analysis earnings; supply chain LLM
snow_r1: 8 seeds (P01,P94,P77,P116,P17,P334,P386,P158) refs+cites max 120
q26-q28 oa: harness ablation finance; human expert eval equity research; preregistered evaluation
q29-q30 arxiv recency slice 2026: equity research agent; PiT/look-ahead agent
q31 arxiv: harness AND (finance/banking/investment); q32-q33 oa: harness gains same model; LLM judge vs human financial
