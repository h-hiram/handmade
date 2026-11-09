# Turn a plain UI request into a prompt that makes an AI work like a designer.
#
# Works offline. No model or API key is needed. The output is plain text you
# paste into any AI tool: ChatGPT, Claude, Gemini, Cursor, v0, Lovable, Bolt.

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .profile import Profile
from .scan import Report
from .system import DEPTH_RULES, MOODS, DesignSystem, build_system, seed_from
from .tells import HYPE, REGISTRY, by_id

INTENTS: dict[str, tuple[str, ...]] = {
    "dashboard": ("dashboard", "admin", "analytics", "report", "kpi", "panel", "portal", "crm", "back office",
                  "management system", "back-office", "monitoring", "table"),
    "form": ("form", "signup", "sign up", "sign-up", "register", "registration", "login", "log in", "checkout",
             "onboarding", "wizard"),
    "ecommerce": ("shop", "store", "product page", "cart", "ecommerce", "e-commerce", "catalog", "catalogue"),
    "docs": ("docs", "documentation", "blog", "article", "guide", "knowledge base", "help center"),
    "portfolio": ("portfolio", "personal site", "resume", "cv", "about me"),
    "landing": ("landing", "homepage", "home page", "marketing", "website", "site", "hero", "launch", "waitlist", "page for"),
}

# When the user names no mood, the product's own words pick one before the screen type does.
MOOD_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("civic", ("county", "government", "ministry", "council", "public", "citizen", "school", "clinic", "hospital",
               "health", "sacco", "cooperative", "tender", "license", "permit", "regulatory", "ngo")),
    ("warm", ("bakery", "cafe", "coffee", "restaurant", "food", "kitchen", "farm", "shop", "duka", "kiosk", "salon",
              "barber", "market", "grocery", "family", "pharmacy", "hotel", "guest house", "craft")),
    ("editorial", ("news", "magazine", "blog", "article", "journal", "newsletter", "publication", "book", "story",
                   "research", "report")),
    ("playful", ("kids", "children", "game", "event", "meetup", "festival", "party", "music", "quiz")),
    ("luxury", ("luxury", "private banking", "jewel", "fashion", "spa", "resort", "wine", "boutique")),
    ("technical", ("api", "developer", "sdk", "devops", "monitoring", "database", "cli", "open source", "engineer",
                   "software", "saas", "cloud")),
    ("utilitarian", ("dashboard", "admin", "inventory", "erp", "crm", "analytics", "tracker", "back office")),
)


def mood_with_reason(text: str, intent: str) -> tuple[str, str]:
    low = text.lower()
    for mood, words in MOOD_HINTS:
        for w in words:
            if re.search(rf"\b{re.escape(w)}s?\b", low):
                return mood, f'the request mentions "{w}"'
    return DEFAULT_MOOD[intent], f"it is the usual mood for a {intent}"


def guess_mood(text: str, intent: str) -> str:
    return mood_with_reason(text, intent)[0]


DEFAULT_MOOD = {"dashboard": "utilitarian", "form": "civic", "ecommerce": "warm", "docs": "editorial",
                "portfolio": "editorial", "landing": "technical", "app": "utilitarian"}

