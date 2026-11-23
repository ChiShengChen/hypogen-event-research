# When Correct Deltas Hide the Wrong Numbers

Evidence and selective publication in cross-release financial question answering

## Abstract

Financial research often compares two estimates derived from different disclosures. Equal signed errors can cancel in a reported revision, so execution accuracy alone can credit incorrect operands. In archived development runs, six exact cancellations occurred despite incorrect earlier and later estimates. This motivates an evaluation that jointly scores each amount, its provenance, and the final difference.

We construct seven issuer-disjoint case pairs from fourteen complete earnings-release PDFs. Each operand is annotated for version, fiscal window, consolidation scope, units and source cells. We preregister three pilot issuers, four held-out issuers and two controlled edits. Astra and Claude Sonnet receive identical page-preserving source text. We compare direct answers and two deterministic publication policies, replaying the same extracted evidence for both policies. An oracle condition provides human source locators and leaves valuation and arithmetic to the model.

On the four held-out issuers, fieldwise verification retains five of five answerable fields for each model, compared with four of five under whole-answer verification. Neither policy emits an erroneous field in this sample. The entire gain is one independently recoverable estimate for Ziff Davis, where the earlier release omits quarterly guidance. Direct Astra also retains all five fields. Claude's raw direct result is two of five. A post-hoc serialization check raises it to five of five by decoding one extra layer of quotation marks around three numeric strings.

The sole correct numeric delta among raw held-out direct replies was supported by its source operands. The two controlled edits elicited all expected changes in both families. These results demonstrate that partial evidence can add a useful field under matched observed risk and leave the prevalence of hidden operand errors unresolved. With only two publishing issuers and zero observed false releases, the one-sided 95% issuer-level upper risk bound is 77.6%. Reliable low-risk claims require a larger, independently adjudicated corpus.

**Keywords**　numerical reasoning, evidence attribution, selective prediction, financial QA
