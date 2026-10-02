---
name: Zomato AI Recommender
colors:
  surface: '#121222'
  surface-dim: '#121222'
  surface-bright: '#38374a'
  surface-container-lowest: '#0c0c1d'
  surface-container-low: '#1a1a2b'
  surface-container: '#1e1e2f'
  surface-container-high: '#29283a'
  surface-container-highest: '#333345'
  on-surface: '#e3e0f8'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e3e0f8'
  inverse-on-surface: '#2f2f40'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#ffb59d'
  on-secondary: '#5d1900'
  secondary-container: '#b83900'
  on-secondary-container: '#ffddd2'
  tertiary: '#e9c400'
  on-tertiary: '#3a3000'
  tertiary-container: '#c9a900'
  on-tertiary-container: '#4c3f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59d'
  on-secondary-fixed: '#390c00'
  on-secondary-fixed-variant: '#832600'
  tertiary-fixed: '#ffe16d'
  tertiary-fixed-dim: '#e9c400'
  on-tertiary-fixed: '#221b00'
  on-tertiary-fixed-variant: '#544600'
  background: '#121222'
  on-background: '#e3e0f8'
  surface-variant: '#333345'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system embodies an intelligent, late-night culinary exploration aesthetic. It blends cinematic dark mode with high-end glassmorphism and radiant energetic accents. The emotional goal is to transform food discovery from a transactional search into an intuitive, sensory-rich experience driven by conversational AI.

Key style pillars:
- **Atmospheric Depth:** Deep cosmic navy gradients create an immersive stage that makes food photography and vibrant UI nodes glow.
- **Luminous Frosted Glassmorphism:** Translucent multi-layered surfaces with precision light borders establish hierarchy without visual heaviness.
- **Kinetic Energy:** Subtle, breathing crimson-amber glowing pulses highlight AI-driven recommendations, live match ratings, and real-time culinary suggestions.

## Colors

The palette leverages a high-contrast relationship between deep nocturnal substrates and blazing culinary hues.

- **Primary Canvas & Backgrounds:** The base interface transitions smoothly from `#0A0A1A` (deep abyssal void) to `#1A1A2E` (midnight indigo) via a radial or subtle diagonal linear gradient.
- **Brand Core (Crimson to Ember):** `#E23744` (iconic vibrant red) blends into `#FF6B35` (radiant flame orange) across interactive CTAs, key AI badges, and active selections.
- **Secondary Accent (Amber/Gold):** `#FFD700` is reserved for rating stars, VIP culinary labels, Michelin/curated badges, and high-confidence AI match percentages.
- **Glass Surfaces:** Base containers use `rgba(255, 255, 255, 0.04)` to `rgba(255, 255, 255, 0.08)`, framed by `rgba(255, 255, 255, 0.12)` borders to preserve structure against saturated backgrounds.
- **Text & Content Tiers:** Text ranges from pure white `#FFFFFF` for primary headlines, to `#A0A5BA` for secondary meta/prompts, down to `#5A5E73` for tertiary markers.

## Typography

The typography pairs **Outfit** for headlines and brand expressions with **Inter** for conversational output, menus, and transactional density.

- **Outfit (Display & Headings):** Geometric, warm, and hyper-modern. It anchors the discovery cards, recommendation highlights, and AI conversational headers.
- **Inter (Body & Controls):** Impeccably legible at small scales in low-light conditions. Used across restaurant descriptions, filter tags, ingredient disclosures, and search input states.
- **Hierarchy Notes:** Use tight negative tracking on display titles (`-0.02em`) to reinforce premium editorial quality. Small uppercase tags (`label-sm`) require subtle positive letter spacing (`0.04em`) for crisp legibility over dark backgrounds.

## Layout & Spacing

A responsive 12-column fluid grid system governs the layout, adjusting down to 8 columns on tablet devices and 4 columns on mobile viewports.

- **Desktop (1200px+):** Max-width container of 1440px with generous margins (`3rem`) and fluid gutters (`1.5rem`). Layout accommodates a dual-pane conversational AI panel (40% width) alongside an interactive restaurant feed/map (60% width).
- **Tablet (768px - 1199px):** 8-column layout. The conversational bar docks to an expandable bottom drawer or top collapsible bar.
- **Mobile (<768px):** 4-column layout with compact edge margins (`1.25rem`) and reduced gutters (`1rem`). Restaurant cards convert to full-bleed swipeable horizontal carousels or single-column stacked feeds.
- **Rhythm Rules:** All layout padding, card interior spaces, and item clusters strictly adhere to a 4px/8px incremental cadence.

## Elevation & Depth

Visual hierarchy is constructed through luminous glass layering rather than traditional drop shadows.