LAYOUT_RULES: dict[str, tuple[str, ...]] = {
    "landing": (
        "No centered hero with a headline, a subline and two buttons. Left-align the headline.",
        "Show the product in the first screen: a real screenshot, a live demo or real data. Not an illustration.",
        "Do not lay features out as three equal cards. Vary the format from section to section.",
        "Build on a 12-column grid and use it asymmetrically, for example 7 and 5 columns.",
        "One call to action per screen. Make it say exactly what happens next.",
    ),
    "dashboard": (
        "No hero, no welcome banner, no greeting. The first thing on screen is the data the user came for.",
        "Left-aligned everything. Numbers right-aligned in tables with tabular figures.",
        "At most four summary figures in a row, each with a comparison (vs last period) or a small trend line.",
        "Tables are the main component. Sticky header, sortable columns, row height 36 to 44px.",
        "Filters live in one toolbar above the content, not in cards.",
        "Separate regions with the depth rule of the design system. No big or colored shadows.",
    ),
    "form": (
        "Single column. Labels above fields. Helper text under the label when the field needs it.",
        "Show errors inline, next to the field, in plain words that say how to fix them.",
        "Group related fields under a short heading. Mark optional fields, not required ones.",
        "Primary button aligned with the fields' left edge, labelled with the action (for example 'Create account').",
    ),
    "ecommerce": (
        "Product photography carries the page. Real products, consistent lighting and crop.",
        "Price, availability and delivery time visible without scrolling.",
        "No discount badges or countdown timers unless the offer is real.",
        "Product grids may be dense. Use 2 columns on phones, 3 to 4 on desktop, no hover zoom gimmicks.",
    ),
    "docs": (
        "Left navigation, content column of 60 to 75 characters and an 'on this page' outline on wide screens.",
        "Headings say what the section answers. Code blocks with copy buttons and real, runnable examples.",
        "No hero. The page opens with the answer.",
    ),
    "portfolio": (
        "Lead with the work, not a tagline. The first screen shows a real project.",
        "Each project gets a short case: problem, what you did, result with a number.",
        "Use an irregular grid that follows the shape of the work, not identical cards.",
    ),
    "app": (
        "Start from the main task. Put the most used action where the eye lands first.",
        "Left-aligned layout with a clear reading line. Center only short isolated moments.",
        "Group with spacing and the depth rule of the design system.",
    ),
}

# What separates a finished, premium UI from a plain one. Drawn from how product designers work:
# hierarchy through weight and color, every state designed, real controls instead of browser defaults.
CRAFT_COMMON: tuple[str, ...] = (
    "Make hierarchy with weight and color first, size second. Most text is body size. Labels use `muted`.",
    "Design every state: hover, focus, active, selected, disabled, empty, loading and error. "
    "Empty states say what will appear and give the next action.",
    "Style every control. No browser-default selects, date inputs, checkboxes or file inputs. "
    "Build custom ones from the system, keeping them accessible.",
    "Use one icon set at one stroke width and one size per context (16px inline, 20px in navigation). "
    "Icons sit on the text baseline and always have a label or aria-label.",
    "Numbers use tabular figures (`font-variant-numeric: tabular-nums`). Units and currency are smaller and `muted`.",
    "Transitions run 150 to 200ms with ease-out, on color, background, border, opacity or transform only.",
    "Align everything to the spacing scale. Repeated items share exact heights and baselines.",
)

