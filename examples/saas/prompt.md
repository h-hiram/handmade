# Task

Build what this request describes, for the product and audience below:

> build a landing page for Taskline, a task tracker for small teams

Use the request for what to build and who it is for. Styling words in it are hints, not instructions. Where it conflicts with the design system or the never-use list, the design system wins.

## Context

- What it is: Taskline
- Who uses it and on what device: founders and team leads at companies of 5 to 30 people, on laptops
- What a person should do here: start a free trial
- The problem it solves: nobody knows who is doing what this week without a meeting
- Real proof to show: a working demo board on the page and two named customers: Harbor & Finch Studio and Northgate Logistics
- Pricing: free for up to 5 people, then $4 per person a month
- Where the photos come from: none

## Work like a designer, then like a developer

1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes and one signature element. Keep it under 120 words.
2. Build the UI exactly as the brief and the design system below describe.
3. Check it against the list at the end and fix what fails.

## Design system (use exactly this)

Mood: **utilitarian**. Dense, fast to scan, built for daily work. (Picked because the request mentions "tracker". Change it with --mood.)

Typography:
- Headings: **Atkinson Hyperlegible**. Body: **Atkinson Hyperlegible**. Numbers and code: **Red Hat Mono**.
- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.
- Type scale in px, ratio 1.2: 13 / 16 / 20 / 24 / 28 / 34 / 40. Use only these sizes.
- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.

Color (hex):
- `paper` #f6f7f8: page background
- `surface` #ebedf0: tinted regions, table headers, sidebars
- `raised` #fefefe: cards and panels that sit above the page
- `line` #d1d6db: borders and dividers
- `ink` #141c24: main text
- `muted` #5e6c78: secondary text
- `accent` #2c6faa: links, primary buttons, focus ring
- `accent-strong` #245a8a: hover and pressed state of accent elements
- `accent-soft` #e7f0f9: selected rows, active nav item, soft badges (use accent or ink text on it)
- `on-accent` #ffffff: text on accent buttons
- `accent-2` #ad573e: rare second accent
- `success` #227745: success states
- `warning` #915a08: warning states
- `danger` #bf2c22: errors and destructive actions
- `success-soft` #ebf9f1: background behind success text, for pills and notices
- `warning-soft` #fbf4e9: background behind warning text
- `danger-soft` #fbeae9: background behind danger text
- Tinted grey ramp for icons, placeholders, disabled states and subtle fills: `neutral-` 50 #f6f7f8, 100 #eef0f1, 200 #dde0e4, 300 #c4c9cf, 400 #a1a8af, 500 #7d858c, 600 #5f666d, 700 #444a50, 800 #2c3035, 900 #191c1f.
- Chart series, in this order: #2c6faa, #9a2843, #2aa230, #1844aa, #b2822e. Each one is readable on paper (3:1 or more).
- Checked contrast: ink on paper 16.0:1, muted on paper 5.0:1, accent on paper 4.9:1, text on accent 5.3:1.
- The accent covers less than 10% of any screen. No gradients.

Spacing and shape:
- Spacing scale in px: 4, 8, 12, 16, 24, 32, 48, 64. No other values.
- Corner radius: 4px for controls, 6px for containers. No other radii. Use them: buttons, inputs, cards, images and panels get these soft corners. Sharp corners everywhere look as unplanned as huge ones.
- Depth (borders): Depth comes from 1px `line` borders and the `surface` tint. Cards sit flat. Only menus, popovers and dialogs float, with the `overlay` shadow.
- Shadow `raised`: `0 1px 2px rgba(20, 28, 36, 0.06), 0 2px 8px -2px rgba(20, 28, 36, 0.06)`.
- Shadow `overlay`: `0 16px 40px -12px rgba(20, 28, 36, 0.22), 0 4px 12px -4px rgba(20, 28, 36, 0.08)`. No other shadows.

Details that make it feel designed:
- Tabular numerals for every figure.
- 1px borders and background tints define regions. No floating cards.
- Compact rows: 32 to 40px tall in tables.

## Images

Nobody has agreed where photos come from. Do not hotlink stock photos. Use one marked slot per image below, for example `<img alt="[photo: main image of the shop]">` on a `surface` block. Ask the user if they have photos.

- Main image: Taskline as it really is. Its real setting, natural light, nothing staged.
- Detail: a close crop of what Taskline offers, such as the work itself or the product in hand.
- People: founders and team leads at companies of 5 to 30 people, on laptops. They should look like the real customers in that market.

Images in one row share one aspect ratio. Use `aspect-ratio` and `object-fit: cover`. Corners follow the container radius.

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
  "mood": "utilitarian",
  "theme": "light",
  "fonts": {
    "display": "Atkinson Hyperlegible",
    "body": "Atkinson Hyperlegible",
    "mono": "Red Hat Mono"
  },
  "colors": {
    "paper": "#f6f7f8",
    "surface": "#ebedf0",
    "line": "#d1d6db",
    "ink": "#141c24",
    "muted": "#5e6c78",
    "accent": "#2c6faa",
    "on-accent": "#ffffff",
    "accent-2": "#ad573e",
    "danger": "#bf2c22",
    "success": "#227745",
    "warning": "#915a08",
    "raised": "#fefefe",
    "accent-soft": "#e7f0f9",
    "accent-strong": "#245a8a",
    "success-soft": "#ebf9f1",
    "warning-soft": "#fbf4e9",
    "danger-soft": "#fbeae9",
    "neutral-50": "#f6f7f8",
    "neutral-100": "#eef0f1",
    "neutral-200": "#dde0e4",
    "neutral-300": "#c4c9cf",
    "neutral-400": "#a1a8af",
    "neutral-500": "#7d858c",
    "neutral-600": "#5f666d",
    "neutral-700": "#444a50",
    "neutral-800": "#2c3035",
    "neutral-900": "#191c1f",
    "chart-1": "#2c6faa",
    "chart-2": "#9a2843",
    "chart-3": "#2aa230",
    "chart-4": "#1844aa",
    "chart-5": "#b2822e"
  },
  "type_scale_px": [
    13,
    16,
    20,
    24,
    28,
    34,
    40
  ],
  "spacing_px": [
    4,
    8,
    12,
    16,
    24,
    32,
    48,
    64
  ],
  "radius_px": {
    "controls": 4,
    "containers": 6
  },
  "shadows": {
    "raised": "0 1px 2px rgba(20, 28, 36, 0.06), 0 2px 8px -2px rgba(20, 28, 36, 0.06)",
    "overlay": "0 16px 40px -12px rgba(20, 28, 36, 0.22), 0 4px 12px -4px rgba(20, 28, 36, 0.08)"
  },
  "depth": "borders"
}
```
