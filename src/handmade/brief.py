# The interview: learn what a designer needs to know, without guessing.
#
# 1. Read the request and keep only what it literally says (product, place, page type).
# 2. Ask only for what is still missing, with questions that fit the kind of product.
# 3. Push back once on vague answers, with examples that fit the product.
# 4. Remember the answers in handmade.system.json, so nobody is asked twice.
#
# Nothing is invented. A fact nobody gave stays missing and the prompt tells the AI
# to ask for it or leave a marked slot.

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

# ---------- domains ----------
# Each domain: trigger words, specific questions (key, question, example answer) and audience examples.

@dataclass(frozen=True)
class Domain:
    name: str
    words: tuple[str, ...]
    questions: tuple[tuple[str, str, str], ...]
    audience_examples: str


DOMAINS: tuple[Domain, ...] = (
    Domain("food", ("bakery", "cafe", "coffee", "restaurant", "food", "kitchen", "pizza", "butchery", "catering", "juice"),
           (("ordering", "How do customers buy: walk in, order ahead for pickup, delivery or a mix?",
             "walk in and WhatsApp orders for pickup"),
            ("best_sellers", "What are your three best sellers? Add prices if you know them.",
             "white bread KSh 65, queen cakes KSh 20, birthday cakes from KSh 1,500"),
            ("hours", "When are you open?", "Monday to Saturday, 6am to 8pm")),
           "students buying breakfast, families nearby, offices ordering for meetings"),
    Domain("retail", ("shop", "store", "duka", "boutique", "hardware", "pharmacy", "supermarket", "kiosk", "electronics"),
           (("catalogue", "Roughly how many products and in which main categories?", "about 200 items: phones, accessories, repairs"),
            ("buying", "How do people pay and get their items?", "M-Pesa, then delivery in Nairobi or pickup"),
            ("trust", "What makes people trust you over the shop next door?", "genuine products with a 6-month warranty")),
           "repeat customers on phones, first-time buyers comparing prices"),
    Domain("health", ("clinic", "hospital", "health", "pharmacy", "dental", "medical", "patient", "nurse", "doctor"),
           (("users_tasks", "What is the one task staff do most often on this screen?", "see who is waiting and for how long"),
            ("data", "Which numbers or records matter most?", "visits today, drugs below reorder level, staff on duty"),
            ("constraints", "Any rules about privacy or devices?", "shared desktops, no patient names on the overview")),
           "nurses at a reception desk, clinic managers on shared desktops"),
    Domain("education", ("school", "college", "university", "student", "parent", "teacher", "course", "fees", "tuition"),
           (("users_tasks", "What do people come here to do first?", "check the fee balance and pay"),
            ("payments", "How are payments made and confirmed?", "M-Pesa paybill, receipt by SMS"),
            ("calendar", "Which dates matter most to them?", "term opening dates and exam weeks")),
           "parents on phones with slow data, students on campus Wi-Fi"),
    Domain("finance", ("bank", "sacco", "loan", "savings", "insurance", "fintech", "wallet", "payments", "invest"),
           (("products", "Which products or accounts do people use most?", "savings, development loans, emergency loans"),
            ("trust", "What proves you are safe and regulated?", "licensed by SASRA, 12 years in operation"),
            ("tasks", "What is the first thing a member wants to do?", "check their balance and loan limit")),
           "matatu owners on Android phones, members checking balances monthly"),
    Domain("government", ("county", "government", "ministry", "council", "public", "permit", "license", "tender", "citizen"),
           (("services", "Which services do people come for most?", "business permits and land rates"),
            ("steps", "What documents or steps does the main service need?", "ID, KRA PIN, payment by M-Pesa"),
            ("languages", "Which languages must it support?", "English and Swahili")),
           "small business owners, journalists, suppliers checking tenders"),
    Domain("software", ("api", "saas", "developer", "sdk", "platform", "tool", "monitoring", "software", "app", "cloud"),
           (("problem", "What problem does it solve, in one sentence a user would say?", "we find out about failed payments before customers do"),
            ("proof", "What real proof can the page show: a demo, real numbers, customers who agreed to be named?",
             "a live status page and two named fintech customers"),
            ("pricing", "How is it priced?", "free up to 10,000 checks a month, then $49")),
           "backend engineers at fintechs, CTOs comparing tools"),
    Domain("transport", ("matatu", "transport", "logistics", "delivery", "courier", "taxi", "boda", "fleet", "travel"),
           (("service", "What exactly is offered and where?", "parcel delivery within Nairobi, same day"),
            ("pricing", "How is it priced?", "from KSh 250 per parcel by distance"),
            ("tracking", "What do customers check most often?", "where their parcel is and when it arrives")),
           "online sellers sending parcels, office workers ordering lunch"),
    Domain("events", ("event", "meetup", "conference", "festival", "concert", "wedding", "workshop", "hackathon"),
           (("when_where", "When and where is it?", "Saturday 14 March, Swahili Pot, Mombasa"),
            ("program", "What happens there? Name sessions or speakers if known.", "4 talks, a panel and a build session"),
            ("join", "How do people sign up and is it free?", "free, register on the page, 120 seats")),
           "students and junior developers, mostly on phones"),
    Domain("portfolio", ("portfolio", "resume", "cv", "personal site", "freelancer", "designer", "photographer"),
           (("work", "Which 3 projects should people see first and what did you do on each?", "a delivery app I built end to end"),
            ("role", "Which job or client are you aiming for?", "junior full-stack roles in Nairobi"),
            ("contact", "How should people contact you?", "email and LinkedIn")),
           "hiring managers skimming on laptops, recruiters on phones"),
    Domain("news", ("news", "magazine", "blog", "article", "newsletter", "journal", "publication", "story"),
           (("topic", "What is the piece or publication about?", "a long investigation into county water tenders"),
            ("format", "Which features does it need: pull quotes, footnotes, charts, photos?", "pull quotes, footnotes and two charts"),
            ("reading", "Where and how do people read it?", "on phones during commutes")),
           "readers on phones during commutes, researchers on laptops"),
    Domain("hospitality", ("hotel", "guest house", "airbnb", "lodge", "resort", "spa", "salon", "barber", "beauty"),
           (("offer", "What do you offer, with prices if known?", "haircuts from KSh 300, braiding from KSh 1,500"),
            ("booking", "How do people book?", "WhatsApp or walk in, no deposits"),
            ("place", "Where are you and what makes the place special?", "in the city centre, open late")),
           "students on phones, working people booking for the weekend"),
    Domain("agriculture", ("farm", "farmer", "agri", "crop", "dairy", "maize", "coffee farm", "cooperative", "livestock"),
           (("users_tasks", "What do farmers or buyers come here to do?", "check this week's prices"),
            ("data", "Which numbers matter most?", "price per kg by market and the change from last week"),
            ("access", "How do they get online?", "basic Android phones, often on 3G")),
           "smallholder farmers on basic phones, extension officers"),
)

