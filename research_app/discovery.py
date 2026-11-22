"""Bounded source discovery for opt-in event research."""
import hashlib
from datetime import date, datetime, time, timezone
from urllib.parse import urlsplit

from pydantic import Field

from .adapters import AdapterError
from .schema import Document, Nonempty, Schema

DISCOVERY_VERSION = 2


class Candidate(Schema):
    url: Nonempty
    published_on: date
    summary: Nonempty


class SearchPass(Schema):
    sources: list[Candidate] = Field(max_length=5)
    gaps: list[Nonempty] = Field(max_length=3)


def source_key(url):
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return None
    return parts.hostname.lower().removeprefix("www."), parts.path.rstrip("/") or "/", parts.query


def collect(event, adapter, *, question=None, unanswered=(), parent_evidence=()):
    if not callable(getattr(adapter, "search", None)):
        raise AdapterError("自動搜尋需要 RESEARCH_MODE=codex")
    context = {
        "event": event.event_text, "target": event.research_target,
        "horizon": event.research_horizon,
        "as_of": event.as_of.isoformat(), "allowed_domains": event.search_domains,
    }
    cutoff = event.as_of.astimezone(timezone.utc)
    domains = tuple(domain.lower().removeprefix("www.") for domain in event.search_domains)

    def allowed(key):
        return key is not None and any(key[0] == domain or key[0].endswith("." + domain) for domain in domains)

    sources = []
    log = []
    seen = {key for doc in event.documents if (key := source_key(doc.source))}
    used_ids = {doc.id for doc in event.documents}
    seen.update(key for item in parent_evidence if (key := source_key(item["source"])))
    used_ids.update(item["document_id"] for item in parent_evidence)
    shared = (
        "Use native web search. Search the allowed official domains only and use at most two search "
        "queries and two page opens per round. Cite the exact HTTPS URLs returned by the tool. "
        "Include only authoritative primary sources with an explicit publication date shown in the "
        "official disclosure. Do not use crawl, file, updated or inferred dates. Prefer documents "
        "public on or before the cutoff date. Summarize in Traditional Chinese, including any "
        "disclosed public metrics and their periods; avoid verbatim copying. "
    )
    tasks = [
        ("initial", "Find the issuer's original release or filing, the disclosed figures and relevant outlook. "
                    "List missing publication timing, corrections or public follow-up indicators as gaps."),
        ("follow_up", "Search specifically for a separate early release, timing clarification, correction "
                      "or supplemental notice. If none exists, check the most important unresolved gap, "
                      "such as a comparable publicly disclosed indicator from the issuer. Find distinct "
                      "documents; do not repeat already accepted URLs."),
        ("supply_chain", "Search proactively for named upstream suppliers and constrained inputs, named "
                         "downstream customers or end-market proxies, and competing firms or alternative "
                         "suppliers, even though the input did not ask about supply chain. Prefer dated issuer "
                         "disclosures or annual reports with actual counterparty names and specific products. "
                         "Where available report the direction of the link, concentration or operational "
                         "dependence, timing, relevant publicly disclosed metrics, and a listing venue "
                         "and ticker only when the primary disclosure explicitly identifies them. Distinguish a peer "
                         "from a qualified substitute, and general relationships from event exposure. "
                         "Search separately for the upstream, downstream and alternatives angles. Use up to "
                         "three search queries and three page opens in this round."),
    ]
    if question is not None:
        context.update({
            "question": question, "unanswered_gaps": list(unanswered),
            "existing_urls": sorted({item["source"] for item in parent_evidence if allowed(source_key(item["source"]))}),
        })
        tasks = [("question_follow_up",
                  "Find a new primary source that directly resolves the explicit research question or "
                  "one of its unresolved gaps. Look for archived investor calendars, prior releases, "
                  "and contemporaneous attachments when the question is about a scheduled date. "
                  "For a document with no cover date, use the issuer's dated publication announcement "
                  "that links to that exact document and search both URLs. Mention that provenance "
                  "in the summary. Do not use hindsight or later results to answer an earlier cutoff.")]
    gaps = []
    for stage, task in tasks:
        instruction = shared if stage != "supply_chain" else shared.replace(
            "at most two search queries and two page opens per round", "at most three search queries and three page opens per round"
        )
        result, trace = adapter.search(SearchPass, instruction + task, {
            **context, "prior_gaps": gaps, "accepted_urls": [doc.source for doc in sources],
            "previous_public_summaries": [doc.paragraphs["summary"] for doc in sources] if stage == "supply_chain" else [],
        })
        retrieved_at = datetime.now(timezone.utc)
        observed = {
            key for item in trace for hit in item.get("results", [])
            if (key := source_key(hit.get("url", "")))
        }
        counts = {"accepted": 0, "duplicate": 0, "unverified_url": 0, "after_cutoff": 0}
        accepted_ids = []
        for candidate in result.sources:
            key = source_key(candidate.url)
            if key not in observed or not allowed(key):
                counts["unverified_url"] += 1
                continue
            if key in seen:
                counts["duplicate"] += 1
                continue
            # A date-only disclosure is considered available at the end of its UTC calendar date.
            day_end = datetime.combine(candidate.published_on, time(23, 59, 59), timezone.utc)
            replay = event.search_mode == "historical_replay"
            obtained = day_end if replay else retrieved_at
            published = day_end if replay else min(day_end, retrieved_at)
            if obtained > cutoff or candidate.published_on > retrieved_at.date():
                counts["after_cutoff"] += 1
                continue
            doc_id = "web-" + hashlib.sha256(candidate.url.encode()).hexdigest()[:16]
            while doc_id in used_ids:
                doc_id += "-web"
            sources.append(Document(
                id=doc_id, source=candidate.url, kind="disclosure", text_format="summary",
                availability_basis="replay_day_end" if replay else "search_observed",
                published_at=published, obtained_at=obtained, paragraphs={"summary": candidate.summary},
            ))
            seen.add(key)
            used_ids.add(doc_id)
            accepted_ids.append(f"{doc_id}:summary")
            counts["accepted"] += 1
        gaps = result.gaps
        log.append({"stage": stage, "web_actions": len(trace), **counts, "accepted_evidence_ids": accepted_ids})
    return sources, {"version": DISCOVERY_VERSION, "mode": event.search_mode, "rounds": log}