- **Level 0 (Canvas Base):** Deep gradient canvas `#0A0A1A` blending into `#1A1A2E`.
- **Level 1 (Panels & Shells):** `rgba(255, 255, 255, 0.03)` with `backdrop-filter: blur(16px)` and a subtle `1px` border of `rgba(255, 255, 255, 0.08)`.
- **Level 2 (Cards & Modules):** `rgba(255, 255, 255, 0.06)` with `backdrop-filter: blur(24px)` and a `1px` edge highlight of `rgba(255, 255, 255, 0.12)`.
- **Level 3 (Modals, Popovers & Floating Bars):** `rgba(26, 26, 46, 0.85)` with `backdrop-filter: blur(32px)`, subtle outer glow `0 12px 40px rgba(0, 0, 0, 0.6)`, and a top-edge linear highlight running from `rgba(226, 55, 68, 0.4)` to `rgba(255, 107, 53, 0.1)`.
- **AI Recommendation Glow:** Key cards and match indicators project a soft ambient neon aura: `box-shadow: 0 0 24px -4px rgba(226, 55, 68, 0.35), 0 0 12px -2px rgba(255, 107, 53, 0.2)`. Pulsing animations cycle the glow spread smoothly from `12px` to `28px`.

## Shapes

The interface embraces a sleek, hyper-curved aesthetic calibrated to specific component scales:

- **Restaurant Cards & Containers:** Structured with standard `16px` (`rounded-lg`) corner radii to maintain soft, friendly boundaries against photographic media.
- **Search Bars & Form Inputs:** Set precisely at `12px` to produce refined, streamlined interactive fields.
- **Action Buttons & Chips:** Utilize high-curvature styling—interactive primary action buttons use full pill-capsule formats or `24px` radius values, while contextual filter tags use smooth rounded-pill envelopes.
- **Floating Controls & Avatars:** Fully circular (`50%` / 9999px) for quick visual scanning and gestural feel.

## Components

### Buttons
- **Primary / AI Action:** Pill shape (`24px` radius or full capsule). Saturated horizontal gradient background from `#E23744` to `#FF6B35`. Crisp white typography with an active glowing shadow (`0 4px 20px rgba(226, 55, 68, 0.4)`).
- **Secondary / Glass:** Pill shape. Background `rgba(255, 255, 255, 0.08)`, border `1px solid rgba(255, 255, 255, 0.15)`, text `#FFFFFF`. Hover triggers background brightness shift to `rgba(255, 255, 255, 0.14)`.
- **Ghost / Tertiary:** Transparent background, text `#A0A5BA`, hover transition to pure white text with background `rgba(255, 255, 255, 0.05)`.

### Chips & Badges
- **Filter Chips:** Capsule rounded, padding `6px 14px`. Idle state uses `rgba(255, 255, 255, 0.05)` with `1px solid rgba(255, 255, 255, 0.1)`. Selected state activates the primary gradient outline and a soft inner tint.
- **AI Match Badge:** Micro pill (`label-sm`). Background `linear-gradient(135deg, rgba(226, 55, 68, 0.2), rgba(255, 107, 53, 0.2))`, text `#FF6B35`, border `1px solid rgba(255, 107, 53, 0.4)`. Contains a glowing spark or star icon.
- **Rating Chip:** Dark amber glass pill with text `#FFD700` and an illuminated gold star glyph.

### Cards
- **Restaurant Discovery Card:** `16px` border-radius with `backdrop-filter: blur(20px)`, background `rgba(255, 255, 255, 0.05)`, and border `1px solid rgba(255, 255, 255, 0.1)`. High-aspect imagery pinned to the top with a bottom gradient fade into content. Hover state triggers a subtle scale lift (`translateY(-4px)`) and a radiant ember border accent.

### Inputs & Conversational Fields
- **AI Prompt Bar:** Height `56px`, `12px` border radius, frosted glass `rgba(255, 255, 255, 0.07)`, backdrop blur `24px`, border `1px solid rgba(255, 255, 255, 0.15)`. Active/focus state ignites a gradient border (`#E23744` to `#FF6B35`) accompanied by an outer ambient glow.
- **Checkboxes & Radios:** `12px` rounded check squircle and circular radio. Unchecked: `1px solid rgba(255, 255, 255, 0.3)`. Checked: filled with primary gradient, pure white glyph.

### Specialized AI Components
- **Recommendation Pulse Tile:** Featured cards highlighted by AI include an animated outer border pulse that cycles the primary ember gradient opacity from `40%` to `100%`.
- **Taste Profile Match Indicator:** Circular SVG progress ring colored in `#FFD700` and `#FF6B35` with percentage readout in Outfit semi-bold.