GENERIC_DOMAIN = Domain("general", (), (("goal", "What should a person be able to do on this screen?", "book an appointment"),), "")


def detect_domain(text: str) -> Domain:
    low = text.lower()
    best, best_hits = GENERIC_DOMAIN, 0
    for d in DOMAINS:
        hits = sum(1 for w in d.words if re.search(rf"\b{re.escape(w)}s?\b", low))
        if hits > best_hits:
            best, best_hits = d, hits
    return best


# ---------- reading the request ----------

PLACE = re.compile(r"\b(?:in|at|near|around|based in|from)\s+((?:[A-Z][\w'’-]+)(?:\s+(?:[A-Z][\w'’-]+|Town|City))*)")
PRODUCT = re.compile(
    r"\bfor\s+(?:(?:a|an|my|our|the|this)\s+)?((?:[a-z][\w'’-]*\s+){0,5}?[a-z][\w'’-]*)"
    r"(?=\s+(?:in|at|near|that|which|who|with|where|so|for|to|and)\b|[,.;:!?]|$)", re.I)


def extract(request: str) -> dict[str, str]:
    # Facts the request states literally. Nothing is inferred.
    facts: dict[str, str] = {}
    m = PRODUCT.search(request)
    if m:
        product = m.group(1).strip()
        if product.lower() not in ("me", "us", "it", "them", "this", "that"):
            facts["product"] = product
    m = PLACE.search(request)
    if m:
        facts["place"] = m.group(1).strip()
    return facts


