---
name: LintasNiaga Core
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393d'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c1f'
  surface-container: '#1e2023'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e7'
  on-surface-variant: '#b9cac3'
  inverse-surface: '#e2e2e7'
  inverse-on-surface: '#2e3034'
  outline: '#83948e'
  outline-variant: '#3a4a45'
  surface-tint: '#00e0bb'
  primary: '#ffffff'
  on-primary: '#00382d'
  primary-container: '#00ffd6'
  on-primary-container: '#00725e'
  inverse-primary: '#006b59'
  secondary: '#c8c5cc'
  on-secondary: '#303035'
  secondary-container: '#47464c'
  on-secondary-container: '#b6b4bb'
  tertiary: '#ffffff'
  on-tertiary: '#302f3a'
  tertiary-container: '#e3e1ef'
  on-tertiary-container: '#64636f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#00ffd6'
  primary-fixed-dim: '#00e0bb'
  on-primary-fixed: '#002019'
  on-primary-fixed-variant: '#005142'
  secondary-fixed: '#e4e1e9'
  secondary-fixed-dim: '#c8c5cc'
  on-secondary-fixed: '#1b1b20'
  on-secondary-fixed-variant: '#47464c'
  tertiary-fixed: '#e3e1ef'
  tertiary-fixed-dim: '#c7c5d3'
  on-tertiary-fixed: '#1b1b25'
  on-tertiary-fixed-variant: '#464651'
  background: '#111317'
  on-background: '#e2e2e7'
  surface-variant: '#333539'
typography:
  display-mono:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: -0.01em
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  data-tabular:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1'
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  element-gap: 8px
---

## Brand & Style

The design system is engineered for high-stakes financial operations, merging the information density of Bloomberg terminals with the polished, developer-centric precision of Stripe. The aesthetic is "Technical Institutional"—it prioritizes rapid data ingestion and professional authority.

The UI style is **High-Contrast / Modern**, utilizing a dark-mode-first architecture to reduce eye strain during long-duration monitoring. It avoids unnecessary decorative elements, relying instead on structural grids, crisp borders, and a singular high-energy accent color to guide the eye toward critical actions and data trends. The emotional response is one of absolute control, precision, and modern sophistication.

## Colors

The palette is anchored in a deep charcoal environment to allow data points to "pop" with maximum legibility.

- **Primary Background**: The base layer of the application uses #06060A, creating a void-like depth.
- **Surface/Card**: Secondary layers use #111116 to create subtle structural containment.
- **Electric Teal**: Used exclusively for primary actions, success states, and data trendlines. It should be used sparingly to maintain its impact.
- **Borders**: A consistent #1A1A24 stroke defines the geometry of the interface.
- **Typography**: Text follows a strict hierarchy—Pure white-ish (#F0F0F5) for headers and values; muted slate (#8888A0) for metadata and labels.
- **Warning**: A specific yellow accent is reserved for "Caveat" states, typically applied as a 2px left-border on cards or alert containers.

## Typography

This design system utilizes **Inter** for its neutral, utilitarian character and excellent legibility at small sizes. 

To achieve the "Bloomberg" feel, numeric data should always use tabular lining (`tnum`) to ensure columns of figures align perfectly in tables and dashboards. Use `label-caps` for table headers and section descriptors to provide a clear structural anchor without overwhelming the primary data.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy within modular dashboard widgets. A strict 4px spacing scale ensures alignment across dense data sets.

- **Grid**: 12-column system with 16px gutters.
- **Density**: High. Vertical rhythm is tight, using 8px gaps between related input groups and 16px-24px between major functional blocks.
- **Alignment**: All data points must be top-aligned within rows to facilitate rapid scanning.

## Elevation & Depth

This design system eschews traditional soft shadows in favor of **Tonal Layering and Crisp Outlines**. 

- **Level 0 (Base)**: #06060A.
- **Level 1 (Cards/Panels)**: #111116 with a 1px solid border of #1A1A24.
- **Level 2 (Modals/Popovers)**: #16161E with a slightly brighter border (#2A2A36) and a 0px blur, 8px offset "hard shadow" to mimic physical stacking without losing the digital-first aesthetic.
- **Interaction**: On hover, borders should transition from #1A1A24 to the Primary Teal (#00FFD6) at 30% opacity to provide immediate feedback.

## Shapes

The shape language balances modern approachability with professional rigidity. 

- **Cards**: 12px radius provides a structured, containerized feel for major dashboard modules.
- **Buttons & Inputs**: 8px and 6px respectively, creating a sharper, more "active" appearance for interactive elements.
- **Data Points**: Graphs and sparklines use 2px stroke widths with no rounding on the joints to emphasize mathematical precision.

## Components

### Buttons
- **Primary**: Solid #00FFD6 background with #06060A text. No gradient. 
- **Secondary**: Ghost style. 1px stroke of #1A1A24 with #F0F0F5 text.
- **Critical**: #FFD600 (Warning Yellow) stroke only for high-consequence caveats.

### Cards & Modules
All containers use the #111116 background. Dashboard widgets feature a 24px header area with a bottom-border of 1px #1A1A24. If a card contains a "Warning" or "Caveat," apply a 4px solid #FFD600 border to the left edge.

### Charts & Visualization
- **Area Charts**: Use the Primary Teal for the trendline (2px). The fill should be a linear gradient from #00FFD6 at 20% opacity to #00FFD6 at 0% opacity.
- **Grid Lines**: Horizontal and vertical grid lines within charts must use #1A1A24 at 0.5px thickness.

### Input Fields
Inputs are dark-filled (#06060A) to contrast against the card background (#111116). Focus state is indicated by a 1px #00FFD6 border glow.

### Data Tables
Rows use a subtle zebra-striping or a bottom-border of 1px #1A1A24. Header cells use `label-caps` typography with #8888A0 color.