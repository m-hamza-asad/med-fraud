# Shahai Design-System Audit for Med Fraud

Status: implementation brief derived from the adjacent, read-only `Design-System` repository on 2026-09-15. This file does not modify or supersede that system.

## Authority and implementation posture

Use this order whenever sources differ:

1. `Design-System/locked-decisions.md` — principles, roles, and direction; highest authority.
2. `Design-System/tokens/` — canonical Design Tokens v1.0 exact values.
3. `foundations/`, `products/`, `visualization/`, and `governance/` — usage and composition rules.
4. `lab/` — historical evidence only.

The audit and presentation-audit describe old artifacts, not the target. Several domain documents retain old “deferred” wording in their main sections but resolve it under “Unresolved Specifications”; use the canonical tokens for resolved values. Do not invent values for gaps explicitly still marked unresolved.

## Product direction

The app should feel like dark, precise, calm, intelligent, high-trust enterprise software where complexity feels controlled. It is dark-first and theme-ready, not “dark aesthetic”: no pure black everywhere, neon, purple AI gradients, glowing UI, default glassmorphism, oversized radii, giant shadows, or decorative technology motifs.

For a medical-fraud workflow, trust is disqualifying rather than merely one quality score. Evidence, uncertainty, data provenance, ownership, approval state, and human control must remain visible. Never make model output look more certain, autonomous, or complete than it is.

## Canonical implementation tokens

Color token values below are canonical HSL triples intended for `hsl(var(--token))`-style use.

### Brand and geometry

| Role | Value | Usage |
|---|---:|---|
| Brand navy primitive | `#0C0059` / `248 100% 17%` | Brand source value; too dark for most direct UI surfaces |
| Signature cream | `#FEF7BB` / `54 97% 86%` | Scarce focus/importance signal, never default primary CTA or warning |
| Near-black anchor | `248 18% 2%` | High-authority moments only |
| Pure white | `0 0% 100%` | Light raised surface |
| Radius xs/sm/md/lg/xl | `4/8/10/14/16px` | Controlled soft geometry; inner radius generally tighter than parent |
| Pill radius | `999px` | Status chips, tags, badges, filters only |
| Hairline | `1px` | Subtle borders and selected-row boundary |

### Dark theme (default)

| Role | HSL triple |
|---|---:|
| Canvas | `248 14% 7%` |
| Base panel/card | `248 12% 10%` |
| Raised/nested surface | `248 12% 13%` |
| Inset/input well | `248 14% 5%` |
| Overlay/popover/tooltip | `248 12% 16%` |
| Structural navy | `248 58% 22%` |
| Strong navy / primary action | `248 65% 28%` |
| Border subtle / strong | `248 11% 20%` / `248 11% 30%` |
| Text primary | `240 22% 97%` |
| Text secondary | `240 14% 75%` |
| Text tertiary | `240 10% 56%` (large/UI roles only; do not assume normal-text AA) |
| Text disabled | `240 8% 38%` plus disabled opacity token |
| Text inverse | `240 22% 9%` |
| Link / focus | `248 72% 75%` |

Use surface tone before borders, borders before shadows. Dark elevation is intentionally specified as shadow tint `248 38% 1%` plus alpha only: raised `.38`, popover `.42`, modal `.50`; blur/offset geometry was not approved, so do not fabricate it.

### Light theme (supported, not default)

| Role | HSL triple |
|---|---:|
| Canvas / base / subtle | `45 25% 97%` / `45 20% 94.5%` / `45 16% 91.5%` |
| Raised | pure white |
| Structural navy | `248 55% 24%` |
| Text primary / secondary / tertiary / muted | `245 20% 10%` / `245 10% 28%` / `245 7% 44%` / `245 6% 58%` |
| Border default / divider | `45 10% 84%` / `45 8% 89%` |

Light shadows: raised `0 1px 2px hsl(45 20% 15% / .08)`; popover `0 4px 14px hsl(45 20% 15% / .12)` plus hairline border; modal `0 16px 40px hsl(45 20% 15% / .16)` plus hairline border.

### Semantic status

Brand and functional colors are separate. Cream is not warning yellow. Status always combines text label and/or shape/icon with color.

Dark status fills use base color at `.12` alpha and borders at `.35`; text/icons use `fg`:

| State | Foreground | Base | Strong |
|---|---:|---:|---:|
| Info | `205 68% 64%` | `205 68% 58%` | `205 72% 30%` |
| Success | `152 48% 60%` | `152 48% 48%` | `152 52% 26%` |
| Warning | `38 82% 64%` | `38 82% 58%` | `38 86% 30%` |
| Error | `357 72% 66%` | `357 72% 60%` | `357 76% 32%` |
| Pending | `230 14% 66%` | `230 14% 62%` | `230 18% 32%` |
| Neutral structural | `220 6% 60%` | — | — |