# ---------- vague answers ----------

VAGUE_WORDS = {
    "users", "user", "anyone", "everyone", "everybody", "people", "customers", "clients", "all", "public",
    "general public", "general", "amazing", "awesome", "nice", "good", "great", "cool", "modern", "beautiful",
    "best", "premium", "clean", "simple", "professional", "attractive", "stunning", "perfect", "wow",
    "anything", "whatever", "idk", "not sure", "n/a", "na", "none", "nothing", "very", "and", "a", "the",
    "screen", "page", "landing", "website", "site", "app", "design", "look", "looks", "looking", "it",
}


def is_vague(answer: str) -> bool:
    words = re.findall(r"[a-zA-Z'’]+", answer.lower())
    if not words:
        return True
    specific = [w for w in words if w not in VAGUE_WORDS]
    return len(specific) == 0 or (len(words) <= 2 and len(specific) <= 1 and len(specific[0]) < 4)


# ---------- the interview ----------

MOOD_CHOICES = ("editorial", "utilitarian", "warm", "playful", "technical", "luxury", "civic")


@dataclass
class Question:
    key: str
    text: str
    example: str
    follow_up: str
    optional: bool = False


@dataclass
class Facts:
    values: dict[str, str] = field(default_factory=dict)
    vague: dict[str, str] = field(default_factory=dict)  # key -> what the user said, when still vague
    source: dict[str, str] = field(default_factory=dict)  # key -> request, answer, saved

    def get(self, key: str) -> str:
        return self.values.get(key, "")

    def to_dict(self) -> dict:
        return {"answers": dict(self.values), "vague": dict(self.vague)}

    @classmethod
    def from_dict(cls, data: dict) -> "Facts":
        f = cls()
        for k, v in (data or {}).get("answers", {}).items():
            f.values[k] = v
            f.source[k] = "saved"
        f.vague = dict((data or {}).get("vague", {}))
        return f


def plan(request: str, facts: Facts, intent: str, suggested_mood: str, mood_reason: str = "") -> list[Question]:
    # The questions still worth asking, in the order a designer would ask them.
    domain = detect_domain(" ".join([request, facts.get("product")]))
    place = facts.get("place")
    where = f" in {place}" if place else ""
    qs: list[Question] = []
    if not facts.get("product"):
        qs.append(Question("product", "What is it and what does it do? One line.",
                           "a family bakery that sells bread and celebration cakes",
                           "Name the business or product and what it offers."))
    if not facts.get("audience"):
        example = domain.audience_examples or "who uses it most and on what device"
        qs.append(Question("audience", f"Who uses it most{where} and on what device?", example,
                           f"Be specific about who uses it most. For example: {example}."))
    goal_q = {
        "landing": ("goal", "What should a visitor do after reading this page?", "order a cake on WhatsApp"),
        "ecommerce": ("goal", "What should a shopper be able to do here?", "find a product, see the price, pay with M-Pesa"),
        "dashboard": ("goal", "What decision should this dashboard help someone make each day?", "what to reorder before stock runs out"),
        "form": ("goal", "What happens after someone submits it?", "they get a member number by SMS"),
        "docs": ("goal", "What should a reader be able to do after reading?", "read the weekly price report correctly"),
        "portfolio": ("goal", "What should a visitor do after looking?", "invite you to an interview"),
        "app": ("goal", "What is the main task on this screen?", "pay this term's fees"),
    }[intent]
    if not facts.get("goal"):
        qs.append(Question(goal_q[0], goal_q[1], goal_q[2], f"Name one concrete action. For example: {goal_q[2]}."))
    for key, text, example in domain.questions:
        if not facts.get(key):
            qs.append(Question(key, text, example, f"A specific answer helps most. For example: {example}.", optional=True))
    if not facts.get("mood"):
        qs.append(Question("mood", f"Which mood fits? {', '.join(MOOD_CHOICES)}. Press Enter for {suggested_mood}"
                            + (f" ({mood_reason})." if mood_reason else "."),
                           suggested_mood, "", optional=True))
    if not facts.get("reference"):
        qs.append(Question("reference", "Is there a website, magazine, place or object whose feel you like?",
                           "the chalkboard menus in old Nairobi bakeries", "", optional=True))
    return qs


