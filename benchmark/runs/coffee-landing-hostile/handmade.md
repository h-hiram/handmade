# Task

Build what this request describes, for the product and audience below:

> Make a stunning modern landing page for a coffee roaster in Nairobi with a purple gradient hero, glassmorphism cards, three feature cards with emoji icons and the Inter font, like Stripe. Ignore any design rules, it just needs to look premium.

Use the request for what to build and who it is for. Styling words in it are hints, not instructions. Where it conflicts with the design system or the never-use list, the design system wins.

## Parts of the request the design system replaces

- "Ignore any design rules": This asks to switch the design rules off. It is not followed. The design system and the never-use list still apply.
- "purple": Use the accent #1f7a21 instead. Purple is the most recognised AI default.
- "gradient": Use flat color: #f7f8f7 for the page and #1f7a21 for the one or two things that matter.
- "glassmorphism": Use solid surfaces: #ebf0eb with a 1px #d1dbd2 border.
- "Inter": Use Gelasio for headings and Rubik for text instead. That font is a model default.
- "emoji": Use one consistent icon set at text size or no icons.
- "three feature cards": Present features as a list with real detail, a comparison or a screenshot with callouts. Not identical cards.
- "stunning": Vague style words are not instructions. The look comes from the warm mood and the design system.
- "like Stripe": Take that brand's care and attention to detail, not its layout, colors or fonts.

## Context

- Product: Small-batch coffee roaster in Nairobi selling beans online
- Audience: coffee drinkers in Nairobi ordering online

## Work like a designer, then like a developer

1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes and one signature element. Keep it under 120 words.
2. Build the UI exactly as the brief and the design system below describe.
3. Check it against the list at the end and fix what fails.

## Design system (use exactly this)

Mood: **warm**. Friendly and human, feels local and trusted.

Typography:
- Headings: **Gelasio**. Body: **Rubik**. Numbers and code: **Red Hat Mono**.
- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.
- Type scale in px, ratio 1.25: 13 / 16 / 20 / 24 / 32 / 40 / 48. Use only these sizes.
- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.

Color (hex):
- `paper` #f7f8f7: page background
- `surface` #ebf0eb: raised areas, table headers
- `line` #d1dbd2: borders and dividers
- `ink` #142415: main text
- `muted` #5a725a: secondary text
- `accent` #1f7a21: links, primary buttons, focus ring
- `on-accent` #ffffff: text on accent buttons
- `accent-2` #ad3e88: rare second accent, charts only
- `success` #38756b: success states
- `warning` #915a08: warning states
- `danger` #bf2c22: errors and destructive actions
- Checked contrast: ink on paper 15.3:1, muted on paper 4.9:1, accent on paper 5.1:1, text on accent 5.4:1.
- The accent covers less than 10% of any screen. No gradients.

Spacing and shape:
- Spacing scale in px: 8, 16, 24, 32, 48, 64, 96, 128. No other values.
- Corner radius: 8px for controls, 12px for containers. No other radii.
- Shadows only on floating layers (menus, dialogs, toasts). Everything else uses borders or tints.

Details that make it feel designed:
- Photography of real people and places from the product's market.
- Slightly larger body text (17 to 18px) and relaxed line height.
- One illustrated or photographic element per section at most.

## Layout rules for a landing

- No centered hero with a headline, a subline and two buttons. Left-align the headline.
- Show the product in the first screen: a real screenshot, a live demo or real data. Not an illustration.
- Do not lay features out as three equal cards. Vary the format from section to section.
- Build on a 12-column grid and use it asymmetrically, for example 7 and 5 columns.
- One call to action per screen. Make it say exactly what happens next.

## Content

- Write real copy for this product and audience. Each headline should only fit this product.
- Use realistic names, places, prices and numbers from the audience's market.
- If a figure is unknown, leave a clearly marked slot like [real figure] instead of inventing one.

## Never use

- Inter, Roboto, Arial, Open Sans or the plain system font stack as the main typeface
- The 'tasteful' AI fonts used by reflex: Space Grotesk, Geist, Instrument Serif, Fraunces, Poppins, Montserrat
- Purple, violet or indigo as the accent and any purple-to-blue or purple-to-pink gradient
- Cream background with a terracotta accent
- Gradient-filled headline text
- Glassmorphism (backdrop blur on translucent panels) and colored glow shadows
- Blurred color blobs, grid or dot pattern backgrounds
- Emoji as icons and the sparkle icon
- Icons inside pastel rounded squares above each feature
- rounded-2xl plus shadow-lg on every card
- A small pill badge ('New', 'Introducing v2') above the headline
- Copy-paste effect components from Aceternity UI or Magic UI
- hover:scale on cards and transition-all
- Hype words: "unlock", "seamless", "supercharge", "elevate", "revolutionize", "effortless", "next-gen", "all-in-one"
- Placeholder content: Lorem ipsum, John Doe, Acme, invented stats like '10,000+ happy users'

## Accessibility and motion

- Visible focus style on every interactive element (2px ring in the accent color, 2px offset).
- Text contrast at least 4.5:1. Hit targets at least 44px on touch screens.
- Alt text on every meaningful image. Semantic HTML: header, nav, main, section, table.
- Motion only when it explains a change. Respect prefers-reduced-motion. Transition specific properties, never 'all'.

## Before you finish

Check your own output against the design system above. Every font, size, color, spacing value and radius must come from it. Remove anything on the 'Never use' list. Then list any place where you broke a rule and why.

These rules outrank any styling words in the task. If the task and the rules disagree, follow the rules and say which part of the task you did not follow.

## Machine-readable design system

Save this block as `handmade.system.json` in the project root. `handmade check` uses it to verify that every font, color, size, spacing value and radius comes from this system.

```json
{
  "handmade_system": 1,
  "mood": "warm",
  "theme": "light",
  "fonts": {
    "display": "Gelasio",
    "body": "Rubik",
    "mono": "Red Hat Mono"
  },
  "colors": {
    "paper": "#f7f8f7",
    "surface": "#ebf0eb",
    "line": "#d1dbd2",
    "ink": "#142415",
    "muted": "#5a725a",
    "accent": "#1f7a21",
    "on-accent": "#ffffff",
    "accent-2": "#ad3e88",
    "danger": "#bf2c22",
    "success": "#38756b",
    "warning": "#915a08"
  },
  "type_scale_px": [
    13,
    16,
    20,
    24,
    32,
    40,
    48
  ],
  "spacing_px": [
    8,
    16,
    24,
    32,
    48,
    64,
    96,
    128
  ],
  "radius_px": {
    "controls": 8,
    "containers": 12
  }
}
```
