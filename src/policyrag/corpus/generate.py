"""Generate the synthetic Velmora Assurance corpus + fact registry + golden set.

    python -m policyrag.corpus.generate --seed 42

Outputs
  data/raw/*.md          documents with YAML front matter (doc_id, doc_type, line, product, ...)
  data/facts.json        every fact, with the doc_ids that state it and acceptable answer variants
  data/golden_set.json   180 evaluation cases derived from the facts

The corpus is deliberately adversarial in realistic ways:
  * sibling products share wording but differ in values (Silver PPO vs Gold PPO)
  * amendments supersede values stated in older policy documents (stale-doc handling)
  * web vs mobile support articles give different limits for the same task
  * internal adjuster memos are confidential and must not leak to public queries
  * boilerplate legal text and no-fact noise articles dilute retrieval
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from policyrag.config import get_settings
from policyrag.corpus.catalog import (
    CLAIMS_ATTRS, COMPANY, INTERNAL_ATTRS, LINES, SUPPORT_TOPICS, TERMS_ATTRS, Attr, Line,
)
from policyrag.textnorm import match_variants

BOILERPLATE = [
    "In this document, \"you\" and \"your\" refer to the named insured shown in the declarations, and \"we\", \"us\" and \"our\" refer to {company}.",
    "Coverage is provided only for losses that occur during the policy period and only if the premium has been paid when due.",
    "Any provision of this document that conflicts with the laws of the state in which it was issued is amended to conform to those laws.",
    "No waiver or change of any provision of this document is valid unless made by written endorsement issued by {company}.",
    "If you or anyone covered under this document conceals or misrepresents a material fact, coverage may be voided from inception.",
    "Benefits are subject to all terms, conditions, limits and exclusions of this document, including any endorsements.",
    "We may examine any covered person, inspect damaged property, and request records reasonably needed to evaluate a claim.",
    "Legal action against {company} may not be brought unless there has been full compliance with all terms of this document.",
    "Where other insurance applies to the same loss, we pay only our share of the loss in proportion to our limit.",
    "Subrogation: if we make a payment, we are entitled to recover it from any party responsible for the loss.",
]
FRAUD = ("Any person who knowingly files a statement of claim containing false or misleading information may be guilty of "
         "insurance fraud. {company} reports suspected fraud to the appropriate authorities.")
NOISE_TOPICS = [
    ("Clearing Your Browser Cache", "If pages in the portal look out of date, clear your browser cache and cookies, then sign in again."),
    ("Supported Browsers", "The portal supports the two most recent versions of major desktop and mobile browsers."),
    ("App Crashes on Launch", "Update the app to the latest version and restart your device. Reinstalling the app does not delete your data."),
    ("Enabling Notifications", "Notifications can be enabled per category in Settings so you only receive the updates you want."),
    ("Accessibility Features", "The portal supports screen readers, high-contrast mode and keyboard navigation throughout."),
    ("Changing Your Email Address", "Update your email under Profile. A confirmation link is sent to the new address before the change applies."),
    ("Adding a Household Member to Your Account", "Household members can be invited to view policies; only the policyholder can make changes."),
    ("Downloading Tax Documents", "Tax forms for the prior year are posted in the Documents tab when they become available."),
    ("Understanding Your Declarations Page", "The declarations page lists your coverages, limits, covered persons and property, and the policy period."),
    ("Language Preferences", "You can set your preferred language for letters and emails in Profile settings."),
    ("Using Live Chat", "Live chat connects you with a support specialist. Transcripts are emailed to you after the chat ends."),
    ("Scam and Phishing Awareness", "Velmora will never ask for your password by phone or email. Report suspicious messages to our security team."),
    ("Printing Documents", "Use the print icon on any document page; documents are formatted for standard letter-size paper."),
    ("Managing Linked Devices", "You can review and remove devices signed in to your account from the Security page."),
    ("Updating Beneficiaries Overview", "Beneficiary changes for life policies require the beneficiary change form and the owner's signature."),
    ("Requesting a Policy Copy", "A full copy of your policy can be downloaded from the Documents tab at any time."),
    ("Reporting a Website Problem", "Use the feedback link in the footer to report a problem; include the page and the time it happened."),
    ("Paying by Phone", "Phone payments are accepted through our automated line; have your policy number and payment details ready."),
    ("Name Changes", "Name changes require supporting documentation such as a marriage certificate or court order."),
    ("Closing Your Online Account", "Closing your online account does not cancel any policy; contact support to cancel coverage."),
]


@dataclass
class Fact:
    fact_id: str
    kind: str                     # product | claims | terms | support | internal
    line: str | None
    product: str | None
    key: str
    label: str
    value: str
    raw: int | None
    match: list[str]
    doc_ids: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    lower_word: str = "lower"
    higher_word: str = "higher"
    confidentiality: str = "public"
    superseded_by: str | None = None


@dataclass
class Doc:
    doc_id: str
    title: str
    doc_type: str                 # policy | claims | support
    line: str | None
    product: str | None
    last_updated: date
    confidentiality: str
    sections: list[tuple[str, list[str]]]
    supersedes: str | None = None

    def to_markdown(self) -> str:
        fm = {
            "doc_id": self.doc_id, "title": self.title, "doc_type": self.doc_type,
            "line": self.line or "", "product": self.product or "",
            "last_updated": self.last_updated.isoformat(), "confidentiality": self.confidentiality,
            "supersedes": self.supersedes or "",
        }
        head = "---\n" + "\n".join(f"{k}: {json.dumps(v)}" for k, v in fm.items()) + "\n---\n\n"
        body = f"# {self.title}\n\n"
        for heading, paras in self.sections:
            body += f"## {heading}\n\n" + "\n\n".join(paras) + "\n\n"
        return head + body.rstrip() + "\n"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class Generator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.docs: list[Doc] = []
        self.facts: dict[str, Fact] = {}
        # line -> attr key -> product -> value(int)
        self.values: dict[str, dict[str, dict[str, int]]] = {}

    # ------------------------------------------------------------------ helpers
    def _date(self, start: date, span_days: int) -> date:
        return start + timedelta(days=self.rng.randrange(span_days))

    def _fill(self, template: str, **kw) -> str:
        return template.format(company=COMPANY, **kw)

    def _fact_for(self, line: Line, product: str, attr: Attr, kind: str, v: int) -> Fact:
        fid = f"{line.key}.{slug(product)}.{attr.key}"
        if fid not in self.facts:
            self.facts[fid] = Fact(
                fact_id=fid, kind=kind, line=line.key, product=product, key=attr.key, label=attr.label,
                value=attr.fmt(v), raw=v, match=match_variants(attr.fmt.__name__, v),
                questions=[self._fill(q, product=product, noun=line.noun) for q in attr.questions],
                lower_word=attr.lower_word, higher_word=attr.higher_word,
            )
        return self.facts[fid]

    def _sentence(self, line: Line, product: str, attr: Attr, v: int, doc_id: str, kind: str) -> str:
        fact = self._fact_for(line, product, attr, kind, v)
        if doc_id not in fact.doc_ids:
            fact.doc_ids.append(doc_id)
        tpl = self.rng.choice(attr.sentences)
        return self._fill(tpl, product=product, noun=line.noun, value=attr.fmt(v))

    def _new_doc_pool(self) -> None:
        """Boilerplate is drawn without replacement per document so paragraphs never repeat in one doc."""
        self._pool = self.rng.sample(BOILERPLATE, len(BOILERPLATE))

    def _boiler(self, n: int) -> list[str]:
        out = [self._fill(self._pool.pop()) for _ in range(min(n, len(self._pool)))]
        return out

    @staticmethod
    def _nice(v: float) -> int:
        step = 500 if v >= 5000 else 50 if v >= 500 else 5 if v >= 50 else 1
        return max(step, int(round(v / step) * step))

    # ------------------------------------------------------------------ values
    def assign_values(self) -> None:
        for line in LINES:
            per_attr: dict[str, dict[str, int]] = {}
            for attr in line.attrs + CLAIMS_ATTRS + TERMS_ATTRS:
                picks = self.rng.sample(attr.choices, len(line.products))
                per_attr[attr.key] = dict(zip(line.products, picks))
            self.values[line.key] = per_attr

    # ------------------------------------------------------------------ documents
    def policy_doc(self, line: Line, product: str) -> Doc:
        doc_id = f"policy-{line.key}-{slug(product)}"
        vals = self.values[line.key]
        sections: dict[str, list[str]] = {}
        for attr in line.attrs:
            sections.setdefault(attr.section, []).append(
                self._sentence(line, product, attr, vals[attr.key][product], doc_id, "product"))
        overview = [
            f"This document describes the {product} {line.name} {line.noun} offered by {COMPANY}. "
            f"It explains what is covered, what you pay, and the conditions that apply to your coverage.",
            "Please read it carefully and keep it with your declarations page.",
        ]
        body: list[tuple[str, list[str]]] = [("Overview", overview)]
        self._new_doc_pool()
        for sec, sents in sections.items():
            self.rng.shuffle(sents)
            body.append((sec, [" ".join(sents) + " " + self._boiler(1)[0]]))
        excl = self.rng.sample(line.exclusions, k=min(4, len(line.exclusions)))
        body.append(("Exclusions", [f"The {product} {line.noun} does not cover:\n\n" + "\n".join(f"- {e}" for e in excl)]))
        terms = [self._sentence(line, product, a, vals[a.key][product], doc_id, "terms") for a in TERMS_ATTRS]
        body.append(("General Terms", [" ".join(terms)] + self._boiler(2)))
        body.append(("Definitions and Conditions", self._boiler(3)))
        body.append(("Fraud Warning", [self._fill(FRAUD)]))
        return Doc(doc_id, f"{COMPANY} {product} {line.name.title()} {line.noun.title()} — Policy Document", "policy",
                   line.key, product, self._date(date(2024, 6, 1), 400), "public", body)

    def claims_doc(self, line: Line, product: str) -> Doc:
        doc_id = f"claims-{line.key}-{slug(product)}"
        vals = self.values[line.key]
        by_sec: dict[str, str] = {
            a.section: self._sentence(line, product, a, vals[a.key][product], doc_id, "claims") for a in CLAIMS_ATTRS
        }
        body = [
            ("How to File a Claim", [
                by_sec["How to File a Claim"],
                "Claims can be started in the online portal, in the mobile app, or by calling the claims line. "
                "You will receive a claim number by email within one business day.",
            ]),
            ("Required Documents", ["Please provide the following:\n\n" + "\n".join(f"- {d}" for d in line.required_docs)]),
            ("Processing Timeline", [by_sec["Processing Timeline"],
                                     "If we need more information, the timeline pauses until it is received."]),
            ("Appeals", [by_sec["Appeals"], "Appeals are reviewed by a person who was not involved in the original decision."]),
            ("Fraud Warning", [self._fill(FRAUD)]),
        ]
        return Doc(doc_id, f"{COMPANY} {product} — Claims Guide", "claims", line.key, product,
                   self._date(date(2024, 6, 1), 400), "public", body)

    def brochure_doc(self, line: Line, product: str) -> Doc:
        """Marketing one-pager restating two product facts (duplicate-source realism)."""
        doc_id = f"brochure-{line.key}-{slug(product)}"
        vals = self.values[line.key]
        attrs = self.rng.sample(line.attrs, 2)
        sents = [self._sentence(line, product, a, vals[a.key][product], doc_id, "product") for a in attrs]
        body = [
            ("Why Choose " + product, [f"{product} is designed for customers who want dependable {line.name} coverage "
                                       f"backed by {COMPANY}'s award-winning service."]),
            ("Highlights", [" ".join(sents)]),
            ("Get a Quote", ["Contact an agent or visit the portal to compare options and get a personalized quote."]),
        ]
        return Doc(doc_id, f"{product} at a Glance", "support", line.key, product,
                   self._date(date(2024, 9, 1), 300), "public", body)

    def amendment_docs(self) -> list[Doc]:
        out = []
        for line in LINES:
            for product in self.rng.sample(line.products, 3):
                attr = self.rng.choice(line.attrs)
                old = self.values[line.key][attr.key][product]
                used = set(self.values[line.key][attr.key].values())
                fresh = [c for c in attr.choices if c not in used]
                if fresh:
                    new = self.rng.choice(fresh)
                else:  # every catalog value is taken: move to a plausible nearby round number
                    factors = [0.8, 1.2, 1.25, 1.5, 0.75, 2.0, 0.6]
                    self.rng.shuffle(factors)
                    new = next((n for f in factors if (n := self._nice(old * f)) not in used and n != old),
                               old + 1)
                base_id = f"policy-{line.key}-{slug(product)}"
                eff = self._date(date(2026, 1, 1), 200)
                doc_id = f"amendment-{line.key}-{slug(product)}-{eff:%Y%m}"
                old_fact = self.facts[f"{line.key}.{slug(product)}.{attr.key}"]
                new_fid = old_fact.fact_id + "@amended"
                old_fact.superseded_by = new_fid
                self.facts[new_fid] = Fact(
                    fact_id=new_fid, kind="product", line=line.key, product=product, key=attr.key, label=attr.label,
                    value=attr.fmt(new), raw=new, match=match_variants(attr.fmt.__name__, new), doc_ids=[doc_id],
                    questions=old_fact.questions, lower_word=attr.lower_word, higher_word=attr.higher_word,
                )
                self.values[line.key][attr.key][product] = new
                body = [
                    ("Summary of Change", [
                        f"Effective {eff:%B %d, %Y}, the {attr.label} for the {product} {line.noun} changes from "
                        f"{attr.fmt(old)} to {attr.fmt(new)}. This amendment supersedes the corresponding provision "
                        f"of the {product} policy document. All other terms remain unchanged."]),
                    ("Who Is Affected", [f"All {product} policies issued or renewed on or after the effective date."]),
                ]
                out.append(Doc(doc_id, f"Amendment: {product} {attr.label.title()} Change ({eff:%B %Y})", "policy",
                               line.key, product, eff, "public", body, supersedes=base_id))
        return out

    def support_docs(self) -> list[Doc]:
        out = []
        for t in SUPPORT_TOPICS:
            doc_id = f"support-{t.slug}"
            paras = []
            for f in t.facts:
                fid = f"support.{f.key}"
                self.facts[fid] = Fact(fid, "support", None, None, f.key, f.key.replace("_", " "), f.value, None,
                                       list(f.match), [doc_id], list(f.questions))
                paras.append(f.sentences[0])
            paras += list(t.filler)
            self.rng.shuffle(paras)
            out.append(Doc(doc_id, t.title, "support", None, None, self._date(date(2025, 1, 1), 300), "public",
                           [("Overview", [f"This article explains {t.title.lower()}."]), ("Details", paras)]))
        for title, text in NOISE_TOPICS:
            out.append(Doc(f"support-{slug(title)}", title, "support", None, None, self._date(date(2024, 6, 1), 500),
                           "public", [("Overview", [text]), ("Need More Help?",
                                                             ["Contact support through live chat or by phone."])]))
        for line in LINES:
            for n, (heading, text) in enumerate([
                ("Getting Started", f"Welcome to {COMPANY} {line.name} coverage. Your documents are in the portal."),
                ("Making Changes", f"Most changes to {line.name} coverage can be requested in the portal and take effect at renewal."),
                ("Renewal Basics", f"Your {line.name} {line.noun} renews automatically unless you or we choose not to renew."),
            ]):
                out.append(Doc(f"support-{line.key}-guide-{n}", f"{line.name.title()} Coverage: {heading}", "support",
                               line.key, None, self._date(date(2024, 6, 1), 500), "public",
                               [("Overview", [text]), ("Tips", [self._fill(self.rng.choice(BOILERPLATE))])]))
        return out

    def internal_docs(self) -> list[Doc]:
        out = []
        for line in LINES:
            doc_id = f"internal-{line.key}-adjuster-guidelines"
            paras = []
            for key, label, choices, fmt, sent, q in INTERNAL_ATTRS:
                v = self.rng.choice(choices)
                fid = f"internal.{line.key}.{key}"
                self.facts[fid] = Fact(fid, "internal", line.key, None, key, label, fmt(v), v,
                                       match_variants(fmt.__name__, v), [doc_id],
                                       [q.format(line=line.name)], confidentiality="internal")
                paras.append(sent.format(line_title=line.name.title(), line=line.name, value=fmt(v)))
            out.append(Doc(doc_id, f"INTERNAL — {line.name.title()} Adjuster Guidelines", "claims", line.key, None,
                           self._date(date(2025, 3, 1), 300), "internal",
                           [("Purpose", ["For claims staff only. Do not share with customers."]),
                            ("Referral Rules", paras)]))
            out.append(Doc(f"internal-{line.key}-reserve-guidance", f"INTERNAL — {line.name.title()} Reserve Guidance",
                           "claims", line.key, None, self._date(date(2025, 3, 1), 300), "internal",
                           [("Purpose", ["For claims staff only."]),
                            ("Guidance", ["Set initial reserves based on the adjuster's best estimate of ultimate cost "
                                          "and revisit them whenever material new information is received."])]))
        return out

    def build(self) -> None:
        self.assign_values()
        for line in LINES:
            for p in line.products:
                self.docs += [self.policy_doc(line, p), self.claims_doc(line, p), self.brochure_doc(line, p)]
        self.docs += self.amendment_docs()
        self.docs += self.support_docs()
        self.docs += self.internal_docs()

    # ------------------------------------------------------------------ golden set
    def golden(self, n_simple=105, n_amend=15, n_compare=25, n_internal=10) -> list[dict]:
        rng = self.rng
        cases: list[dict] = []

        def fact_ref(f: Fact) -> dict:
            return {"fact_id": f.fact_id, "doc_ids": f.doc_ids, "match": f.match}

        def add(ctype, question, expected, facts, answerable=True, conf=("public",), line=None):
            cases.append({
                "id": f"g{len(cases) + 1:03d}", "type": ctype, "question": question, "expected_answer": expected,
                "must_contain": [f.match for f in facts], "facts": [fact_ref(f) for f in facts],
                "relevant_doc_ids": sorted({d for f in facts for d in f.doc_ids}),
                "answerable": answerable, "allowed_confidentiality": list(conf), "line": line,
                "expected_format": "PolicyAnswer.v1",
            })

        current = [f for f in self.facts.values() if f.superseded_by is None]
        amended = [f for f in current if f.fact_id.endswith("@amended")]
        public_simple = [f for f in current if f.kind in ("product", "claims", "terms", "support")
                         and not f.fact_id.endswith("@amended")]
        support = [f for f in public_simple if f.kind == "support"]
        others = [f for f in public_simple if f.kind != "support"]
        picks = support + rng.sample(others, n_simple - len(support))
        rng.shuffle(picks)
        for f in picks:
            subj = f.product or "Velmora"
            add("simple", rng.choice(f.questions), f"{f.label.capitalize()} for {subj}: {f.value}.", [f], line=f.line)

        for f in rng.sample(amended, min(n_amend, len(amended))):
            add("amendment", rng.choice(f.questions),
                f"{f.label.capitalize()} for {f.product}: {f.value} (per the latest amendment).", [f], line=f.line)

        comparable = {}
        for f in current:
            if f.kind in ("product", "claims", "terms") and f.raw is not None:
                comparable.setdefault((f.line, f.key), []).append(f)
        groups = [g for g in comparable.values() if len(g) >= 2]
        for _ in range(n_compare):
            g = rng.choice(groups)
            a, b = rng.sample(g, 2)
            lower = rng.random() < 0.5
            word = a.lower_word if lower else a.higher_word
            winner = (a if a.raw < b.raw else b) if lower else (a if a.raw > b.raw else b)
            line = next(l for l in LINES if l.key == a.line)
            q = rng.choice([
                f"Which has the {word} {a.label}: {a.product} or {b.product}?",
                f"Between the {a.product} and {b.product} {line.noun}s, which one has a {word} {a.label}?",
                f"Compare the {a.label} of {a.product} and {b.product} — which is {word}?",
            ])
            add("comparison", q, f"{winner.product} ({a.product}: {a.value}; {b.product}: {b.value}).", [a, b], line=a.line)

        internal = [f for f in current if f.kind == "internal"]
        for f in rng.sample(internal, min(n_internal, len(internal))):
            add("internal", f.questions[0], f"{f.label.capitalize()}: {f.value}.", [f],
                conf=("public", "internal"), line=f.line)

        # ---- unanswerable: should abstain and route to review
        fake_products = [("Diamond PPO", "health", "plan"), ("Bronze PPO", "health", "plan"), ("Titanium Auto", "auto", "policy"),
                         ("Motorcycle Plus", "auto", "policy"), ("HomeElite", "home", "policy"), ("Trip Ultra", "travel", "plan"),
                         ("Pet Platinum", "pet", "plan"), ("Term 40", "life", "policy")]
        for name, lk, noun in fake_products:
            line = next(l for l in LINES if l.key == lk)
            q = rng.choice(line.attrs).questions[0].format(product=name, noun=noun, company=COMPANY)
            add("unanswerable", q, "Not in the documents: no such product exists.", [], answerable=False, line=lk)
        missing_attr = {
            "health": "What is the adult dental cleaning copay for {p}?",
            "auto": "What is the gap insurance payout limit on {p}?",
            "home": "What is the identity theft restoration limit on {p}?",
            "travel": "What is the rental car collision limit on {p}?",
            "pet": "What is the dental illness sublimit on {p}?",
            "life": "What percentage of the death benefit can be accelerated on {p}?",
        }
        for lk, tpl in missing_attr.items():
            line = next(l for l in LINES if l.key == lk)
            for p in rng.sample(line.products, 2 if lk in ("health", "auto") else 1):
                add("unanswerable", tpl.format(p=p), "Not stated in the documents.", [], answerable=False, line=lk)
        for f in rng.sample(internal, 4):
            add("unanswerable", f.questions[0], "Not available to public users (internal document).", [],
                answerable=False, line=f.line)
        for q in ["Does Velmora accept cryptocurrency for premium payments?",
                  "What is Velmora's stock ticker symbol?",
                  "Who is the CEO of Velmora Assurance?",
                  "Does Velmora offer a rewards credit card?",
                  "What is the mailing address of Velmora's headquarters?"]:
            add("unanswerable", q, "Not stated in the documents.", [], answerable=False)
        return cases


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    data_dir = args.out or get_settings().data_dir
    raw = data_dir / "raw"
    if raw.exists():
        shutil.rmtree(raw)
    raw.mkdir(parents=True)

    g = Generator(args.seed)
    g.build()
    for d in g.docs:
        (raw / f"{d.doc_id}.md").write_text(d.to_markdown(), encoding="utf-8")
    facts = [vars(f) for f in g.facts.values()]
    (data_dir / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    golden = g.golden()
    (data_dir / "golden_set.json").write_text(json.dumps(golden, indent=2), encoding="utf-8")

    by_type: dict[str, int] = {}
    for c in golden:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    print(f"docs={len(g.docs)} facts={len(facts)} golden={len(golden)} {by_type}")


if __name__ == "__main__":
    main()
