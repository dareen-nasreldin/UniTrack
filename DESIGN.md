---
name: UniTrack
description: Personal task tracker for a Computer Engineering student — inbox-first, course-organized, deadline-aware.
colors:
  accent: "#4F46E5"
  accent-hover: "#4338CA"
  accent-light: "#EEF2FF"
  accent-text: "#3730A3"
  nav-bg: "#0F172A"
  bg: "#F8FAFC"
  surface: "#FFFFFF"
  surface-2: "#F1F5F9"
  border: "#E2E8F0"
  border-strong: "#CBD5E1"
  text: "#0F172A"
  text-muted: "#64748B"
  text-faint: "#94A3B8"
  success: "#16A34A"
  success-bg: "#F0FDF4"
  success-border: "#86EFAC"
  danger: "#DC2626"
  danger-bg: "#FEF2F2"
  danger-border: "#FCA5A5"
  warning: "#D97706"
  warning-bg: "#FFFBEB"
  warning-border: "#FCD34D"
  info: "#0369A1"
  info-bg: "#F0F9FF"
  info-border: "#7DD3FC"
typography:
  display:
    fontFamily: "'DM Serif Display', Georgia, serif"
    fontSize: "clamp(2.25rem, 3.75vw, 3.375rem)"
    fontWeight: 400
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  title:
    fontFamily: "'DM Serif Display', Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    letterSpacing: "0.01em"
  caption:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    letterSpacing: "0.06em"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-danger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.danger}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  task-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "16px"
  form-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "9px 12px"
---

# Design System: UniTrack

## 1. Overview

**Creative North Star: "The Quiet Instrument"**

UniTrack's visual system is built around a single idea: a well-calibrated instrument disappears in use. The UI does not announce itself. It holds information without decoration, responds to interaction without drama, and rewards close attention with structural clarity. Slate stillness. Indigo precision. A dark navbar that anchors the chrome; a white body that holds the work.

The system rejects two aesthetics by name. First, the generic SaaS productivity aesthetic — pastel blobs, rounded gradients, "streamline your workflow" energy, Asana-style milestone celebrations. Second, the gamified app aesthetic — confetti, streaks, achievement badges, encouraging microcopy. UniTrack is a personal tool built by an engineer for an engineer. It does not try to motivate; it enables.

The landing page is exempt from the interior's restraint. There, the serif and indigo can move forward. In the app, they stay at the back.

**Key Characteristics:**
- Dark slate-900 navbar anchors the chrome; near-white body holds the work
- Indigo as the single accent voice — used sparingly, always carrying meaning
- DM Serif Display for page titles and hero headings; system-sans for all functional copy
- Shadows imply lift without announcing it — ambient and barely perceptible at rest
- Dense information with explicit breathing room between groups (course sections, form fields)

## 2. Colors: The Slate and Signal Palette

One accent voice over a structured slate neutral ramp. The palette has no secondary accent; indigo is the only color with intent.