Light status fills use `.08` and borders `.35`; foreground/strong: info `205 75% 32%` / `205 78% 28%`; success `152 55% 26%` / `152 58% 22%`; warning `38 90% 27%` / `38 92% 24%`; error `357 70% 38%` / `357 72% 32%`; pending `230 15% 40%` / `230 18% 34%`.

### Typography and spacing

Poppins is the sole UI and content typeface. Radnika Next is exclusively for the lowercase Shahai wordmark, ideally as a controlled asset. Weight roles: reading `400`, interface `500`, heading `600`, display `700` (rare).

| Product role | Size / line-height / weight / tracking |
|---|---|
| Display | `56px / 1.08 / 700 / -0.02em` — rare impact moments |
| H1 | `40px / 1.18 / 600 / -0.015em` — one workspace title per screen |
| H2 | `28px / 1.28 / 600 / -0.01em` |
| H3 | `20px / 1.35 / 600` |
| H4 | `16px / 1.4 / 600` |
| Body large | `17px / 1.65 / 400` |
| Body | `15px / 1.6 / 400` |
| Body small | `13px / 1.55 / 400` |
| UI label | `13px / 1.3 / 500` |
| Metadata | `12px / 1.4 / 400` |
| Caption | `11px / 1.4 / 400` |
| KPI | `32px / 1.1 / 600 / -0.01em` |
| Table header | `12px / 1.3 / 600 / 0.02em` |
| Table body | `13px / 1.45 / 400` |

Spacing roles: micro `4px`, inline `8px`, control `10px`, element `16px`, group `24px`, section `40px`, composition `56px`. Standard control height `38px`, compact control `32px`, table rows `44px` comfortable / `32px` compact, nav item `40px`, chip `22px`, icon button `32px`. Control padding is `0.65rem 1rem`; card padding `1.375rem`.

Use ALL CAPS with tracking only for structural/navigation language; use sentence case for communication. Establish hierarchy through size, weight, spacing, contrast, alignment, placement, tracking, and line-height before adding containers.

### Icons and the Framed Line anchor

Use `lucide-react`: `16px` standard with stroke `1.75`; `13px` compact with stroke `2`; icon/text gap `8px`. Icons aid recognition, not decoration. Reserve Sparkles exclusively for AI/model semantics, not generic “magic.”

The approved numeral/sequence grammar is Framed Line: `32px` frame, `1px` border, `4px` radius, `13px` tabular numeral at weight `600`, `14px` heading gap. Use it where numbering is a meaningful sequence/chapter/anchor, not as decoration.

## Layout and component guidance

### Composition and surfaces

- Choose Focus, Working, or Analytical density (mapping to Impact, Editorial, Dense). The likely default for case investigation is Analytical or Working, not indiscriminate compactness.
- Dense mode comes from rigorous grids, scan anchors, segmentation, stable alignment, strong hierarchy, and summary/detail separation—not shrinking everything.
- A screen gets one primary focal point. Attention hierarchy is Ambient → Normal → Important → Focus → Semantic.
- Group in this order: spacing/alignment → tonal surface difference → subtle border → elevation/shadow → stronger container.
- A card must convey ownership, behavior, a distinct data entity, or meaningful grouping. Avoid “carditis.”
- Navy marks structural, selected, contextual, analytical, and active-workflow regions. Cream marks the single scarce focus/important exception.
- Navigation should recede after orientation; the workspace dominates. Support global, local, and contextual navigation. On constrained widths, collapse/condense navigation while keeping it reachable.
- Responsive tables retain scan-anchor columns; defer supporting detail to expandable rows/details rather than blindly hiding columns or shrinking type.

Exact product breakpoints, sidebar dimensions, touch-target minimums, and formal responsive table priority rules remain unresolved. Base those choices on content and validate; do not claim they are canonical tokens.

### Actions, forms, and overlays

- Usually one dominant primary action; rank secondary, tertiary, and destructive actions.
- Labels describe the outcome: “Generate analysis,” “Approve claim decision,” “Create investigation,” not “Submit.”
- Every input needs a persistent visible label. Add helper text where expectations are not self-evident, attach specific errors to the field, group logically, and use progressive disclosure.
- Use persistent context panels for evidence, AI analysis, source documents, history, comments, approval, and versioning; this reduces modal overload.
- Reserve modal elevation for genuinely interruptive/high-authority decisions.

### Flagship investigation table

The table should support the relevant subset of sorting, filtering, search, selection, row actions, pagination, expandable rows, status, bulk actions, loading, empty/error states, and pinned columns. Provide Comfortable and Compact density controls.

Visually: restrained horizontal separators; minimal vertical rules; stable alignment; left-align text, right-align numbers; tabular numerals; clear headers; subtle hover; unmistakable selection. Use `44px`/`32px` row heights and the canonical type roles. Tables have equal status with charts when exact lookup and auditability matter.

### States, fraud findings, and AI assistance