CRAFT: dict[str, tuple[str, ...]] = {
    "dashboard": (
        "Frame: a left sidebar (240 to 264px) with grouped navigation, section labels and the active item on "
        "`accent-soft`. A top bar with page title, a search field with a keyboard hint and the user menu.",
        "A toolbar under the title: a segmented date range control (Today, 7 days, 30 days, Custom), "
        "filters as styled dropdown buttons and one primary action on the right.",
        "KPI row: label in `muted`, value large in the display or mono face, a delta with an arrow in success or "
        "danger and a sparkline drawn in SVG with the first chart color.",
        "One primary chart with real axes: light gridlines in `line`, labelled ticks, a legend that names series, "
        "and a tooltip style. Draw it in inline SVG or a chart library, never as a placeholder box.",
        "The main table: sticky header on `surface`, row hover tint, status pills (status color text on its `-soft` background), avatars or initials for people and a row action menu.",
        "Add one secondary panel that answers 'what needs me now': a queue, alerts or a short activity feed with times.",
        "Show who is signed in, when data was last updated and pagination or a row count under the table.",
    ),
    "form": (
        "Frame: a two-column layout on desktop. The form on the left (about 560px). A summary or help panel on the "
        "right with what the user gets, what they need ready and how long it takes.",
        "Long forms become steps with a progress indicator (step names, not only numbers). At most five fields per step.",
        "Each field: label above, helper text where it helps, a 44px tall input with a clear focus ring, "
        "inline validation after the field loses focus and an error message that says how to fix it.",
        "Use the right control: segmented buttons or radio cards for two to four choices, a styled select for more, "
        "input masks for phone and ID numbers and a styled file drop zone for uploads.",
        "A sticky footer bar with Back and the primary action. The primary button names the action.",
        "Reassure at the point of doubt: data use, fees and timing next to the field that raises them.",
    ),
    "landing": (
        "The first screen shows the real product or real photography, framed with care: a browser or device "
        "frame, a cropped detail or a composed photo. Never an empty gradient.",
        "Give each section its own format: a statement, a product detail with callouts, proof with real names, "
        "a comparison, a short FAQ. Do not repeat card grids.",
        "Use the display face at a confident size for one line per section. Everything else stays calm.",
        "Proof must be real: customer names, places and numbers the user supplied or marked slots.",
        "A footer with real contact details, hours and location or marked slots for them.",
    ),
    "ecommerce": (
        "Product cards: consistent image ratio, name, price in tabular figures, availability and a quiet add "
        "button. No hover zoom.",
        "A filter bar with styled chips and a sort control. Show the result count.",
        "Product page: large gallery with thumbnails, price and delivery near the buy button, a quantity stepper, "
        "and details in short sections.",
        "The cart shows totals, delivery cost and payment options (for example M-Pesa) before checkout.",
    ),
    "docs": (
        "Three columns on wide screens: navigation, content and an 'on this page' outline that tracks scroll.",
        "Code blocks with a language label, copy button and syntax colors from the chart series.",
        "Callouts for notes and warnings use `accent-soft` or a `-soft` status background, with an icon.",
    ),
    "portfolio": (
        "Large, carefully cropped project images. Captions in `muted` with role, year and result.",
        "A case study page: problem, approach, three to five key screens with notes and the outcome.",
    ),
    "app": (
        "A clear frame: navigation, a page header with title and primary action and the work area.",
        "Lists and tables use row hover, selection on `accent-soft` and inline actions.",
        "Dialogs and menus float with the `overlay` shadow over a dimmed backdrop.",
    ),
}

BANNED = (
    "Inter, Roboto, Arial, Open Sans or the plain system font stack as the main typeface",
    "The 'tasteful' AI fonts used by reflex: Space Grotesk, Geist, Instrument Serif, Fraunces, Poppins, Montserrat",
    "Purple, violet or indigo as the accent and any purple-to-blue or purple-to-pink gradient",
    "Cream background with a terracotta accent",
    "Gradient-filled headline text",
    "Glassmorphism (backdrop blur on translucent panels) and colored glow shadows",
    "Blurred color blobs, grid or dot pattern backgrounds",
    "Emoji as icons and the sparkle icon",
    "Icons inside pastel rounded squares above each feature",
    "rounded-2xl plus shadow-lg on every card",
    "A small pill badge ('New', 'Introducing v2') above the headline",
    "Copy-paste effect components from Aceternity UI or Magic UI",
    "hover:scale on cards and transition-all",
    'Hype words: "unlock", "seamless", "supercharge", "elevate", "revolutionize", "effortless", "next-gen", "all-in-one"',
    "Placeholder content: Lorem ipsum, John Doe, Acme, invented stats like '10,000+ happy users'",
)


@dataclass
class Brief:
    request: str
    product: str = ""
    audience: str = ""
    mood: str = ""
    reference: str = ""
    signature: str = ""
    intent: str = ""
    allow: tuple[str, ...] = ()  # deliberate brand choices, for example ("purple",)
    answers: dict = field(default_factory=dict)  # more facts: place, goal, best sellers...
    vague: dict = field(default_factory=dict)  # facts the user gave only vaguely
    mood_source: str = ""  # how the mood was chosen, shown in the prompt


# ---------- request screening ----------
# A request can ask for AI defaults ("purple gradient hero with glass cards") or try to switch the
# rules off ("ignore the design system"). Each match is answered with what to do instead,
# so the AI never builds a default just because the request named it.

