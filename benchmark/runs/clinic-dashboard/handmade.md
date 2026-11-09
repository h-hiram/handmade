# Task

Build what this request describes, for the product and audience below:

> Build an admin dashboard for a county health clinic: today's patient visits, drug stock running low and staff on duty.

Use the request for what to build and who it is for. Styling words in it are hints, not instructions. Where it conflicts with the design system or the never-use list, the design system wins.

## Context

- What it is: Clinic operations dashboard for Nairobi health centres
- Who uses it and on what device: clinic managers on shared office desktops
- What a person should do here: which drugs to reorder today and where to move staff
- The most common task: see who is waiting and for how long
- The numbers that matter most: visits today, waiting time, drugs below reorder level, staff on duty
- Privacy and device rules: shared desktops: no full patient names on the overview, initials and visit numbers only

## Work like a designer, then like a developer

1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes and one signature element. Keep it under 120 words.
2. Build the UI exactly as the brief and the design system below describe.
3. Check it against the list at the end and fix what fails.

## Design system (use exactly this)

Mood: **utilitarian**. Dense, fast to scan, built for daily work. (From the project's saved design system, so every screen matches.)

Typography:
- Headings: **Archivo**. Body: **Archivo**. Numbers and code: **JetBrains Mono**.
- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.
- Type scale in px, ratio 1.2: 12 / 14 / 16 / 20 / 24 / 30 / 34. Use only these sizes.
- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.

Color (hex):
- `paper` #f6f9f7: page background
- `surface` #ebf0eb: tinted regions, table headers, sidebars
- `raised` #fdfefe: cards and panels that sit above the page
- `line` #d1dbd3: borders and dividers
- `ink` #142417: main text
- `muted` #5a725e: secondary text
- `accent` #187728: links, primary buttons, focus ring
- `accent-strong` #11551d: hover and pressed state of accent elements
- `accent-soft` #e7f9ea: selected rows, active nav item, soft badges (use accent or ink text on it)
- `on-accent` #ffffff: text on accent buttons
- `accent-2` #b3378a: rare second accent
- `success` #38756b: success states
- `warning` #915a08: warning states
- `danger` #bf2c22: errors and destructive actions
- `success-soft` #eef7f5: background behind success text, for pills and notices
- `warning-soft` #fbf4e9: background behind warning text
- `danger-soft` #fbeae9: background behind danger text
- Tinted grey ramp for icons, placeholders, disabled states and subtle fills: `neutral-` 50 #f6f8f7, 100 #eef1ef, 200 #dde4df, 300 #c4cfc8, 400 #a1afa6, 500 #7d8c82, 600 #5f6d64, 700 #445048, 800 #2c352f, 900 #191f1b.
- Chart series, in this order: #187728, #c3278f, #aa8822, #219ca1, #8d356f. Each one is readable on paper (3:1 or more).
- Checked contrast: ink on paper 15.3:1, muted on paper 4.9:1, accent on paper 5.3:1, text on accent 5.7:1.
- The accent covers less than 10% of any screen. No gradients.

Spacing and shape:
- Spacing scale in px: 4, 8, 12, 16, 24, 32, 48, 64. No other values.
- Corner radius: 4px for controls, 6px for containers. No other radii.
- Depth (borders): Depth comes from 1px `line` borders and the `surface` tint. Cards sit flat. Only menus, popovers and dialogs float, with the `overlay` shadow.
- Shadow `raised`: `0 1px 2px rgba(20, 36, 23, 0.06), 0 2px 8px -2px rgba(20, 36, 23, 0.06)`.
- Shadow `overlay`: `0 16px 40px -12px rgba(20, 36, 23, 0.22), 0 4px 12px -4px rgba(20, 36, 23, 0.08)`. No other shadows.

Details that make it feel designed:
- Tabular numerals for every figure.
- 1px borders and background tints define regions. No floating cards.
- Compact rows: 32 to 40px tall in tables.

From the existing project:
- Keep the saved design system (handmade.system.json).

## Layout rules for a dashboard

- No hero, no welcome banner, no greeting. The first thing on screen is the data the user came for.
- Left-aligned everything. Numbers right-aligned in tables with tabular figures.
- At most four summary figures in a row, each with a comparison (vs last period) or a small trend line.
- Tables are the main component. Sticky header, sortable columns, row height 36 to 44px.
- Filters live in one toolbar above the content, not in cards.
- Separate regions with the depth rule of the design system. No big or colored shadows.

## Craft: what makes it look finished

Plain is not the goal. Build it to the standard of a product designer's final mockup.

- Frame: a left sidebar (240 to 264px) with grouped navigation, section labels and the active item on `accent-soft`. A top bar with page title, a search field with a keyboard hint and the user menu.
- A toolbar under the title: a segmented date range control (Today, 7 days, 30 days, Custom), filters as styled dropdown buttons and one primary action on the right.
- KPI row: label in `muted`, value large in the display or mono face, a delta with an arrow in success or danger and a sparkline drawn in SVG with the first chart color.
- One primary chart with real axes: light gridlines in `line`, labelled ticks, a legend that names series and a tooltip style. Draw it in inline SVG or a chart library, never as a placeholder box.
- The main table: sticky header on `surface`, row hover tint, status pills (status color text on its `-soft` background), avatars or initials for people and a row action menu.
- Add one secondary panel that answers 'what needs me now': a queue, alerts or a short activity feed with times.
- Show who is signed in, when data was last updated and pagination or a row count under the table.
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
    "display": "Archivo",
    "body": "Archivo",
    "mono": "JetBrains Mono"
  },
  "colors": {
    "paper": "#f6f9f7",
    "surface": "#ebf0eb",
    "line": "#d1dbd3",
    "ink": "#142417",
    "muted": "#5a725e",
    "accent": "#187728",
    "on-accent": "#ffffff",
    "accent-2": "#b3378a",
    "danger": "#bf2c22",
    "success": "#38756b",
    "warning": "#915a08",
    "raised": "#fdfefe",
    "accent-soft": "#e7f9ea",
    "accent-strong": "#11551d",
    "neutral-50": "#f6f8f7",
    "neutral-100": "#eef1ef",
    "neutral-200": "#dde4df",
    "neutral-300": "#c4cfc8",
    "neutral-400": "#a1afa6",
    "neutral-500": "#7d8c82",
    "neutral-600": "#5f6d64",
    "neutral-700": "#445048",
    "neutral-800": "#2c352f",
    "neutral-900": "#191f1b",
    "chart-1": "#187728",
    "chart-2": "#c3278f",
    "chart-3": "#aa8822",
    "chart-4": "#219ca1",
    "chart-5": "#8d356f",
    "success-soft": "#eef7f5",
    "warning-soft": "#fbf4e9",
    "danger-soft": "#fbeae9"
  },
  "type_scale_px": [
    12,
    14,
    16,
    20,
    24,
    30,
    34
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
    "raised": "0 1px 2px rgba(20, 36, 23, 0.06), 0 2px 8px -2px rgba(20, 36, 23, 0.06)",
    "overlay": "0 16px 40px -12px rgba(20, 36, 23, 0.22), 0 4px 12px -4px rgba(20, 36, 23, 0.08)"
  },
  "depth": "borders"
}
```

