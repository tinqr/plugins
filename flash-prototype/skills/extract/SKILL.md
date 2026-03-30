---
name: extract
description: Extract a production-ready Figma design and match every value to Flash production tokens with pixel accuracy. Full figma-to-code protocol -- subagent extraction, precise color/typography/spacing matching against Flash's token set, icon SVG pipeline (download, clean, classify mono/multicolor), layout model analysis. Produces a design_spec.md that the build skill consumes. Use when implementing a polished Figma design as a Flash prototype, when someone provides a Figma URL for a finished design, says "extract this design", "implement this Figma", or "build this from the design". This is for production-ready designs with intentional colors -- for rough wireframes, use /flash-prototype:adapt instead.
---

# Extract: Production Figma Design to Flash Spec

You are extracting a polished Figma design and matching every visual value to Flash production tokens. The design has intentional colors, typography, and spacing -- your job is precise matching, not creative interpretation.

This skill implements the figma-to-code protocol (v2): per-widget extraction via subagent, values written to a persistent spec file, implementation from that file. The key principle is that extraction and implementation are interleaved, not sequential -- you read Figma for the widget you're building right now, build it, verify it, move on.

## Phase 0: Validate the Figma reference

The user provides a file key and node ID. Work with exactly what they give you.

- If they provide a node ID: go straight to extraction on that exact node. Do NOT explore other nodes, pages, or frames in the file.
- If the node ID is invalid or inaccessible: **stop and tell the user.** Ask them to verify the Figma URL and share the correct node ID. Do not search the file for alternatives or pick a different node.
- If they provide only a file key (no node): call `get_metadata` to list top-level frames, show them the list, and ask which one to extract.

The user's Figma reference is the source of truth. Never substitute, explore, or improvise.

## Phase 1: Per-Widget Extraction Loop

For each widget or screen section, repeat this cycle:

### 1a. Read via subagent

Dispatch a subagent to call `get_design_context`. The raw output is React/Tailwind reference code that consumes massive context -- the main conversation must never see it.

**Subagent prompt:**

> Call `get_design_context` with fileKey `{KEY}` and nodeId `{NODE}` (clientLanguages: dart, clientFrameworks: flutter). From the result, return a compact summary with:
>
> 1. **Visual layout description** from the screenshot -- what's where, visual hierarchy
> 2. **Every node ID** for meaningful elements (for fix cycles)
> 3. **All colors** as exact hex+alpha -- backgrounds, text, borders, icons, accents
> 4. **Typography** -- font family, weight, size, line height, letter spacing, font features for each text element
> 5. **Spacing** -- padding, margins, gaps between every pair of adjacent elements in exact px. If Figma shows 0px gap, report "0px -- spacing from line-height only." Never leave internal spacing unspecified.
> 6. **Border radii** -- every radius value
> 7. **Shadows** -- color, blur, offset if any
> 8. **Component structure** -- parent-child nesting, conditional states (selected/unselected, expanded/collapsed)
> 9. **Layout model** -- scrollable or fixed-viewport? Pinned elements (CTA at bottom, header at top)? How is space between sections handled?
> 10. **Icons** -- every icon with set name (e.g., `solar:chart-bold-duotone`), size, monochrome/multicolor classification, colors used, and asset download URL
> 11. **Explicit dimensions** -- widths/heights where Figma specifies them
> 12. **Design token names** if present in the output
>
> Do NOT return the raw React/Tailwind code. Return a structured summary only.

### 1b. Match colors to Flash tokens

For each color the subagent reports, find the exact or nearest Flash token. Flash tokens are in `lib/flash/theme/color.dart`:

**Primary palette:**
| Token | Hex | Match when design shows |
|-------|-----|------------------------|
| `primary` | #2C2C84 | Deep blue/purple brand color |
| `darkNight` | #1F1F49 | Dark navy backgrounds |
| `secondary` | #CBF15E | Lime green accents, CTAs |
| `dayBreak` | #C8D1FF | Lavender, secondary text on dark |
| `lightNight` | #4A4AC6 | Mid-blue, lighter brand variant |
| `primaryT3` | #5F5FF2 | Brighter blue/purple |