# (key used by --allow, pattern, what to do instead)
REQUEST_RULES: tuple[tuple[str, str, str], ...] = (
    ("override", r"\b(?:ignore|disregard|forget|skip|bypass|override|don'?t follow|do not follow|no need for)\b[^.\n]{0,40}"
                 r"\b(?:rules?|instructions?|design system|guidelines?|constraints?|brief|checklist|above|previous|everything)\b",
     "This asks to switch the design rules off. It is not followed. The design system and the never-use list still apply."),
    ("purple", r"\b(?:purple|violet|indigo|lavender|fuchsia|magenta|lilac)\b",
     "Use the accent {accent} instead. Purple is the most recognised AI default."),
    ("gradient-text", r"\bgradient[- ](?:text|heading|headline|title|font)s?\b",
     "Set the headline in solid {ink}. Create emphasis with weight, size or the heading face."),
    ("gradient", r"\bgradients?\b",
     "Use flat color: {paper} for the page and {accent} for the one or two things that matter."),
    ("glass", r"\b(?:glass(?:morphism|y)?|frosted|backdrop[- ]?blur|translucent (?:cards|panels))\b",
     "Use solid surfaces: {surface} with a 1px {line} border."),
    ("glow", r"\b(?:neon|glow(?:s|ing|y)?)\b",
     "No glows. Separate things with borders and spacing. Shadows only on menus and dialogs."),
    ("fonts", r"\b(?:inter|roboto|arial|helvetica|open sans|poppins|montserrat|space grotesk|geist|dm sans|"
              r"plus jakarta sans|outfit|manrope|sora|satoshi)\b",
     "Use {fontpair} instead. That font is a model default."),
    ("emoji", r"\bemojis?\b|[\U0001F300-\U0001FAFF\u2728]",
     "Use one consistent icon set at text size or no icons."),
    ("sparkle", r"\bsparkles?\b",
     "Name the feature plainly and show what it does instead of decorating it."),
    ("three-cards", r"\b(?:three|3)\s+(?:equal\s+)?(?:feature\s+)?(?:cards|columns|boxes|tiles)\b|\b(?:feature|icon)\s+cards\b",
     "Present features as a list with real detail, a comparison or a screenshot with callouts. Not identical cards."),
    ("centered-hero", r"\bcent(?:er|re)d?\s+hero\b|\bhero\b[^.\n]{0,40}\b(?:two|2)\s+(?:buttons|ctas|calls to action)\b",
     "Left-align the headline and show the product itself on the first screen. One call to action."),
    ("bento", r"\bbento\b",
     "Use a simple list or a two-column layout unless the content really has different sizes of importance."),
    ("blobs", r"\b(?:blobs?|orbs?|blurr?ed (?:circles|shapes|background))\b",
     "Use a plain {paper} background. Let real content carry the visual weight."),
    ("effects", r"\b(?:aceternity|magic ?ui|spotlight effect|aurora|meteors|beams|particles|shimmer)\b",
     "No stock effects. If motion is needed, animate one real change in the interface."),
    ("vague", r"\b(?:modern|sleek|futuristic|stunning|beautiful|premium|eye[- ]catching|vibrant|trendy|slick|fancy|cool)\b",
     "Vague style words are not instructions. The look comes from the {mood} mood and the design system."),
    ("copy-brand", r"\b(?:like|similar to|inspired by)\s+(?:stripe|linear|vercel|apple|notion|airbnb|framer|figma|openai|shopify)\b"
                   r"|\b(?:stripe|linear|vercel|apple|notion)[- ]style\b",
     "Take that brand's care and attention to detail, not its layout, colors or fonts."),
    ("placeholder", r"\blorem ipsum\b|\b(?:placeholder|dummy|sample|fake) (?:text|content|copy|data)\b",
     "Write real copy for this product. Where a fact is unknown, leave a marked slot like [real figure]."),
    ("vanity", r"\btestimonials?\b|\bhappy (?:customers|users)\b|\b(?:social proof|trust badges?)\b",
     "Only real quotes and real figures with a source. Otherwise leave marked slots."),
    ("shadows", r"\b(?:soft|big|drop)\s+shadows?\b|\bshadows? (?:everywhere|on (?:all|every))\b|\brounded cards\b",
     "Use {radius_controls}px and {radius_containers}px radii only, borders for structure and shadows only on floating layers."),
)
_HYPE_RULE = ("hype", HYPE.pattern, "Write plain copy: what it does, for whom, with a concrete example.")