- Empty states answer: what is this area, why is it empty, what should the user do next. No giant illustration filler.
- Use skeletons for predictable content and measurable progress where possible.
- AI progress should say what is happening and provide real counts, e.g. “Comparing claim evidence — 12 of 17 documents reviewed.”
- AI surfaces must expose: what it is doing; sources/data/tools used; output; uncertainty; required human action; next step.
- Keep evidence attached to each claim/finding. Prefer a source/evidence context panel and exact citations over a generic sources list.
- Expose recommendation, evidence, key factors, assumptions, limitations, and alternatives; never expose raw hidden model reasoning as a feature.
- Preserve distinct agent states: Queued, Running, Waiting for input, Review required, Approval required, Approved, Executing, Completed, Failed, Cancelled.
- “Approved” (human decision) must be distinct from “Completed” (system execution); “Failed” must be distinct from “Cancelled.” Make responsibility for the next action obvious.

## Interaction and accessibility

- Target WCAG 2.2 AA. Every interactive element must be keyboard reachable and have a visible focus state.
- Dark-theme focus ring: `2px` at `2px` offset, color `248 72% 75%`; do not default focus to cream.
- Disabled opacity is `.4`. Selected fill alpha `.35`, border `248 65% 28%` at `1px`.
- Primary hover/pressed: `248 65% 31%` / `248 65% 26%`. Secondary hover/pressed: `248 12% 15.5%` / `248 12% 12%`. Row hover: `248 12% 12%`.
- Motion communicates state, hierarchy, or relationship and should feel responsive, not animated. Hover `140ms ease`, press/focus `100ms ease`, disclosure `180ms ease-out`, popover `140ms ease-out`, panel/toast-in `200ms ease-out`, toast-out `150ms ease-in`, modal `180ms ease-out` with opacity + `4px` translate only. No scale/bounce/springs. Checkbox/radio and row selection are instant.
- Under `prefers-reduced-motion: reduce`, zero every duration.
- Never encode fraud severity, claim status, agent state, chart series, validation, or approval solely by color. Add labels and suitable icon/shape/pattern/annotation.
- Provide text equivalents/alt text for meaningful imagery and accessible data-table alternatives for complex charts.
- Minimum touch target is still explicitly unresolved; choose a defensible accessible value during implementation and record it as app-local pending design-system approval.

## Data visualization

Meaning determines form. Use tables for exact lookup/auditability, bars for magnitude comparison, lines for change over time, scatterplots for relationships/outliers, and waterfalls for contribution to change. Pie/donut is exception-only. Titles should state the finding (“Duplicate billing clusters increased after provider reassignment”), while the chart supplies evidence.

Use the canonical theme-specific six-series palette, not the brand palette:

| Series | Dark | Light |
|---|---:|---:|
| Blue | `228 58% 54%` | `228 58% 42%` |
| Teal | `158 50% 36%` | `158 55% 32%` |
| Amber | `38 70% 55%` | `38 75% 34%` |
| Violet | `300 45% 46%` | `300 48% 40%` |
| Slate | `225 8% 70%` | `225 15% 42%` |
| Terracotta | `15 55% 52%` | `15 58% 38%` |

Direct-label every series; the documented blue/teal tritanopia residual risk makes redundant encoding mandatory. Chart geometry: `2px` standard line, `3px` emphasized line, `5px` point, `2px` top-only bar radius. Prefer direct labels at up to four series; use a legend at five or more. Strip unnecessary gridlines, axes, legends, ticks, precision, shadows, gradients, and ornament.

Sequential ramp (light → dark): `248 30% 88%`, `248 35% 72%`, `248 45% 56%`, `248 55% 40%`, `248 65% 24%`. For values printed inside ramp cells, use light text when cell lightness is below `55%`, dark text otherwise.

## Final review checklist

1. Skeleton: hierarchy still works without imagery, accent, icons, shadows, decoration.
2. Squint: first read, major groups, and primary action are obvious.
3. Grayscale: status and chart meaning survives without hue.
4. Removal: remove anything that does not reduce comprehension.
5. No-logo: still recognizably Shahai through type, hierarchy, composition, color behavior, geometry, and restraint.
6. Real content: test long provider/patient names, many diagnosis/procedure codes, missing values, large/negative/decimal amounts, multiple simultaneous statuses, source restrictions, overflow, loading, errors, approvals, permissions, and long tables.
7. Stress-test the system against dashboard, dense table, AI/agent workspace, detailed form, chart, settings, context panel/modal, loading, empty, error, and approval/review states.

## Primary source files consulted

- `locked-decisions.md`
- `tokens/README.md`
- `tokens/primitives/{color,typography,geometry}.json`
- `tokens/semantic/{dark,light,status,interaction,elevation}.json`
- `tokens/mediums/product.json`
- `tokens/components/framed-line.json`
- `tokens/data-viz/{categorical,ramps,chart-geometry}.json`
- `tokens/{iconography,architecture-vocabulary}.json`
- Relevant `foundations/`, `products/`, `visualization/`, and `governance/` guidance
