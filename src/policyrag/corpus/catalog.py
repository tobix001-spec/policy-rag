"""Product catalog and attribute specs for the fictional insurer "Velmora Assurance".

Every number that appears in the corpus comes from here, which is what lets the
golden set know the exact answer and the exact documents that contain it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

COMPANY = "Velmora Assurance"


def money(v: int) -> str:
    return f"${v:,}"


def days(v: int) -> str:
    return f"{v} days"


def pct(v: int) -> str:
    return f"{v}%"


def hours(v: int) -> str:
    return f"{v} hours"


def months(v: int) -> str:
    return f"{v} months"


def years(v: int) -> str:
    return f"{v} years"


def calls(v: int) -> str:
    return f"{v} service calls"


def claims(v: int) -> str:
    return f"{v} claims"


@dataclass(frozen=True)
class Attr:
    key: str
    label: str                      # human label used in questions ("annual deductible")
    section: str                    # section heading the sentence is written under
    choices: tuple[int, ...]        # sampled without replacement per line -> distinct per product
    fmt: Callable[[int], str]
    sentences: tuple[str, ...]      # {product} {value}
    questions: tuple[str, ...]      # {product}
    lower_word: str = "lower"       # comparative used in comparison questions
    higher_word: str = "higher"


@dataclass(frozen=True)
class Line:
    key: str
    name: str                       # "health"
    noun: str                       # "plan" / "policy"
    products: tuple[str, ...]
    attrs: tuple[Attr, ...]
    exclusions: tuple[str, ...]
    required_docs: tuple[str, ...]
    support_topics: tuple[tuple[str, tuple[Attr, ...]], ...] = field(default=())


# ---------------------------------------------------------------- shared claims/terms attributes
CLAIMS_ATTRS: tuple[Attr, ...] = (
    Attr("claim_window", "claim filing deadline", "How to File a Claim",
         (30, 45, 60, 90, 120, 180, 365), days,
         ("Claims under the {product} {noun} must be submitted within {value} of the date of loss or service.",
          "You have {value} from the date of service to file a claim on your {product} {noun}.",
          "For {product}, the filing deadline is {value} after the loss occurs; late claims may be denied."),
         ("How long do I have to file a claim under {product}?",
          "What is the claim filing deadline for the {product} {noun}?",
          "Within how many days must a {product} claim be submitted?"),
         "shorter", "longer"),
    Attr("decision_sla", "claim decision time", "Processing Timeline",
         (10, 14, 15, 21, 30, 45), days,
         ("{company} issues a decision on complete {product} claims within {value} of receipt.",
          "Once all documents are received, a {product} claim decision is made within {value}.",
          "Our service standard for {product} is a coverage decision within {value} of a complete submission."),
         ("How long does it take to get a decision on a {product} claim?",
          "What is the claim decision timeframe for {product}?",
          "Within how many days will {company} decide a complete {product} claim?"),
         "faster", "slower"),
    Attr("appeal_window", "appeal deadline", "Appeals",
         (30, 45, 60, 90, 120, 180), days,
         ("If a {product} claim is denied, you may file a written appeal within {value} of the denial notice.",
          "Appeals for {product} must be received within {value} after you receive the explanation of benefits.",
          "The appeal window for {product} is {value} from the date on the denial letter."),
         ("How long do I have to appeal a denied {product} claim?",
          "What is the appeal deadline for {product}?",
          "If my {product} claim is denied, by when must I appeal?"),
         "shorter", "longer"),
)

TERMS_ATTRS: tuple[Attr, ...] = (
    Attr("grace_period", "premium grace period", "General Terms",
         (10, 15, 20, 30, 31, 45, 60), days,
         ("A grace period of {value} applies to late premium payments on the {product} {noun}.",
          "If a {product} premium is missed, coverage continues during a {value} grace period.",
          "{product} policyholders receive a {value} grace period before coverage lapses for non-payment."),
         ("What is the grace period for late premiums on {product}?",
          "How many days of grace period does {product} allow for missed payments?",
          "If I miss a {product} premium payment, how long before coverage lapses?"),
         "shorter", "longer"),
    Attr("cancel_notice", "cancellation notice period", "General Terms",
         (10, 14, 20, 30, 45, 60), days,
         ("{company} will provide at least {value} written notice before cancelling a {product} {noun}.",
          "Before cancelling your {product} coverage, we send written notice at least {value} in advance.",
          "The minimum cancellation notice for {product} is {value}."),
         ("How much notice does {company} give before cancelling a {product} {noun}?",
          "What is the cancellation notice period for {product}?",
          "How many days' notice will I get before my {product} coverage is cancelled?"),
         "shorter", "longer"),
)


def _a(key, label, section, choices, fmt, sentences, questions, lw="lower", hw="higher") -> Attr:
    return Attr(key, label, section, tuple(choices), fmt, tuple(sentences), tuple(questions), lw, hw)


HEALTH = Line(
    "health", "health", "plan",
    ("Bronze HMO", "Silver HMO", "Silver PPO", "Gold PPO", "Platinum PPO", "Catastrophic EPO"),
    (
        _a("deductible", "annual deductible", "Cost Sharing", (250, 500, 750, 1000, 1500, 2000, 3000, 4500, 6000), money,
           ("The annual deductible for the {product} plan is {value} per individual.",
            "Members enrolled in {product} must meet an individual annual deductible of {value} before coinsurance applies.",
            "{product} carries a {value} individual deductible each plan year."),
           ("What is the annual deductible for the {product} plan?",
            "How much is the individual deductible on {product}?",
            "What deductible do I have to meet on {product} before coverage kicks in?")),
        _a("oop_max", "out-of-pocket maximum", "Cost Sharing", (3000, 4000, 5500, 6500, 7500, 8200, 9100), money,
           ("The individual out-of-pocket maximum under {product} is {value} per plan year.",
            "Once a member's cost sharing reaches {value}, {product} pays 100% of covered in-network services for the rest of the year.",
            "{product} limits individual out-of-pocket spending to {value} annually."),
           ("What is the out-of-pocket maximum for {product}?",
            "How much is the most I would pay out of pocket in a year on {product}?",
            "What is the yearly out-of-pocket limit on the {product} plan?")),
        _a("specialist_copay", "specialist visit copay", "Cost Sharing", (20, 30, 40, 50, 65, 75, 90), money,
           ("In-network specialist visits on {product} have a {value} copay.",
            "A {value} copay applies to each in-network specialist office visit under {product}.",
            "Seeing an in-network specialist on the {product} plan costs a {value} copay per visit."),
           ("What is the specialist copay on {product}?",
            "How much does a specialist visit cost on the {product} plan?",
            "What copay do I pay to see an in-network specialist with {product}?")),
        _a("er_copay", "emergency room copay", "Cost Sharing", (100, 150, 200, 250, 300, 350, 500), money,
           ("Emergency room visits under {product} carry a {value} copay, waived if you are admitted.",
            "The {product} emergency room copay is {value} per visit; it is waived on inpatient admission.",
            "{product} members pay {value} for each emergency room visit unless admitted."),
           ("What is the ER copay for {product}?",
            "How much do I pay for an emergency room visit on {product}?",
            "What is the emergency room copay under the {product} plan?")),
        _a("coinsurance", "coinsurance rate", "Cost Sharing", (10, 15, 20, 25, 30, 40), pct,
           ("After the deductible, {product} members pay {value} coinsurance for covered in-network services.",
            "{product} coinsurance is {value} of the allowed amount once the deductible is met.",
            "The member coinsurance on {product} is {value} after the deductible."),
           ("What is the coinsurance rate for {product}?",
            "After meeting the deductible, what percentage do I pay on {product}?",
            "What coinsurance applies on the {product} plan?")),
    ),
    ("cosmetic surgery", "experimental or investigational treatments", "services received outside the United States except emergencies",
     "weight-loss programs", "long-term custodial care", "hearing aids", "routine dental care for adults", "fertility treatment"),
    ("itemized provider bill", "explanation of benefits from any other insurer", "member ID number", "diagnosis codes"),
)

AUTO = Line(
    "auto", "auto", "policy",
    ("Basic Liability", "Standard Auto", "Premier Auto", "Rideshare Auto", "Classic Car", "Fleet Commercial"),
    (
        _a("collision_deductible", "collision deductible", "Physical Damage Coverage", (250, 500, 750, 1000, 1500, 2000), money,
           ("Collision losses under the {product} policy are subject to a {value} deductible.",
            "The {product} collision deductible is {value} per incident.",
            "For collision claims, {product} applies a {value} deductible."),
           ("What is the collision deductible on {product}?",
            "How much is the deductible for a collision claim under {product}?",
            "If I crash my car, what deductible applies on the {product} policy?")),
        _a("comprehensive_deductible", "comprehensive deductible", "Physical Damage Coverage", (100, 250, 400, 600, 850, 1250), money,
           ("Comprehensive losses such as theft, hail and vandalism carry a {value} deductible on {product}.",
            "The comprehensive deductible for {product} is {value}.",
            "{product} applies a {value} deductible to comprehensive (non-collision) claims."),
           ("What is the comprehensive deductible on {product}?",
            "How much is the deductible for theft or hail damage under {product}?",
            "What deductible applies to non-collision damage on {product}?")),
        _a("rental_per_day", "rental car reimbursement", "Optional Coverages", (30, 35, 40, 50, 60, 75), money,
           ("{product} reimburses rental cars up to {value} per day while your vehicle is being repaired after a covered loss.",
            "Rental reimbursement on {product} is capped at {value} per day.",
            "While a covered vehicle is in the shop, {product} pays up to {value} per day toward a rental."),
           ("How much does {product} pay per day for a rental car?",
            "What is the daily rental reimbursement limit on {product}?",
            "Does {product} cover a rental car, and up to how much per day?")),
        _a("roadside_calls", "roadside assistance allowance", "Optional Coverages", (2, 3, 4, 5, 6, 8), calls,
           ("{product} includes up to {value} for roadside assistance per policy term.",
            "Roadside assistance on {product} is limited to {value} each policy term.",
            "Policyholders on {product} may use {value} of roadside assistance per term."),
           ("How many roadside assistance calls does {product} include?",
            "What is the roadside assistance limit on {product}?",
            "How many times can I use roadside assistance per term on {product}?"), "fewer", "more"),
        _a("bi_limit", "bodily injury liability limit", "Liability Coverage", (25000, 50000, 100000, 250000, 300000, 500000), money,
           ("Bodily injury liability under {product} is limited to {value} per person.",
            "The {product} policy provides bodily injury liability coverage of {value} per person.",
            "{product} pays up to {value} per injured person for bodily injury liability."),
           ("What is the bodily injury liability limit per person on {product}?",
            "How much bodily injury coverage per person does {product} provide?",
            "What is the per-person liability limit for injuries under {product}?")),
    ),
    ("racing or speed contests", "intentional damage", "wear and tear", "using the vehicle for delivery without an endorsement",
     "mechanical breakdown", "custom equipment over the scheduled limit", "drivers excluded by name"),
    ("police report number", "photos of the damage", "repair estimate", "other driver's insurance information"),
)

HOME = Line(
    "home", "home", "policy",
    ("HomeBasic", "HomeStandard", "HomePlus", "Renters Essential", "Condo Shield", "Landlord Protect"),
    (
        _a("home_deductible", "all-perils deductible", "Deductibles", (500, 1000, 1500, 2000, 2500, 5000), money,
           ("An all-perils deductible of {value} applies to each covered loss under {product}.",
            "The {product} policy carries a {value} deductible for covered property losses.",
            "Each property claim on {product} is subject to a {value} deductible."),
           ("What is the deductible on {product}?",
            "How much is the all-perils deductible for {product}?",
            "What deductible applies to a property claim under {product}?")),
        _a("water_backup", "water backup sublimit", "Special Limits", (5000, 7500, 10000, 15000, 20000, 25000), money,
           ("Water backup of sewers or drains is covered up to {value} under {product}.",
            "{product} includes a water backup sublimit of {value}.",
            "Sewer and drain backup losses on {product} are limited to {value}."),
           ("What is the water backup limit on {product}?",
            "How much does {product} cover for sewer or drain backup?",
            "Is sewer backup covered by {product}, and up to what amount?")),
        _a("ale_months", "additional living expense period", "Loss of Use", (3, 6, 9, 12, 18, 24), months,
           ("If your home becomes uninhabitable, {product} pays additional living expenses for up to {value}.",
            "Additional living expense coverage on {product} lasts up to {value}.",
            "{product} covers hotel and temporary housing costs for a maximum of {value}."),
           ("How long does {product} pay additional living expenses?",
            "For how many months will {product} cover temporary housing?",
            "What is the loss-of-use period under {product}?"), "shorter", "longer"),
        _a("jewelry_limit", "jewelry theft limit", "Special Limits", (1500, 2000, 2500, 5000, 7500, 10000), money,
           ("Theft of jewelry and watches is limited to {value} under {product} unless scheduled.",
            "{product} applies a {value} special limit to jewelry theft.",
            "Unscheduled jewelry is covered for theft up to {value} on {product}."),
           ("What is the jewelry theft limit on {product}?",
            "How much jewelry theft does {product} cover without scheduling?",
            "If my jewelry is stolen, how much will {product} pay?")),
    ),
    ("flood", "earthquake", "mold resulting from long-term leaks", "pest infestation", "home business property over $2,500",
     "intentional acts", "vacancy beyond 60 consecutive days"),
    ("photos or video of damaged property", "list of damaged items with estimated values", "receipts if available",
     "contractor repair estimate"),
)

TRAVEL = Line(
    "travel", "travel", "plan",
    ("Trip Lite", "Trip Standard", "Trip Premier", "Annual Multi-Trip", "Student Abroad", "Business Traveler"),
    (
        _a("trip_cancel", "trip cancellation limit", "Trip Protection", (2500, 5000, 7500, 10000, 15000, 25000), money,
           ("Trip cancellation benefits under {product} reimburse prepaid, non-refundable costs up to {value} per trip.",
            "{product} covers trip cancellation up to {value}.",
            "The maximum trip cancellation benefit on {product} is {value} per covered trip."),
           ("What is the trip cancellation limit on {product}?",
            "How much will {product} reimburse if I cancel my trip?",
            "What is the maximum trip cancellation benefit under {product}?")),
        _a("evac_limit", "medical evacuation limit", "Medical Coverage", (50000, 100000, 250000, 500000, 750000, 1000000), money,
           ("Emergency medical evacuation is covered up to {value} under {product}.",
            "{product} provides medical evacuation and repatriation coverage of up to {value}.",
            "The {product} plan includes {value} in emergency evacuation benefits."),
           ("What is the medical evacuation limit on {product}?",
            "How much emergency evacuation coverage does {product} include?",
            "Up to what amount does {product} cover medical evacuation?")),
        _a("baggage_delay", "baggage delay waiting period", "Baggage", (4, 6, 8, 12, 18, 24), hours,
           ("Baggage delay benefits on {product} begin once checked luggage is delayed more than {value}.",
            "{product} reimburses essential purchases after a baggage delay of {value}.",
            "Under {product}, a bag must be delayed at least {value} before the delay benefit applies."),
           ("How long must my bag be delayed before {product} pays?",
            "What is the baggage delay waiting period on {product}?",
            "After how many hours of baggage delay does {product} coverage start?"), "shorter", "longer"),
        _a("cfar_window", "cancel-for-any-reason purchase window", "Optional Upgrades", (7, 10, 14, 15, 20, 21), days,
           ("The cancel-for-any-reason upgrade for {product} must be purchased within {value} of the initial trip deposit.",
            "To add cancel-for-any-reason coverage to {product}, buy it within {value} of your first trip payment.",
            "{product} allows the cancel-for-any-reason upgrade only within {value} of the initial deposit."),
           ("When do I have to buy the cancel-for-any-reason upgrade for {product}?",
            "What is the CFAR purchase window for {product}?",
            "How soon after my deposit must I add cancel-for-any-reason to {product}?"), "shorter", "longer"),
    ),
    ("pre-existing conditions without the waiver", "extreme sports such as BASE jumping", "travel against government advisories",
     "pandemic-related border closures", "lost cash"),
    ("proof of travel dates", "receipts for prepaid costs", "carrier delay confirmation", "medical records for illness claims"),
)

PET = Line(
    "pet", "pet", "plan",
    ("Pet Accident Only", "Pet Wellness", "Pet Complete", "Senior Pet", "Exotic Pet", "Multi-Pet"),
    (
        _a("reimbursement", "reimbursement rate", "Benefits", (60, 70, 75, 80, 85, 90), pct,
           ("{product} reimburses {value} of eligible veterinary costs after the deductible.",
            "The reimbursement rate on {product} is {value}.",
            "Once the deductible is met, {product} pays back {value} of covered vet bills."),
           ("What is the reimbursement rate on {product}?",
            "What percentage of vet bills does {product} reimburse?",
            "How much of my vet bill does {product} pay back?")),
        _a("pet_annual_limit", "annual benefit limit", "Benefits", (3000, 5000, 7500, 10000, 15000, 20000), money,
           ("{product} pays up to {value} in benefits per policy year.",
            "The annual benefit limit for {product} is {value}.",
            "Covered claims on {product} are capped at {value} per year."),
           ("What is the annual limit on {product}?",
            "How much will {product} pay per year at most?",
            "What is the yearly benefit cap for {product}?")),
        _a("illness_wait", "illness waiting period", "Waiting Periods", (7, 10, 14, 15, 21, 30), days,
           ("Illness coverage under {product} begins after a {value} waiting period.",
            "{product} has a {value} waiting period for illnesses from the policy start date.",
            "New {product} policies have a {value} illness waiting period."),
           ("What is the illness waiting period for {product}?",
            "How long before illnesses are covered on {product}?",
            "How many days is the waiting period for illness on {product}?"), "shorter", "longer"),
        _a("max_enroll_age", "maximum enrollment age", "Eligibility", (6, 8, 9, 10, 12, 14), years,
           ("Pets can be newly enrolled in {product} up to {value} of age.",
            "The maximum enrollment age for {product} is {value}.",
            "{product} accepts new enrollments for pets up to {value} old."),
           ("What is the maximum enrollment age for {product}?",
            "Up to what age can I enroll my pet in {product}?",
            "Is there an age limit to sign up for {product}?"), "lower", "higher"),
    ),
    ("pre-existing conditions", "breeding and pregnancy costs", "cosmetic procedures such as tail docking", "grooming",
     "food and supplements unless prescribed"),
    ("itemized veterinary invoice", "medical records for the past 12 months", "pet's microchip number"),
)

LIFE = Line(
    "life", "life", "policy",
    ("Term 10", "Term 20", "Term 30", "Whole Life", "Universal Life", "Final Expense"),
    (
        _a("free_look", "free-look period", "Policyholder Rights", (10, 15, 20, 30, 31, 45), days,
           ("You may cancel {product} for a full refund within {value} of delivery (the free-look period).",
            "The {product} free-look period is {value} from the date you receive the policy.",
            "{product} provides a {value} free-look period for a full premium refund."),
           ("What is the free-look period for {product}?",
            "How long do I have to cancel {product} for a full refund?",
            "How many days is the free-look window on {product}?"), "shorter", "longer"),
        _a("max_face", "maximum face amount", "Coverage Amounts", (50000, 250000, 500000, 1000000, 2000000, 5000000), money,
           ("{product} may be issued with a face amount of up to {value}.",
            "The maximum face amount available on {product} is {value}.",
            "Coverage under {product} can be purchased up to {value}."),
           ("What is the maximum face amount for {product}?",
            "How much coverage can I buy with {product}?",
            "What is the highest death benefit available on {product}?")),
        _a("max_issue_age", "maximum issue age", "Eligibility", (55, 60, 65, 70, 75, 85), years,
           ("{product} can be issued to applicants up to {value} of age.",
            "The maximum issue age for {product} is {value}.",
            "Applicants must be no older than {value} to purchase {product}."),
           ("What is the maximum issue age for {product}?",
            "Up to what age can someone buy {product}?",
            "Is there an age limit to apply for {product}?")),
    ),
    ("suicide within the first two policy years", "material misrepresentation on the application", "acts of war",
     "death while committing a felony"),
    ("certified death certificate", "claimant statement form", "beneficiary identification"),
)

LINES: tuple[Line, ...] = (HEALTH, AUTO, HOME, TRAVEL, PET, LIFE)


# ---------------------------------------------------------------- company-wide support facts
@dataclass(frozen=True)
class SupportFact:
    key: str
    value: str
    match: tuple[str, ...]          # normalized acceptable answer tokens
    sentences: tuple[str, ...]
    questions: tuple[str, ...]


@dataclass(frozen=True)
class SupportTopic:
    slug: str
    title: str
    channel: str                    # web | mobile | phone | general
    facts: tuple[SupportFact, ...]
    filler: tuple[str, ...]


def sf(key, value, match, sentences, questions) -> SupportFact:
    return SupportFact(key, value, tuple(match), tuple(sentences), tuple(questions))


SUPPORT_TOPICS: tuple[SupportTopic, ...] = (
    SupportTopic("upload-web", "Uploading Claim Documents on the Web Portal", "web", (
        sf("upload_web_mb", "25 MB", ["25 mb", "25mb"],
           ["Each file uploaded through the web portal can be up to 25 MB."],
           ["What is the maximum file size for uploading claim documents on the web portal?",
            "How big can a file be when I upload claim documents on the website?"]),
        sf("upload_web_files", "20 files", ["20"],
           ["You can attach up to 20 files to a single claim from the web portal."],
           ["How many files can I attach to one claim on the web portal?"]),
    ), ("Accepted formats are PDF, JPG, PNG and HEIC.", "Uploads are virus-scanned before they reach an adjuster.")),
    SupportTopic("upload-mobile", "Uploading Claim Documents in the Mobile App", "mobile", (
        sf("upload_mobile_mb", "10 MB", ["10 mb", "10mb"],
           ["The mobile app accepts files up to 10 MB each; larger files should be sent through the web portal."],
           ["What is the maximum file size for uploads in the mobile app?",
            "How large can a photo be when I upload it in the Velmora app?"]),
    ), ("The app compresses photos automatically when possible.", "Uploads resume automatically if your connection drops.")),
    SupportTopic("password-reset", "Resetting Your Password", "web", (
        sf("reset_link_min", "30 minutes", ["30 minutes", "30 min"],
           ["Password reset links expire 30 minutes after they are sent."],
           ["How long is a password reset link valid?", "When does the password reset email link expire?"]),
        sf("lockout_attempts", "5 failed attempts", ["5 failed", "five failed", "5 attempts", "5 unsuccessful"],
           ["Accounts are locked after 5 failed sign-in attempts."],
           ["How many failed login attempts before my account is locked?"]),
        sf("lockout_minutes", "15 minutes", ["15 minutes", "15 min"],
           ["A locked account unlocks automatically after 15 minutes."],
           ["How long does an account lockout last?"]),
    ), ("Use a password of at least 12 characters.", "Never share your reset link with anyone.")),
    SupportTopic("two-factor", "Two-Factor Authentication", "web", (
        sf("otp_minutes", "10 minutes", ["10 minutes", "10 min"],
           ["One-time verification codes are valid for 10 minutes."],
           ["How long is a two-factor verification code valid?"]),
    ), ("You can receive codes by text message or an authenticator app.",)),
    SupportTopic("contact-hours", "Contacting Customer Support", "phone", (
        sf("phone_hours", "8 a.m. to 8 p.m. Eastern, Monday through Friday", ["8 a.m. to 8 p.m", "8am to 8pm", "8 am to 8 pm", "8 a.m.–8 p.m", "8am-8pm"],
           ["Phone support is available from 8 a.m. to 8 p.m. Eastern, Monday through Friday."],
           ["What are the phone support hours?", "When can I call Velmora customer service?"]),
        sf("callback_hours", "2 business hours", ["2 business hours", "two business hours"],
           ["If you request a callback, an agent will call you within 2 business hours."],
           ["How quickly will I get a callback after requesting one?"]),
    ), ("Live chat is available around the clock in the portal.", "Interpreter services are available on request.")),
    SupportTopic("id-cards", "Replacing an ID Card", "general", (
        sf("id_card_mail", "7 to 10 business days", ["7 to 10 business days", "7-10 business days", "7–10 business days"],
           ["Physical replacement ID cards arrive by mail in 7 to 10 business days."],
           ["How long does a replacement physical ID card take to arrive?"]),
    ), ("A digital ID card is available immediately in the app.",)),
    SupportTopic("payments", "Premium Payments and Discounts", "general", (
        sf("autopay_discount", "3%", ["3%", "3 percent"],
           ["Enrolling in autopay earns a 3% discount on your premium."],
           ["What discount do I get for enrolling in autopay?", "How much is the autopay discount?"]),
        sf("late_fee", "$15", ["$15", "15 dollars"],
           ["A late fee of $15 is charged when a payment is received after the due date."],
           ["What is the late payment fee?"]),
        sf("paperless_discount", "$2 per month", ["$2", "2 dollars"],
           ["Choosing paperless billing saves $2 per month."],
           ["How much is the paperless billing discount?"]),
    ), ("Payments can be made by bank transfer, debit card or credit card.", "Payment confirmation emails are sent within one hour.")),
    SupportTopic("address-change", "Updating Your Address", "general", (
        sf("address_days", "3 business days", ["3 business days", "three business days"],
           ["Address changes are processed within 3 business days."],
           ["How long does it take to process an address change?"]),
    ), ("A change of address may affect your premium for auto and home policies.",)),
    SupportTopic("direct-deposit", "Setting Up Direct Deposit for Claim Payments", "web", (
        sf("dd_days", "5 business days", ["5 business days", "five business days"],
           ["New direct deposit instructions take effect within 5 business days."],
           ["How long until direct deposit for claim payments takes effect?"]),
    ), ("Until direct deposit is active, payments are mailed by check.",)),
    SupportTopic("records", "Claim Records and Retention", "general", (
        sf("retention_years", "7 years", ["7 years", "seven years"],
           ["Velmora retains claim records for 7 years after a claim is closed."],
           ["How long does Velmora keep claim records?"]),
    ), ("You can download a copy of any closed claim from the portal.",)),
    SupportTopic("complaints", "Filing a Complaint", "general", (
        sf("complaint_days", "10 business days", ["10 business days", "ten business days"],
           ["Formal complaints receive a written response within 10 business days."],
           ["How long does Velmora take to respond to a formal complaint?"]),
    ), ("You may also contact your state insurance department.",)),
    SupportTopic("claim-status", "Checking Claim Status", "web", (
        sf("status_refresh", "every 4 hours", ["4 hours", "four hours"],
           ["Claim status in the portal refreshes every 4 hours."],
           ["How often does claim status update in the portal?"]),
    ), ("Status values are Received, In Review, Pending Information, Approved and Closed.",)),
    SupportTopic("status-mobile", "Claim Notifications in the Mobile App", "mobile", (
        sf("push_delay", "15 minutes", ["15 minutes", "15 min"],
           ["Push notifications for claim updates are sent within 15 minutes of a status change."],
           ["How fast do push notifications arrive after a claim status change?"]),
    ), ("Enable notifications in your phone's settings to receive updates.",)),
)

# Internal (confidential) adjuster guidelines: one memo per line, two facts each.
INTERNAL_ATTRS: tuple[tuple[str, str, tuple[int, ...], Callable[[int], str], str, str], ...] = (
    ("large_loss", "large-loss referral threshold", (15000, 25000, 40000, 50000, 75000, 100000), money,
     "{line_title} claims with an estimated loss above {value} must be referred to a senior adjuster.",
     "What is the large-loss referral threshold for {line} claims?"),
    ("siu_count", "SIU referral trigger", (2, 3, 4, 5, 6, 7), claims,
     "Refer a {line} policyholder to the Special Investigations Unit after {value} within any 12-month period.",
     "After how many claims in 12 months is a {line} policyholder referred to SIU?"),
)