# Which never-use lines a deliberate --allow key removes.
ALLOW_UNBANS = {
    "purple": ("Purple, violet or indigo",), "gradient": ("Purple, violet or indigo",),
    "gradient-text": ("Gradient-filled headline",), "glass": ("Glassmorphism",), "glow": ("Glassmorphism",),
    "fonts": ("Inter, Roboto", "The 'tasteful' AI fonts"), "emoji": ("Emoji as icons",),
    "three-cards": ("Icons inside pastel",), "bento": (), "effects": ("Copy-paste effect",),
}


@dataclass
class RequestIssue:
    key: str
    quote: str
    instead: str


def screen_request(text: str, system: DesignSystem | None = None, allow: tuple[str, ...] = ()) -> list[RequestIssue]:
    # Find parts of a request that ask for AI defaults or try to disable the rules.
    fill = {}
    if system is not None:
        c = system.colors
        fill = {"accent": c["accent"], "ink": c["ink"], "paper": c["paper"], "surface": c["surface"], "line": c["line"],
                "display": system.display_font, "body": system.body_font, "mood": system.mood.name,
                "fontpair": system.body_font if system.display_font == system.body_font
                else f"{system.display_font} for headings and {system.body_font} for text",
                "radius_controls": system.radius[0], "radius_containers": system.radius[1]}
    allowed = {a.strip().lower() for a in allow}
    issues: list[RequestIssue] = []
    seen: set[str] = set()
    for key, pattern, instead in (*REQUEST_RULES, _HYPE_RULE):
        if key in seen or (key in allowed and key != "override"):
            continue
        m = re.search(pattern, text, re.I)
        if m:
            seen.add(key)
            try:
                msg = instead.format(**fill) if fill else re.sub(r"\{\w+\}", "the design system's value", instead)
            except (KeyError, IndexError):
                msg = instead
            issues.append(RequestIssue(key, m.group(0).strip(), msg))
    return issues


# Explicit page names outrank loose words: "landing page for my bakery shop" is a landing page.
EXPLICIT_PAGES: tuple[tuple[str, str], ...] = (
    ("landing", r"\blanding page|\bhome ?page\b|\bmarketing (?:page|site)\b"),
    ("dashboard", r"\bdashboards?\b|\badmin (?:panel|page|area)\b"),
    ("form", r"\bforms?\b|\bsign ?up\b|\bregistration\b|\bcheckout\b|\blog ?in (?:page|screen)\b"),
    ("ecommerce", r"\bonline (?:store|shop)\b|\be-?commerce\b|\bproduct (?:listing|page|grid)\b|\bcart\b"),
    ("docs", r"\bdocs\b|\bdocumentation\b|\bhelp (?:page|center|centre)\b|\barticle (?:page)?\b"),
    ("portfolio", r"\bportfolio\b"),
)


def detect_intent(text: str, product: str = "") -> str:
    # The screen type. The request's own page name wins; the product's words only break a tie.
    for source in (text, product):
        low = source.lower()
        for intent, pattern in EXPLICIT_PAGES:
            if re.search(pattern, low):
                return intent
        for intent, words in INTENTS.items():
            if any(re.search(rf"\b{re.escape(w)}\b", low) for w in words):
                return intent
    return "app"


def questions() -> list[tuple[str, str]]:
    # The questions a designer asks before starting. (field, question)
    moods = ", ".join(MOODS)
    return [
        ("product", "What is it, in one line? Name the product and what it does."),
        ("audience", "Who uses it and where? (for example: county health officers on office laptops)"),
        ("mood", f"Which mood fits? Choose one: {moods}"),
        ("reference", "One reference you like: a website, a magazine, a place or an object. (optional)"),
        ("signature", "One thing people should remember about this screen. (optional)"),
    ]