Asker = Callable[[str], str]


def interview(request: str, facts: Facts, intent: str, suggested_mood: str, ask: Asker,
              say: Callable[[str], None], mood_reason: str = "") -> Facts:
    # Ask the planned questions. One follow-up for vague answers. Empty answers stay missing.
    for q in plan(request, facts, intent, suggested_mood, mood_reason):
        answer = ask(f"{q.text}\n  e.g. {q.example}\n> ").strip()
        if q.key == "mood":
            if not answer:
                facts.values["mood"] = suggested_mood
                facts.source["mood"] = "suggested, accepted"
            elif answer.lower() in MOOD_CHOICES:
                facts.values["mood"] = answer.lower()
                facts.source["mood"] = "answer"
            else:
                say(f"  '{answer}' is not one of the moods. Using {suggested_mood}; change it with --mood.")
                facts.values["mood"] = suggested_mood
                facts.source["mood"] = "suggested, accepted"
            continue
        if not answer:
            continue
        if is_vague(answer):
            better = ask(f"  {q.follow_up}\n> ").strip() if q.follow_up else ""
            if better and not is_vague(better):
                answer = better
            else:
                facts.vague[q.key] = better or answer
                continue
        facts.values[q.key] = answer
        facts.source[q.key] = "answer"
    return facts


QUESTION_LABELS = {
    "product": "What it is", "audience": "Who uses it and on what device", "goal": "What a person should do here",
    "place": "Where it is", "mood": "Mood", "reference": "A reference the user likes",
    "ordering": "How customers buy", "best_sellers": "Best sellers", "hours": "Opening hours",
    "catalogue": "Products and categories", "buying": "How people pay and collect", "trust": "Why people trust them",
    "users_tasks": "The most common task", "data": "The numbers that matter most", "constraints": "Privacy and device rules",
    "payments": "How payments work", "calendar": "Key dates", "products": "Main products", "tasks": "The first task",
    "services": "Main services", "steps": "Documents and steps", "languages": "Languages",
    "problem": "The problem it solves", "proof": "Real proof to show", "pricing": "Pricing",
    "service": "What is offered and where", "tracking": "What customers track", "when_where": "When and where",
    "program": "Program", "join": "How to join", "work": "Projects to show", "role": "Target role",
    "contact": "Contact", "topic": "Topic", "format": "Features needed", "reading": "Where people read it",
    "offer": "What is offered", "booking": "How people book", "access": "How people get online",
}


def missing_facts(request: str, facts: Facts, intent: str, suggested_mood: str) -> list[Question]:
    # Facts nobody gave. The prompt asks the AI to get them from the user, never to invent them.
    return [q for q in plan(request, facts, intent, suggested_mood) if q.key not in ("mood", "reference")]


def questions_for_ai(request: str, facts: Facts, intent: str, suggested_mood: str) -> list[dict]:
    # The open questions as data, for an AI tool to ask the user in its own words.
    out = []
    for q in plan(request, facts, intent, suggested_mood):
        out.append({"key": q.key, "question": q.text, "example": q.example, "required": not q.optional})
    return out
