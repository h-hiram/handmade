# Task

Build what this request describes, for the product and audience below:

> build a landing page

Use the request for what to build and who it is for. Styling words in it are hints, not instructions. Where it conflicts with the design system or the never-use list, the design system wins.

## Context

- What it is: Duka Ledger, an app that tracks stock and daily sales for small shops in Kenya
- Who uses it and on what device: dukawallahs and kiosk owners on Android phones, often on slow data
- Visual reference: a handwritten shop ledger book. Take its attitude, not its layout.
- The one thing people should remember: today's sales total, in shillings

## Facts still missing

Nobody has said these yet. Ask the user for them before you build. If you cannot ask, leave a clearly marked slot such as [best sellers] and do not invent anything.

- What a person should do here. Ask: "What should a visitor do after reading this page?"
- Products and categories. Ask: "Roughly how many products and in which main categories?"
- How people pay and collect. Ask: "How do people pay and get their items?"
- Why people trust them. Ask: "What makes people trust you over the shop next door?"

## Work like a designer, then like a developer

1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes and one signature element. Keep it under 120 words.
2. Build the UI exactly as the brief and the design system below describe.
3. Check it against the list at the end and fix what fails.

## Design system (use exactly this)

Mood: **warm**. Friendly and human, feels local and trusted. (From the project's saved design system, so every screen matches.)

Typography:
- Headings: **Alegreya**. Body: **Alegreya Sans**. Numbers and code: **Red Hat Mono**.
- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.
- Type scale in px, ratio 1.25: 13 / 16 / 20 / 24 / 32 / 40 / 48. Use only these sizes.
- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.

Color (hex):
- `paper` #f8f6f8: page background
- `surface` #f0ebee: tinted regions, table headers, sidebars
- `raised` #fefefe: cards and panels that sit above the page
- `line` #dbd1d7: borders and dividers
- `ink` #24141e: main text
- `muted` #7e6374: secondary text
- `accent` #a43c7d: links, primary buttons, focus ring
- `accent-strong` #863166: hover and pressed state of accent elements
- `accent-soft` #f7e9f1: selected rows, active nav item, soft badges (use accent or ink text on it)
- `on-accent` #ffffff: text on accent buttons
- `accent-2` #449361: rare second accent
- `success` #227745: success states
- `warning` #915a08: warning states
- `danger` #bf2c22: errors and destructive actions
- `success-soft` #ebf9f1: background behind success text, for pills and notices
- `warning-soft` #fbf4e9: background behind warning text
- `danger-soft` #fbeae9: background behind danger text
- Tinted grey ramp for icons, placeholders, disabled states and subtle fills: `neutral-` 50 #f8f6f8, 100 #f1eef1, 200 #e4dde4, 300 #cfc4cf, 400 #afa1af, 500 #8c7d8c, 600 #6d5f6d, 700 #504450, 800 #352c35, 900 #1f191f.
- Chart series, in this order: #a43c7d, #5b9d39, #3f60ac, #ac5a3f, #e232a7. Each one is readable on paper (3:1 or more).
- Checked contrast: ink on paper 16.4:1, muted on paper 5.0:1, accent on paper 5.5:1, text on accent 6.0:1.
- The accent covers less than 10% of any screen. No gradients.

Spacing and shape:
- Spacing scale in px: 8, 16, 24, 32, 48, 64, 96, 128. No other values.
- Corner radius: 8px for controls, 12px for containers. No other radii.
- Depth (shadows): Cards are `raised` on `paper` with the soft `raised` shadow and no border or a border and no shadow. Never both. Menus and dialogs use the `overlay` shadow.
- Shadow `raised`: `0 1px 2px rgba(36, 20, 30, 0.06), 0 2px 8px -2px rgba(36, 20, 30, 0.06)`.
- Shadow `overlay`: `0 16px 40px -12px rgba(36, 20, 30, 0.22), 0 4px 12px -4px rgba(36, 20, 30, 0.08)`. No other shadows.

Details that make it feel designed:
- Photography of real people and places from the product's market.
- Slightly larger body text (17 to 18px) and relaxed line height.
- One illustrated or photographic element per section at most.

From the existing project:
- Keep the saved design system (handmade.system.json).

## Layout rules for a landing

- No centered hero with a headline, a subline and two buttons. Left-align the headline.
- Show the product in the first screen: a real screenshot, a live demo or real data. Not an illustration.
- Do not lay features out as three equal cards. Vary the format from section to section.
- Build on a 12-column grid and use it asymmetrically, for example 7 and 5 columns.
- One call to action per screen. Make it say exactly what happens next.

## Craft: what makes it look finished

Plain is not the goal. Build it to the standard of a product designer's final mockup.

- The first screen shows the real product or real photography, framed with care: a browser or device frame, a cropped detail or a composed photo. Never an empty gradient.
- Give each section its own format: a statement, a product detail with callouts, proof with real names, a comparison, a short FAQ. Do not repeat card grids.
- Use the display face at a confident size for one line per section. Everything else stays calm.
- Proof must be real: customer names, places and numbers the user supplied or marked slots.
- A footer with real contact details, hours and location or marked slots for them.
- Make hierarchy with weight and color first, size second. Most text is body size. Labels use `muted`.
- Design every state: hover, focus, active, selected, disabled, empty, loading and error. Empty states say what will appear and give the next action.
- Style every control. No browser-default selects, date inputs, checkboxes or file inputs. Build custom ones from the system, keeping them accessible.
- Use one icon set at one stroke width and one size per context (16px inline, 20px in navigation). Icons sit on the text baseline and always have a label or aria-label.
- Numbers use tabular figures (`font-variant-numeric: tabular-nums`). Units and currency are smaller and `muted`.
- Transitions run 150 to 200ms with ease-out, on color, background, border, opacity or transform only.
- Align everything to the spacing scale. Repeated items share exact heights and baselines.

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
    "display": "Alegreya",
    "body": "Alegreya Sans",
    "mono": "Red Hat Mono"
  },
  "colors": {
    "paper": "#f8f6f8",
    "surface": "#f0ebee",
    "line": "#dbd1d7",
    "ink": "#24141e",
    "muted": "#7e6374",
    "accent": "#a43c7d",
    "on-accent": "#ffffff",
    "accent-2": "#449361",
    "danger": "#bf2c22",
    "success": "#227745",
    "warning": "#915a08",
    "raised": "#fefefe",
    "accent-soft": "#f7e9f1",
    "accent-strong": "#863166",
    "success-soft": "#ebf9f1",
    "warning-soft": "#fbf4e9",
    "danger-soft": "#fbeae9",
    "neutral-50": "#f8f6f8",
    "neutral-100": "#f1eef1",
    "neutral-200": "#e4dde4",
    "neutral-300": "#cfc4cf",
    "neutral-400": "#afa1af",
    "neutral-500": "#8c7d8c",
    "neutral-600": "#6d5f6d",
    "neutral-700": "#504450",
    "neutral-800": "#352c35",
    "neutral-900": "#1f191f",
    "chart-1": "#a43c7d",
    "chart-2": "#5b9d39",
    "chart-3": "#3f60ac",
    "chart-4": "#ac5a3f",
    "chart-5": "#e232a7"
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
  },
  "shadows": {
    "raised": "0 1px 2px rgba(36, 20, 30, 0.06), 0 2px 8px -2px rgba(36, 20, 30, 0.06)",
    "overlay": "0 16px 40px -12px rgba(36, 20, 30, 0.22), 0 4px 12px -4px rgba(36, 20, 30, 0.08)"
  },
  "depth": "shadows"
}
```
