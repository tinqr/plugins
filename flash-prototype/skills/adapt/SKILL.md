---
name: adapt
description: Adapt a rough Figma wireframe into Flash's visual language for prototype building. Creatively maps wireframe placeholder colors to Flash production tokens (dark backgrounds become Flash navy, white stays white, accents become lime green), extracts layout structure and icons, and produces a build-ready spec. Use when working from wireframes (rough layouts with placeholder colors), when someone says "adapt my wireframe", "turn this wireframe into Flash", "map this to Flash colors", or during workshop sessions where participants wireframed ideas. For polished production-ready designs with intentional colors, use /flash-prototype:extract instead.
---

# Adapt: Wireframe to Flash Prototype Spec

You are reading a rough Figma wireframe and creatively adapting it to look like a real Flash screen. Wireframes use placeholder colors -- black, white, gray. Flash has a distinctive visual identity. Your job is to translate the wireframe's **visual intent** (what's a background, what's a heading, what's an accent) into Flash's palette.

This is creative mapping, not pixel-accurate matching. A wireframe's dark gray rectangle becomes `darkNight`. Its green button becomes `secondary`. Its light text becomes `dayBreak`. The result should feel like it belongs in the Flash app.

## When to use this vs `/flash-prototype:extract`

- **This skill (`adapt`)**: wireframes, rough layouts, Figma MCP output, workshop prototypes, anything with placeholder/generic colors
- **`extract`**: polished Figma designs with intentional colors that should be matched precisely to tokens

## Step 0: Validate the Figma reference

The user provides a file key and node ID. Work with exactly what they give you.

- If the node ID is invalid or inaccessible: **stop and tell the user.** Ask them to verify the Figma URL and share the correct node ID. Do not search the file for alternatives, explore other pages, or pick a different node.
- If they provide only a file key (no node): call `get_metadata` to list top-level frames, show them the list, and ask which one to adapt.
- Never substitute a different node or file. The user's reference is the source of truth.

## Step 1: Read the wireframe via subagent

Dispatch a subagent to extract the wireframe from the exact node provided. The raw `get_design_context` output stays in the subagent.

**Subagent prompt:**

> Call `get_design_context` with fileKey `{KEY}` and nodeId `{NODE}` (clientLanguages: dart, clientFrameworks: flutter). From the result, return a compact summary with:
>
> 1. **Visual layout description** -- what's where, what feels like the main content area, what feels like navigation, what feels like a CTA
> 2. **All node IDs** for meaningful elements
> 3. **All colors** as hex -- note which elements use each color
> 4. **Typography** -- approximate sizes and weights per text element
> 5. **Spacing** -- padding, margins, gaps in px between all adjacent elements. If 0px, say so explicitly.
> 6. **Border radii**
> 7. **Component structure** -- nesting, what wraps what
> 8. **Layout model** -- scrollable or fixed? Pinned elements?
> 9. **Icons** -- any icons with set names, sizes, and asset download URLs
> 10. **Explicit dimensions**
>
> Do NOT return the raw React/Tailwind code.

## Step 2: Classify the screen palette

Before mapping individual colors, determine the overall palette intent:

**Light screen** (default -- most Flash screens are white/light):
- Background → `Colors.white`
- Primary text → `primary` (#2C2C84, automatic via theme -- no override needed)
- Secondary text → `gray6` (#A2A2A2) or `greyLight` (#ACB1B5)
- Cards/elevated surfaces → `gray1` (#F9F9F9) or `gray2` (#F5F5F5)
- Accents/CTAs → `primary` background with `secondary` text (default ElevatedButton theme)
- Borders → `gray3` (#F3F2F2)
- This is the default. Flash is primarily a white app. When in doubt, go light.

**Dark screen** (only specific screens like home, gold rates use this):
- Background → `darkNight` (#1F1F49) or `primary` (#2C2C84)
- Primary text → `Colors.white`
- Secondary text → `dayBreak` (#C8D1FF)
- Cards/elevated surfaces → `primary` on darkNight bg, or `expenseCardColor` (#3C3D90)
- Accents/CTAs → `secondary` (#CBF15E, lime green)
- Borders → `dayBreak` with alpha
- Only use this when the wireframe clearly shows a dark/black background. It's the exception, not the default.

**Mixed screen** (dark header + light content):
- Apply dark rules to the dark section (usually a hero/header area)
- Apply light rules to the content section below
- The transition is usually at a clear boundary (header gradient ends, white content starts)

## Step 3: Map colors by role

Go through each color the subagent reported and assign a Flash token based on what it does in the layout, not what hex it is:

| Wireframe role | Dark screen token | Light screen token |
|---------------|-------------------|-------------------|
| Page background | `darkNight` | `Colors.white` |
| Card/surface background | `primary` or `expenseCardColor` | `gray1` or `gray2` |
| Primary text | `Colors.white` | `primary` (theme default) |
| Secondary/muted text | `dayBreak` | `gray6` or `greyLight` |
| Heading text | `Colors.white` | `primary` (theme default) |
| Hero number (big amount) | `Colors.white` | `primary` |
| CTA button background | `secondary` | `primary` |
| CTA button text | `primary` | `secondary` |
| Positive change (+ arrow) | `boskyGreen` (#51C073) | `boskyGreen` |
| Negative change (- arrow) | `red` (#EE423A) | `red` |
| Border/divider | `dayBreak` at 40% alpha | `gray3` |
| Icon (default) | `Colors.white` or `dayBreak` | `primary` |
| Icon (accent) | `secondary` | `secondary` |
| Input field border | `gray3` (theme handles this) | `gray3` (theme handles this) |
| Disabled element | `gray4` | `gray4` |
| Badge/chip background | `dayBreak` at 20% alpha | `gray2` |

**Contrast rules -- these override the table above:**

Some Flash tokens only work on specific backgrounds. Getting this wrong makes text unreadable.

| Token | Works on | Does NOT work on | Why |
|-------|----------|-----------------|-----|
| `dayBreak` (#C8D1FF) | Dark backgrounds (darkNight, primary) | White or light backgrounds | Light lavender on white has no contrast |
| `secondary` (#CBF15E) | Dark backgrounds (as text/icon) | White backgrounds (as text) | Lime green text on white is hard to read |
| `Colors.white` | Dark backgrounds | White backgrounds (obviously) | |
| `gray6` (#A2A2A2) | White or light backgrounds | Dark backgrounds | Medium gray disappears on dark |
| `greyLight` (#ACB1B5) | White or light backgrounds | Dark backgrounds | Same issue |
| `primary` (#2C2C84) | White or light backgrounds | Very dark backgrounds | Dark blue on dark navy is invisible |

**The rule:** if you're about to put light-colored text (`dayBreak`, `secondary`, white) on a light background, stop -- use `primary`, `gray6`, or `greyDark` instead. If you're about to put dark text (`primary`, `gray6`) on a dark background, stop -- use `Colors.white` or `dayBreak` instead.

**When the wireframe uses a color that doesn't fit any role above**, ask yourself: "What is this element doing?" A colored bar might be a progress indicator (`secondary`), a status badge (`boskyGreen`/`red`/`honeyComb`), or a decorative accent (`dayBreak` on dark only). Map by purpose.

## Step 4: Map typography

Wireframe text sizes are often approximate. Map to the nearest Flash textTheme style:

| Wireframe size | Flash style | Typical role |
|---------------|-------------|-------------|
| 32-40px bold | `displayLarge` (36px) | Hero amounts, big numbers |
| 26-30px bold | `displayMedium` (28px) | Section headers |
| 22-26px bold | `headlineLarge` (24px) | Page titles |
| 18-22px bold | `headlineMedium` (20px) | Card titles |
| 17-19px semibold | `titleLarge` (18px) | Labels, AppBar titles |
| 15-17px semibold | `titleSmall` (16px) | Button text |
| 15-17px medium | `labelLarge` (16px) | Body text |
| 13-15px semibold | `labelSmall` (14px) | Chips, badges |
| 13-15px medium | `bodyLarge` (14px) | Secondary body |
| 11-13px | `bodySmall` (12px) | Captions, hints |

Round generously. A wireframe showing 15px semibold becomes `titleSmall` (16px w600). Close enough wins over exact matching for wireframes.

## Step 5: Map components

Wireframe patterns → Flash production components:

| Wireframe shows | Likely Flash component |
|----------------|----------------------|
| Big colored button at bottom | `PrimaryButton` (pinned CTA) |
| Outlined/ghost button | `SecondaryButton` |
| X close button | `CloseIconButton` |
| Panel sliding up from bottom | `FlashBottomSheet` + `showModal()` |
| Handle bar at top of panel | `BottomSheetHandle` |
| Title row in a panel | `BottomSheetHeader` |
| Small tag/label | `Badge` |
| Pill-shaped filter/toggle | `FlashChip` |
| Full page with top bar | `ScreenLayout` |

Anything that doesn't match a production component becomes a custom widget -- note it in the spec.

## Step 6: Handle icons

Wireframes may have:
- **Real icons from Figma** (set names like `solar:...`) → extract, clean SVGs, save to `assets/icons/`
- **Placeholder shapes** (circles, squares representing icons) → note in spec as "needs icon -- [describe purpose]"
- **No icons** → note that standard Material navigation icons are sufficient

For real icons, follow the same SVG pipeline:
1. Download from asset URL
2. Clean: replace CSS vars with hex fallback, fix percentage dimensions, remove style attrs
3. Save to `assets/icons/` with descriptive filename
4. Classify mono/multicolor

For placeholders, the builder will need to either find appropriate icons or use simple Material icons.

## Step 7: Write the spec

Write `design_spec.md` in the prototype directory:

```markdown
# <Feature Name> -- Adapted Design Spec

Source: Figma wireframe `<file_key>`, node `<node_id>`
Adapted: <date>
Palette: Dark / Light / Mixed

## Layout Model
- Scrollable / Fixed viewport
- Pinned elements: [list]

## Color Adaptation
| Element | Wireframe | Flash token | Role |
|---------|-----------|-------------|------|
| Screen bg | #333333 | darkNight | page background |
| Header text | #FFFFFF | Colors.white | primary text on dark |
| CTA button | #4CAF50 | secondary | primary CTA accent |
| Card bg | #444444 | primary | elevated surface on dark |
| Muted text | #999999 | dayBreak | secondary text on dark |
| ... | ... | ... | ... |

## Typography Adaptation
| Element | Wireframe | textTheme style | Color override |
|---------|-----------|-----------------|----------------|
| Hero amount | 36px bold | displayLarge | .copyWith(color: Colors.white) |
| Section label | 18px semibold | titleLarge | .copyWith(color: dayBreak) |
| ... | ... | ... | ... |

## Component Mapping
| Wireframe element | Flash component | Custom? |
|------------------|----------------|---------|
| Bottom button | PrimaryButton | No |
| Rate row | -- | Yes: custom widget |
| ... | ... | ... |

## Icons
| Purpose | Source | File | Status |
|---------|--------|------|--------|
| Wallet icon | solar:wallet-bold | assets/icons/wallet_bold.svg | Extracted |
| Chart placeholder | (square) | -- | Needs icon |
| ... | ... | ... | ... |

## Spacing
[Spacing values from wireframe -- use as-is, wireframe spacing is usually intentional]

## Node IDs
[For reference if re-extraction needed]
```

## Step 8: Recommend next step

> "Your wireframe is adapted to Flash's visual language. The spec is at `lib/prototypes/<feature>/design_spec.md`.
>
> Next: use Superpowers to plan the build, then the `/flash-prototype:build` skill to implement it. Build knows Flash's component library and will use your adapted spec to produce widgets that look like the real app."

## Edge Cases

**Wireframe is entirely gray (no color at all):** Default to a light/white screen -- Flash is primarily a white app. Map the lightest gray to `Colors.white` (background), medium grays to `gray1`/`gray2` (cards), darker grays to `primary` (text). Only go dark if the wireframe explicitly uses a dark/black background or the participant says "this should be like the Flash home screen".

**Wireframe uses non-Flash brand colors (someone used red and blue):** Map by role, not by hue. Their red CTA becomes `secondary` (lime green) because it's the CTA. Their blue header becomes `darkNight` because it's the background. Function over color.

**Wireframe has multiple screens:** Adapt each screen separately in the spec. They may have different palette intents (one dark, one light).

**Participant wants to keep wireframe colors:** Respect their choice, but flag that production Flash uses specific tokens. Note original colors in the spec alongside Flash mappings so they can decide.

**Mixed intent is ambiguous:** When you can't tell if something is "dark screen" or "light screen with a dark header", ask the participant: "Is this a dark screen like the Flash home page, or a white screen with a colored header?"