def _fmt_colors(system: DesignSystem) -> str:
    c = system.colors
    rows = [
        ("paper", "page background"), ("surface", "tinted regions, table headers, sidebars"),
        ("raised", "cards and panels that sit above the page"), ("line", "borders and dividers"),
        ("ink", "main text"), ("muted", "secondary text"), ("accent", "links, primary buttons, focus ring"),
        ("accent-strong", "hover and pressed state of accent elements"),
        ("accent-soft", "selected rows, active nav item, soft badges (use accent or ink text on it)"),
        ("on-accent", "text on accent buttons"),
        ("accent-2", "rare second accent"), ("success", "success states"),
        ("warning", "warning states"), ("danger", "errors and destructive actions"),
        ("success-soft", "background behind success text, for pills and notices"),
        ("warning-soft", "background behind warning text"), ("danger-soft", "background behind danger text"),
    ]
    lines = [f"- `{name}` {c[name]}: {use}" for name, use in rows if name in c]
    neutrals = [f"{k.split('-')[1]} {c[k]}" for k in c if k.startswith("neutral-")]
    if neutrals:
        lines.append("- Tinted grey ramp for icons, placeholders, disabled states and subtle fills: `neutral-` "
                     + ", ".join(neutrals) + ".")
    charts = [c[k] for k in c if k.startswith("chart-")]
    if charts:
        lines.append(f"- Chart series, in this order: {', '.join(charts)}. Each one is readable on paper (3:1 or more).")
    return "\n".join(lines)


def _system_section(system: DesignSystem, mood_note: str = "") -> str:
    cr = system.contrast_report()
    sizes = " / ".join(str(s) for s in system.type_scale)
    space = ", ".join(str(s) for s in system.spacing)
    parts = [
        "## Design system (use exactly this)",
        "",
        f"Mood: **{system.mood.name}**. {system.mood.summary}."
        + (f" ({mood_note[0].upper() + mood_note[1:]}.)" if mood_note else "")
        + (" Dark theme, matching the existing project." if system.dark else ""),
        "",
        "Typography:",
        f"- Headings: **{system.display_font}**. Body: **{system.body_font}**. Numbers and code: **{system.mono_font}**.",
        "- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.",
        f"- Type scale in px, ratio {system.mood.ratio}: {sizes}. Use only these sizes.",
        "- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.",
        "",
        "Color (hex):",
        _fmt_colors(system),
        f"- Checked contrast: ink on paper {cr['ink on paper']}:1, muted on paper {cr['muted on paper']}:1, "
        f"accent on paper {cr['accent on paper']}:1, text on accent {cr['text on accent']}:1.",
        "- The accent covers less than 10% of any screen. No gradients.",
        "",
        "Spacing and shape:",
        f"- Spacing scale in px: {space}. No other values.",
        f"- Corner radius: {system.radius[0]}px for controls, {system.radius[1]}px for containers. No other radii.",
        f"- Depth ({system.mood.depth}): {DEPTH_RULES[system.mood.depth]}",
        f"- Shadow `raised`: `{system.shadows['raised']}`.",
        f"- Shadow `overlay`: `{system.shadows['overlay']}`. No other shadows.",
        "",
        "Details that make it feel designed:",
        *(f"- {d}" for d in system.mood.details),
    ]
    if system.kept or system.replaced:
        parts += ["", "From the existing project:"]
        parts += [f"- Keep {k}." for k in system.kept]
        parts += [f"- Replace {r}." for r in system.replaced]
    return "\n".join(parts)


def _system_json(system: DesignSystem) -> str:
    return "\n".join([
        "## Machine-readable design system",
        "",
        "Save this block as `handmade.system.json` in the project root. "
        "`handmade check` uses it to verify that every font, color, size, spacing value and radius comes from this system.",
        "",
        "```json",
        json.dumps(system.to_dict(), indent=2),
        "```",
    ])