### Primary
- **Clarity Indigo** (`#4F46E5`): The single accent voice. Focus rings, primary buttons, active states, today's calendar highlight, active toggle segments. Never decorative — only when carrying user intent or system state.
- **Clarity Indigo Deep** (`#4338CA`): Hover state for indigo-colored interactive elements. One step darker, same role.
- **Clarity Indigo Tint** (`#EEF2FF`): Background tint for indigo-context areas (internship section, today's calendar cell, edit-button hover). Communicates "this region belongs to the accent" at low intensity.
- **Clarity Indigo Text** (`#3730A3`): Indigo-tinted body text used within accent-light regions for readable contrast.

### Neutral
- **Page Mist** (`#F8FAFC`): Page background. Near-white with the faintest slate tint — cooler than cream, never warm.
- **Pure Surface** (`#FFFFFF`): Cards, panels, form inputs, navbar dropdowns. The active working surface.
- **Receded Slate** (`#F1F5F9`): Secondary surfaces — input backgrounds on hover, info boxes, empty calendar cells, secondary panels. One step behind Pure Surface.
- **Deep Slate** (`#0F172A`): Primary text and the navbar background. The same hue at full depth, tying body copy to the navigation chrome.
- **Mid Slate** (`#64748B`): Muted text — subtitles, metadata, placeholder labels, course section headers. Secondary information.
- **Faint Slate** (`#94A3B8`): Placeholder text, hints, done-task metadata, empty indicators. Tertiary information; present but receded.
- **Hairline** (`#E2E8F0`): Default borders — card edges, field strokes, dividers.
- **Structural Line** (`#CBD5E1`): Hover and focus borders. One step stronger; visible on interaction.

### Semantic
- **Clear** (`#16A34A`) / tint `#F0FDF4` / stroke `#86EFAC`: Task completion, success messages.
- **Alarm** (`#DC2626`) / tint `#FEF2F2` / stroke `#FCA5A5`: Destructive actions, error states.
- **Caution** (`#D97706`) / tint `#FFFBEB` / stroke `#FCD34D`: Inbox-pending alerts, overdue warnings.
- **Signal** (`#0369A1`) / tint `#F0F9FF` / stroke `#7DD3FC`: Informational messages, neutral system notices.

### Named Rules
**The One Voice Rule.** Clarity Indigo is the only non-neutral, non-semantic accent in the system. Do not introduce a second accent color. If a surface needs visual distinction, use a background tint or a border step — not a new hue.

**The Warm-Neutral Prohibition.** Page Mist (`#F8FAFC`) is cool-tinted. Never drift the background toward warm or sandy tones. Warmth in this system lives in the typography pairing (serif + sans), not in the surface color.

## 3. Typography

**Display Font:** DM Serif Display (with Georgia, serif fallback)
**Body Font:** System UI stack (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial)

**Character:** The serif/sans pairing creates editorial contrast without softening the engineering tone. DM Serif Display carries weight through its letterforms alone — no bold, no uppercase, no tracking. It appears only at the title level and above; below that, everything is system-sans. The fonts share almost no visual DNA, which is the point: the contrast is the hierarchy.

### Hierarchy
- **Display** (weight 400, clamp(2.25rem–3.375rem), line-height 1.12, letter-spacing -0.025em): Landing page hero and section headings only. The font's natural weight does the work; don't pair with bold.
- **Title** (DM Serif Display, 1.5rem, line-height 1.3, letter-spacing -0.02em): Page-level headings inside the app (`<h2 class="page-title">`). One per page.
- **Body** (system-sans, 0.9375rem/15px, line-height 1.6): All functional copy — task titles, form copy, descriptions. The working register.
- **Label** (system-sans, 0.8125rem, weight 600, letter-spacing 0.01em): Form field labels, nav links, button text, item metadata. Short runs only.
- **Caption** (system-sans, 0.75rem, weight 600, letter-spacing 0.06em): Course section headers in the dashboard — uppercase structural dividers that organize task groups. This is the only sanctioned use of uppercase tracked text in the app interior.

### Named Rules
**The Serif Ceiling Rule.** DM Serif Display appears only at Title level and above. Never use it for body copy, labels, buttons, or metadata. Below the page title, the system is pure sans.

**The One Uppercase Zone Rule.** Uppercase tracked text (`letter-spacing: 0.06em; text-transform: uppercase`) is reserved for course section headers — structural dividers that group task cards. It is not a decorative pattern and must not appear as marketing eyebrows, card labels, or button text.

## 4. Elevation

The system is subtly lifted by default. Cards and panels carry a permanent ambient shadow that is barely perceptible at rest — present enough to separate the surface from the page, not enough to draw attention. Elevation reads as structural fact, not decorative statement.

Shadows use the page's own dark hue (`rgba(15,23,42,...)`) at low opacity, so they read as the page casting shade rather than a generic drop shadow. Three steps; each has a defined role.

### Shadow Vocabulary
- **Ambient** (`0 1px 2px rgba(15,23,42,.06), 0 1px 3px rgba(15,23,42,.04)`): Default resting state for all cards, containers, and form panels. Always present; imperceptible in isolation.
- **Hover Lift** (`0 4px 12px rgba(15,23,42,.07), 0 2px 4px rgba(15,23,42,.04)`): Applied on card hover. The only moment elevation is consciously felt. Transitions at 150ms.
- **Modal** (`0 8px 24px rgba(15,23,42,.08), 0 4px 8px rgba(15,23,42,.04)`): Reserved for overlays, dialogs, and popovers that sit above page content.

### Named Rules
**The Flat-At-Rest Rule.** Surfaces at rest carry only Ambient shadow. Hover Lift exists to confirm interactivity — it should never appear on non-interactive elements. If something can't be clicked, it doesn't lift.

## 5. Components

### Buttons
Tactile and immediate — tight padding, crisp borders, responses within 150ms. The hierarchy is clear and never ambiguous.

- **Shape:** Gently curved (8px radius, `{rounded.md}`)
- **Primary:** Clarity Indigo background (`#4F46E5`), white text, 8px×16px padding, min-height 36px. Hover transitions to Clarity Indigo Deep (`#4338CA`) in 150ms.
- **Small variant:** 6px×12px padding, min-height 32px, 13px font. Same color rules.
- **Secondary:** White background, slate-900 text, Hairline border. Hover shifts background to Receded Slate, border to Structural Line.
- **Danger (ghost):** White background, Alarm red text, danger-border stroke. Hover fills danger-bg. Never solid red background on default state — destructive actions require a confirmation step before presenting a filled danger button.
- **Success:** Solid Clear green, white text. Used only for completion confirmations, not primary navigation actions.
- **Focus ring:** 2px Clarity Indigo outline, 2px offset. Present on all interactive elements; never suppressed.

### Task Action Strip (Signature Component)
The 3-button strip (complete / edit / delete) is UniTrack's most distinctive component. Three 30×30px icon buttons grouped in a bordered cluster, separated by 1px gaps using the border color as fill. The border-radius matches `{rounded.sm}` (6px).

- **Default state:** Surface background, Mid Slate icons. Unobtrusive.
- **Complete hover:** Clear green tint background, green icon.
- **Edit hover:** Clarity Indigo tint background, indigo icon.
- **Delete hover:** Alarm red tint background, red icon.
- Touch target expanded to ~44px via `::after` pseudo-element; visual footprint stays 30px.

### Cards / Containers
- **Corner Style:** Smoothly rounded (12px, `{rounded.lg}`) for page-level containers; modestly rounded (8px, `{rounded.md}`) for cards within containers
- **Background:** Pure Surface (`#FFFFFF`) on Page Mist bg; Receded Slate (`#F1F5F9`) for secondary regions inside a card
- **Shadow:** Ambient at rest; Hover Lift on interactive cards
- **Border:** 1px Hairline (`#E2E8F0`) at rest; 1px Structural Line (`#CBD5E1`) on hover
- **Internal Padding:** 1.5rem (24px) for page containers; 1rem (16px) for task cards

### Inputs / Fields
- **Style:** White background, 1px Hairline border, 8px radius. 16px font size (prevents iOS zoom on mobile).
- **Focus:** Border shifts to Clarity Indigo; 3px Clarity Indigo ring at 12% opacity (`rgba(79,70,229,.12)`). The ring is deliberately soft — assertive enough to confirm focus, quiet enough not to compete with content.
- **Placeholder:** Faint Slate (`#94A3B8`). Meets 4.5:1 against the white input background.
- **Labels:** 0.8125rem, weight 600, Deep Slate — positioned above the field, never as floating placeholders.
- **Disabled / Error:** Not yet styled; when added, use Receded Slate background for disabled and Alarm border/tint for error.

### Navigation
- **Style:** Full-width dark bar, slate-900 background (`#0F172A`), 56px height, sticky at top.
- **Logo:** White-on-dark, 700 weight, with inline SVG trend-line mark in a rounded square at 12% white fill.
- **Nav links:** 36px height, slate-400 default text, 6px radius. Hover: white text, 8% white background fill. Active page gets no special treatment beyond the browser's current URL — links don't carry persistent active states in the current implementation.
- **Mobile:** Hamburger toggle at ≤768px. Menu drops below nav as a vertical list with the same link styles. Animated hamburger-to-X using transform/opacity transitions.
- **User section:** Divider line, email in slate-500 (truncated at 180px), Account link, Sign Out button styled as a nav link.

### Inline Delete Confirmation
Two-step delete flow replacing browser `confirm()`. The delete button reveals a ✓ / ✗ pair in-place, using the same 30px action-button footprint. The confirmation step uses Alarm red tint background (danger-bg) to signal consequence before committing.

## 6. Do's and Don'ts

### Do:
- **Do** use Clarity Indigo only when it carries meaning — focus, primary action, active state, today's date. Its rarity is what makes it legible.
- **Do** use DM Serif Display only for page-level titles and landing hero headings. One serif heading per screen.
- **Do** apply Ambient shadow as the default resting elevation for all cards and containers. Never zero-shadow a surface that sits on the page.
- **Do** differentiate surface depth through background color steps (Page Mist → Pure Surface → Receded Slate) before adding borders or shadows.
- **Do** use `text-wrap: balance` on h1–h3 headings to prevent orphaned words.
- **Do** expand touch targets to ~44px on icon buttons via pseudo-element, while keeping the visual footprint at its intended size.
- **Do** provide a two-step confirmation before any destructive action. Never a `window.confirm()` dialog.
- **Do** keep uppercase tracked text (`letter-spacing: 0.06em; text-transform: uppercase`) confined to course-section dividers in the dashboard. That is its one sanctioned use.

### Don't:
- **Don't** introduce a second accent color. Clarity Indigo is the only non-semantic accent in the system. A new hue — even as a "secondary accent" — breaks The One Voice Rule.
- **Don't** use gradient text (`background-clip: text` with a gradient fill). This is prohibited regardless of context.
- **Don't** replicate the generic SaaS productivity aesthetic: pastel blobs, rounded gradients, feature-highlight carousels, "empower your workflow" copy, or Asana/Monday-style milestone celebrations.
- **Don't** add gamification elements: streaks, achievement badges, confetti, progress celebrations. UniTrack is a tool, not a habit app.
- **Don't** drift the page background toward warm or sandy tones. Page Mist (`#F8FAFC`) is cool-tinted; any warmth in new surfaces must be explicitly justified.
- **Don't** add uppercase tracked eyebrows above every section on the landing page. Course-section headers in the dashboard are structural, not decorative. The landing page has no equivalent structural need.
- **Don't** extend the left-stripe border pattern (`border-left > 1px` as a colored accent). The existing inbox-alert `border-left: 4px solid var(--warning)` is a known debt — replace with a full tinted background border or a leading icon when restyling that component.
- **Don't** nest cards inside cards. Task cards live inside page containers; they do not contain child cards.
- **Don't** apply Hover Lift shadow to non-interactive elements. Elevation implies clickability.