**Grays:**
| Token | Hex | Match when design shows |
|-------|-----|------------------------|
| `gray1` | #F9F9F9 | Near-white backgrounds |
| `gray2` | #F5F5F5 | Light card backgrounds |
| `gray3` | #F3F2F2 | Borders, input outlines |
| `gray4` | #DBDADA | Disabled states |
| `gray5` | #C6C6C6 | Outlined button borders |
| `gray6` | #A2A2A2 | Placeholder text, muted labels |
| `gray8` | #787878 | Secondary text on light |
| `gray9` | #707070 | Darker secondary text |
| `greyLight` | #ACB1B5 | Hint text |
| `greyDark` | #5F7A90 | Dark secondary |

**Accent colors:**
| Token | Hex | Match when design shows |
|-------|-----|------------------------|
| `red` | #EE423A | Error, destructive |
| `tangelo` | #FE5900 | Warnings, orange accents |
| `honeyComb` | #FBB325 | Gold, yellow highlights |
| `boskyGreen` | #51C073 | Success, positive change |
| `seaGreen` | #00ABA4 | Teal accents |
| `hydra` | #439FD8 | Blue accents |
| `candy` | #ED3B7C | Pink accents |

**Matching rules:**
- **Exact match** (within ~5 hex units): use the token directly
- **Close match** (within ~20 hex units): use the nearest token, note the deviation in the spec
- **No match**: flag it with `// FLAGGED: #HEXVAL not in color.dart -- needs decision`. The design may need a new token, or there may be a match you're not seeing. Don't silently invent colors.

**Contrast rules -- verify after matching:**

Some tokens only work on specific backgrounds. Check every text/icon color against its background:

| Token | Works on | Does NOT work on |
|-------|----------|-----------------|
| `dayBreak` (#C8D1FF) | Dark backgrounds (darkNight, primary) | White or light backgrounds -- light lavender has no contrast on white |
| `secondary` (#CBF15E) | Dark backgrounds (as text/icon) | White backgrounds (as text) -- lime green on white is unreadable |
| `Colors.white` | Dark backgrounds only | Light backgrounds |
| `gray6` (#A2A2A2) | White or light backgrounds | Dark backgrounds -- disappears |
| `primary` (#2C2C84) | White or light backgrounds | Very dark backgrounds -- invisible |

If a matched token violates contrast on its background, flag it in the spec rather than silently using it.

### 1c. Match typography to textTheme

Map each text element to the closest `Theme.of(context).textTheme` style:

| Size | Weight | textTheme style |
|------|--------|----------------|
| 36px | bold (w700) | `displayLarge` |
| 28px | bold (w700) | `displayMedium` |
| 28px | semibold (w600) | `displaySmall` |
| 24px | bold (w700) | `headlineLarge` |
| 20px | bold (w700) | `headlineMedium` |
| 20px | medium (w500) | `headlineSmall` |
| 18px | semibold (w600) | `titleLarge` |
| 18px | medium (w500) | `titleMedium` |
| 16px | semibold (w600) | `titleSmall` |
| 16px | medium (w500) | `labelLarge` |
| 16px | regular (w400) | `labelMedium` |
| 14px | semibold (w600) | `labelSmall` |
| 14px | medium (w500) | `bodyLarge` |
| 12px | semibold (w600) | `bodyMedium` |
| 12px | medium (w500) | `bodySmall` |

All styles use Raleway with lining numerals (fontFeature `lnum`), 1.4 line-height. The theme applies `bodyColor: primary` -- override with `.copyWith(color: ...)` for non-default text colors.

**If a design uses a size/weight combo that doesn't match any style**, flag it in the spec. Don't use raw `TextStyle()`.

### 1d. Map to Flash components

When the extracted element matches a production component, note it:

| Design element | Flash component | Import |
|---------------|----------------|--------|
| Primary CTA button | `PrimaryButton` | `buttons/primary_button.dart` |
| Secondary/outlined button | `SecondaryButton` | `buttons/secondary_button.dart` |
| Close X icon button | `CloseIconButton` | `buttons/close_icon_button.dart` |
| Bottom sheet container | `FlashBottomSheet` | `bottom_sheet/flash_bottom_sheet.dart` |
| Present a sheet | `showModal()` | `bottom_sheet/show_modal.dart` |
| Sheet header row | `BottomSheetHeader` | `bottom_sheet/bottom_sheet_header.dart` |
| Drag handle bar | `BottomSheetHandle` | `bottom_sheet/bottom_sheet_handle.dart` |
| Sheet close button | `BottomSheetCloseButton` | `bottom_sheet/bottom_sheet_close_button.dart` |
| Status badge/tag | `Badge` | `badge.dart` |
| Filter/selection chip | `FlashChip` | `flash_chip.dart` |
| Page scaffold + AppBar | `ScreenLayout` | `screen_layout.dart` |

All imports prefix with `flash/components/`.

### 1e. Extract icons

For each icon in the design:

1. **Download the SVG** from the asset URL the subagent returned
2. **Clean for flutter_svg:**
   - Replace `fill="var(--fill-0, #2C2C84)"` with the fallback hex: `fill="#2C2C84"`
   - Replace `width="100%" height="100%"` with numeric values from the `viewBox`
   - Remove `style="display: block;"` attributes
3. **Save to `assets/icons/`** with a descriptive filename matching the icon set name (e.g., `chart_bold_duotone.svg`)
4. **Classify:**
   - **Monochrome** (single fill color) → code will use `ColorFilter.mode(color, BlendMode.srcIn)`
   - **Multicolor** (multiple fills/strokes -- names with "color", "twotone", "flat") → code renders without ColorFilter
5. **Verify identity** -- confirm the saved SVG matches the Figma source. A `streamline-color:gift-2-flat` must not look like a `solar:gift-bold`. The icon set name is the source of truth.
6. **Register `assets/icons/`** in `pubspec.yaml` (Flutter asset dirs are NOT recursive)

### 1f. Write to spec file

After extraction, write (or update) `design_spec.md` in the prototype directory:

```markdown
# <Feature Name> -- Design Spec

Source: Figma file `<file_key>`, node `<node_id>`
Extracted: <date>

## Layout Model
- Scrollable / Fixed viewport
- Pinned elements: [list]
- Background: [dark/light/mixed]

## Color Mapping
| Element | Design hex | Flash token | Notes |
|---------|-----------|-------------|-------|
| Screen bg | #1F1F49 | darkNight | exact |
| Header text | #FFFFFF | Colors.white | |
| CTA bg | #CBF15E | secondary | exact |
| ... | ... | ... | |

## Typography Mapping
| Element | Design spec | textTheme style | Color override |
|---------|------------|-----------------|----------------|
| Page title | 24/bold | headlineLarge | .copyWith(color: Colors.white) |
| Subtitle | 14/w500 | bodyLarge | .copyWith(color: dayBreak) |
| ... | ... | ... | ... |

## Component Mapping
| Design element | Flash component | Custom widget needed? |
|---------------|----------------|-----------------------|
| Main CTA | PrimaryButton | No |
| Rate card | -- | Yes: RateCard |
| ... | ... | ... |

## Icons
| Name | File | Set | Color mode |
|------|------|-----|------------|
| wallet | assets/icons/wallet_bold.svg | solar:wallet-bold | monochrome |
| ... | ... | ... | ... |

## Spacing
[All padding, margin, gap values extracted]

## Node IDs
[For fix cycles -- re-read these nodes when issues are flagged]
```

### 1g. Implement the widget

Build the widget using values from the spec file. Full attention on code quality. The context window is free for implementation thinking because extraction data lives in the file.

### 1h. Spot-check

Call `get_screenshot` on the Figma node (use the saved node ID). Compare against what you built. Fix obvious discrepancies before moving to the next widget.

## Fix Protocol

When issues are flagged after building:

1. **Re-read the Figma node** via subagent. No guessing from memory.
2. **For each issue**, find the exact Figma value, compare to code, fix it.
3. **While in that widget**, check the whole widget against the node -- catch anything else that's off.
4. **Update the spec file** if any value was wrong.
5. **Screenshot compare** after fixing -- confirm before claiming done.

A fix cycle always re-reads Figma. The feedback tells you WHERE to look; Figma tells you WHAT'S RIGHT.

## Hard Rules

- Never implement a widget without reading its Figma node first.
- Never fix a flagged issue without re-reading the Figma node.
- Never claim a fix is done without screenshot comparison.
- Extraction goes to a file (design_spec.md), not just context memory.
- When in doubt, re-read the node. One extra API call costs seconds; rework costs sessions.

## Handoff

After extraction is complete, recommend the build skill:

> "Design spec written to `design_spec.md`. Use `/flash-prototype:build` with Superpowers to implement the prototype -- it knows Flash's component library and conventions."