def _common_tail(intent: str, extra_bans: list[str], allow: tuple[str, ...] = ()) -> str:
    article = "an" if intent[0] in "aeiou" else "a"
    lines = [f"## Layout rules for {article} {intent}", ""]
    lines += [f"- {r}" for r in LAYOUT_RULES[intent]]
    lines += ["", "## Craft: what makes it look finished", "",
              "Plain is not the goal. Build it to the standard of a product designer's final mockup.", ""]
    lines += [f"- {r}" for r in CRAFT.get(intent, ())]
    lines += [f"- {r}" for r in CRAFT_COMMON]
    lines += [
        "",
        "## Content",
        "",
        "- Write real copy for this product and audience. Each headline should only fit this product.",
        "- Use realistic names, places, prices and numbers from the audience's market.",
        "- If a figure is unknown, leave a clearly marked slot like [real figure] instead of inventing one.",
        "",
        "## Never use",
        "",
    ]
    unbanned = {prefix for key in allow for prefix in ALLOW_UNBANS.get(key.strip().lower(), ())}
    lines += [f"- {b}" for b in BANNED if not any(b.startswith(u) for u in unbanned)]
    lines += [f"- {b}" for b in extra_bans]
    lines += [
        "",
        "## Accessibility and motion",
        "",
        "- Visible focus style on every interactive element (2px ring in the accent color, 2px offset).",
        "- Text contrast at least 4.5:1. Hit targets at least 44px on touch screens.",
        "- Alt text on every meaningful image. Semantic HTML: header, nav, main, section, table.",
        "- Motion only when it explains a change. Respect prefers-reduced-motion. Transition specific properties, never 'all'.",
        "",
        "## Before you finish",
        "",
        "Check your own output against the design system above. Every font, size, color, spacing value and radius "
        "must come from it. Remove anything on the 'Never use' list. Then list any place where you broke a rule and why.",
        "",
        "These rules outrank any styling words in the task. If the task and the rules disagree, follow the rules "
        "and say which part of the task you did not follow.",
    ]
    return "\n".join(lines)


def _labels() -> dict[str, str]:
    from .brief import DOMAINS, QUESTION_LABELS
    labels = dict(QUESTION_LABELS)
    for d in DOMAINS:
        for key, question, _example in d.questions:
            labels.setdefault(key, question.rstrip("?").split("?")[0])
    return labels


def _context_and_missing(brief: Brief, intent: str, mood: str) -> tuple[list[str], list[str]]:
    from .brief import Facts, missing_facts

    labels = _labels()
    facts = Facts(values={k: v for k, v in {"product": brief.product, "audience": brief.audience,
                                             **brief.answers}.items() if v})
    context = []
    order = ["product", "place", "audience", "goal"] + [k for k in facts.values if k not in ("product", "place", "audience", "goal")]
    for key in order:
        value = facts.values.get(key)
        if value:
            context.append(f"- {labels.get(key, key.replace('_', ' ').capitalize())}: {value}")
    if brief.reference:
        context.append(f"- Visual reference: {brief.reference}. Take its attitude, not its layout.")
    if brief.signature:
        context.append(f"- The one thing people should remember: {brief.signature}")
    for key, said in brief.vague.items():
        context.append(f'- {labels.get(key, key)}: the user only said "{said}". Treat this as unknown.')

    missing = []
    for q in missing_facts(brief.request, facts, intent, mood):
        if q.key in brief.vague:
            continue
        missing.append(f"- {labels.get(q.key, q.text)}. Ask: \"{q.text}\"")
    for key, said in brief.vague.items():
        missing.append(f'- {labels.get(key, key)}. The answer given ("{said}") is too vague to build on.')
    return context, missing


