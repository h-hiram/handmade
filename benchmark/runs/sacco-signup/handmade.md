# Task

Build what this request describes, for the product and audience below:

> Build a member registration form for a matatu SACCO: personal details, vehicle registration, next of kin.

Use the request for what to build and who it is for. Styling words in it are hints, not instructions. Where it conflicts with the design system or the never-use list, the design system wins.

## Context

- What it is: Member portal for a matatu SACCO in Nairobi
- Who uses it and on what device: matatu owners, mostly on Android phones
- What a person should do here: the SACCO office reviews the application and sends a member number by SMS within two working days
- Fields: full name, national ID, phone (M-Pesa), vehicle registration, route, next of kin name, relationship and phone
- Documents: photo of the logbook and the national ID

## Facts still missing

Nobody has said these yet. Ask the user for them before you build. If you cannot ask, leave a clearly marked slot such as [best sellers] and do not invent anything.

- Main products. Ask: "Which products or accounts do people use most?"
- Why people trust them. Ask: "What proves you are safe and regulated?"
- The first task. Ask: "What is the first thing a member wants to do?"

## Work like a designer, then like a developer

1. Before any code, write a short design brief. Cover the layout, the type hierarchy, where the accent goes and one signature element. Keep it under 120 words.
2. Build the UI exactly as the brief and the design system below describe.
3. Check it against the list at the end and fix what fails.

## Design system (use exactly this)

Mood: **civic**. Plain, trustworthy, accessible to everyone. (From the project's saved design system, so every screen matches.)

Typography:
- Headings: **Merriweather Sans**. Body: **Merriweather**. Numbers and code: **Source Code Pro**.
- Load every font properly (Google Fonts link, @font-face, next/font or @fontsource). Never name a font you do not load.
- Type scale in px, ratio 1.2: 13 / 16 / 20 / 24 / 28 / 34 / 40. Use only these sizes.
- Body line height 1.5. Headings 1.1 to 1.25. Line length 60 to 75 characters for reading text.

Color (hex):
- `paper` #f6f7f8: page background
- `surface` #ebedf0: tinted regions, table headers, sidebars
- `raised` #fefefe: cards and panels that sit above the page
- `line` #d1d6db: borders and dividers
- `ink` #141b24: main text
- `muted` #5e6a78: secondary text
- `accent` #376ba9: links, primary buttons, focus ring
- `accent-strong` #2d588a: hover and pressed state of accent elements
- `accent-soft` #e8eff7: selected rows, active nav item, soft badges (use accent or ink text on it)
- `on-accent` #ffffff: text on accent buttons
- `accent-2` #a54a46: rare second accent
- `success` #227745: success states
- `warning` #915a08: warning states
- `danger` #bf2c22: errors and destructive actions
- `success-soft` #ebf9f1: background behind success text, for pills and notices
- `warning-soft` #fbf4e9: background behind warning text
- `danger-soft` #fbeae9: background behind danger text
- Tinted grey ramp for icons, placeholders, disabled states and subtle fills: `neutral-` 50 #f6f7f8, 100 #eef0f1, 200 #dde0e4, 300 #c4c9cf, 400 #a1a8af, 500 #7d858c, 600 #5f666d, 700 #444a50, 800 #2c3035, 900 #191c1f.
- Chart series, in this order: #376ba9, #923040, #35a242, #b13a89, #a98837. Each one is readable on paper (3:1 or more).
- Checked contrast: ink on paper 16.2:1, muted on paper 5.1:1, accent on paper 5.1:1, text on accent 5.5:1.
- The accent covers less than 10% of any screen. No gradients.

Spacing and shape:
- Spacing scale in px: 4, 8, 12, 16, 24, 32, 48, 64. No other values.
- Corner radius: 4px for controls, 4px for containers. No other radii.
- Depth (borders): Depth comes from 1px `line` borders and the `surface` tint. Cards sit flat. Only menus, popovers and dialogs float, with the `overlay` shadow.
- Shadow `raised`: `0 1px 2px rgba(20, 27, 36, 0.06), 0 2px 8px -2px rgba(20, 27, 36, 0.06)`.
- Shadow `overlay`: `0 16px 40px -12px rgba(20, 27, 36, 0.22), 0 4px 12px -4px rgba(20, 27, 36, 0.08)`. No other shadows.

Details that make it feel designed:
- Plain language at a reading age most citizens can follow.
- Clear headings that say what the section does.
- Meet WCAG 2.2 AA everywhere, AAA for body text where possible.

From the existing project:
- Keep the saved design system (handmade.system.json).

## Layout rules for a form

- Single column. Labels above fields. Helper text under the label when the field needs it.
- Show errors inline, next to the field, in plain words that say how to fix them.
- Group related fields under a short heading. Mark optional fields, not required ones.
- Primary button aligned with the fields' left edge, labelled with the action (for example 'Create account').

## Craft: what makes it look finished

Plain is not the goal. Build it to the standard of a product designer's final mockup.

- Frame: a two-column layout on desktop. The form on the left (about 560px). A summary or help panel on the right with what the user gets, what they need ready and how long it takes.
- Long forms become steps with a progress indicator (step names, not only numbers). At most five fields per step.
- Each field: label above, helper text where it helps, a 44px tall input with a clear focus ring, inline validation after the field loses focus and an error message that says how to fix it.
- Use the right control: segmented buttons or radio cards for two to four choices, a styled select for more, input masks for phone and ID numbers and a styled file drop zone for uploads.
- A sticky footer bar with Back and the primary action. The primary button names the action.
- Reassure at the point of doubt: data use, fees and timing next to the field that raises them.
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
  "mood": "civic",
  "theme": "light",
  "fonts": {
    "display": "Merriweather Sans",
    "body": "Merriweather",
    "mono": "Source Code Pro"
  },
  "colors": {
    "paper": "#f6f7f8",
    "surface": "#ebedf0",
    "line": "#d1d6db",
    "ink": "#141b24",
    "muted": "#5e6a78",
    "accent": "#376ba9",
    "on-accent": "#ffffff",
    "accent-2": "#a54a46",
    "danger": "#bf2c22",
    "success": "#227745",
    "warning": "#915a08",
    "raised": "#fefefe",
    "accent-soft": "#e8eff7",
    "accent-strong": "#2d588a",
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
    "chart-1": "#376ba9",
    "chart-2": "#923040",
    "chart-3": "#35a242",
    "chart-4": "#b13a89",
    "chart-5": "#a98837",
    "success-soft": "#ebf9f1",
    "warning-soft": "#fbf4e9",
    "danger-soft": "#fbeae9"
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
    "containers": 4
  },
  "shadows": {
    "raised": "0 1px 2px rgba(20, 27, 36, 0.06), 0 2px 8px -2px rgba(20, 27, 36, 0.06)",
    "overlay": "0 16px 40px -12px rgba(20, 27, 36, 0.22), 0 4px 12px -4px rgba(20, 27, 36, 0.08)"
  },
  "depth": "borders"
}
```