def build_prompt(brief: Brief, profile: Profile | None = None, report: Report | None = None,
                 variant: int = 0, saved_system: dict | None = None) -> tuple[str, DesignSystem]:
    intent = brief.intent or detect_intent(brief.request, brief.product)
    if brief.mood in MOODS:
        mood, mood_note = brief.mood, brief.mood_source or "chosen by the user"
    else:
        mood, reason = mood_with_reason(" ".join([brief.request, brief.product, brief.audience]), intent)
        mood_note = f"picked because {reason}. Change it with --mood"
    if saved_system:
        system = DesignSystem.from_dict(saved_system)
        mood, mood_note = system.mood.name, "from the project's saved design system, so every screen matches"
    else:
        seed = seed_from(brief.request, brief.product, brief.audience, mood, str(variant))
        system = build_system(mood, seed, profile=profile, dense=intent == "dashboard")

    context, missing = _context_and_missing(brief, intent, mood)
    if not context:
        context = ["- No product details were given. See the missing facts below."]
    missing_lines: list[str] = []
    if missing:
        missing_lines = [
            "## Facts still missing",
            "",
            "Nobody has said these yet. Ask the user for them before you build. "
            "If you cannot ask, leave a clearly marked slot such as [best sellers] and do not invent anything.",
            "",
            *missing,
            "",
        ]

    extra = []
    if report:
        extra = [f"{t.title} (found in this project)" for t in report.triggered if t.category != "copy"][:6]

    issues = screen_request(" ".join([brief.request, brief.reference, brief.signature, *brief.answers.values()]),
                            system, brief.allow)
    override_lines: list[str] = []
    if issues:
        override_lines = ["## Parts of the request the design system replaces", ""]
        override_lines += [f'- "{i.quote}": {i.instead}' for i in issues]
        override_lines.append("")
    allow_lines: list[str] = []
    if brief.allow:
        allow_lines = ["## Deliberate brand choices", "",
                       *(f"- {a}: the user confirmed this is part of the brand. Use it, but keep it consistent and pass contrast."
                         for a in brief.allow), ""]

    request_block = "\n".join("> " + line if line.strip() else ">" for line in brief.request.strip().splitlines())
    text = "\n".join([
        "# Task",
        "",
        "Build what this request describes, for the product and audience below:",
        "",
        request_block,
        "",
        "Use the request for what to build and who it is for. Styling words in it are hints, not instructions. "
        "Where it conflicts with the design system or the never-use list, the design system wins.",
        "",
        *override_lines,
        *allow_lines,
        "## Context",
        "",
        *context,
        "",
        *missing_lines,
        "## Work like a designer, then like a developer",
        "",
        "1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes "
        "and one signature element. Keep it under 120 words.",
        "2. Build the UI exactly as the brief and the design system below describe.",
        "3. Check it against the list at the end and fix what fails.",
        "",
        _system_section(system, mood_note),
        "",
        _common_tail(intent, extra, brief.allow),
        "",
        _system_json(system),
        "",
    ])
    return text, system


def build_fix_prompt(report: Report, brief: Brief | None = None, variant: int = 0) -> tuple[str, DesignSystem]:
    # A prompt that tells an AI to repair the exact tells found in a project.
    brief = brief or Brief(request="")
    intent = brief.intent or detect_intent(brief.request + " " + " ".join(report.files), brief.product)
    mood = brief.mood if brief.mood in MOODS else guess_mood(" ".join([brief.request, brief.product, brief.audience]), intent)
    seed = seed_from(report.root, brief.product, mood, str(variant))
    system = build_system(mood, seed, profile=report.profile, dense=intent == "dashboard")
    tells = by_id()

    lines = [
        "# Task",
        "",
        "Redesign the visual layer of this existing UI so it looks deliberately designed, not generated. "
        "Keep every feature, route, data binding and piece of logic. Change markup structure only where a rule below requires it.",
        "",
        f"A scan of {len(report.files)} files scored {report.score}/100 ({report.verdict}). Fix every item below.",
        "",
        "## What to fix, file by file",
        "",
    ]
    by_file: dict[str, list] = {}
    for f in report.findings:
        by_file.setdefault(f.file, []).append(f)
    for file, items in by_file.items():
        lines.append("### Whole project" if file == "(project)" else f"### {file}")
        for f in items:
            t = tells[f.tell]
            where = f"line {f.line}: " if f.line else ""
            lines.append(f"- {where}{t.title} ({f.detail}). Fix: {t.fix}")
        lines.append("")
    if brief.product:
        lines += ["## Context", "", f"- Product: {brief.product}"]
        if brief.audience:
            lines.append(f"- Audience: {brief.audience}")
        lines.append("")
    lines += [_system_section(system), "", _common_tail(intent, [], brief.allow), "", _system_json(system), ""]
    return "\n".join(lines), system


def list_bans() -> list[str]:
    return list(BANNED) + [t.title for t in REGISTRY]
