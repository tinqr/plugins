---
name: build
description: Build a Flutter prototype in the flash-prototypes repo using Flash production tokens and components. Provides Flash-specific building conventions -- project structure, color tokens, text styles, production components, dumb widget boundary -- for use alongside Superpowers workflow skills. Use when building prototypes, implementing wireframes, creating new features in ~/flutter-projects/flash-prototypes/, or when someone says "build my prototype", "implement this", "start building", "let's code this". Also triggers when Superpowers is planning or executing a build in flash-prototypes and needs domain-specific guidance.
---

# Build: Flash Prototype Construction

You are building a Flutter prototype that looks and feels like the real Flash app. This skill is **self-contained** -- it carries everything you need to know about building Flash prototypes. You do not need to read CLAUDE.md or any other project documentation. Everything is here.

Use **Superpowers** for the workflow (planning with `/superpowers:writing-plans`, building with subagent-driven development). This skill provides the domain rules that make Superpowers produce correct Flash code.

The goal: a participant who is a designer (not a developer) tells you what to build. You produce a working prototype on their phone that looks like it belongs in the Flash app.

## The Project

**Repo:** `~/flutter-projects/flash-prototypes/` -- a Flutter iOS project.
**Framework:** Flutter with Riverpod (`flutter_riverpod`) for state management.
**Font:** Raleway (via `google_fonts`) with lining numerals (`FontFeature.enable('lnum')`).
**Theme:** Light theme with `primary` (#2C2C84) as the dominant brand color. Configured in `lib/flash/theme/app_theme.dart`.
**Target:** iOS physical device only. Ignore Android warnings.
**Data:** Mock data only. No real APIs, no backend, no network requests.

**Architecture:**
```
main.dart → MaterialApp → LauncherScreen → [list of FeatureGroups]
                                              └→ PrototypeEntry → YourScreen
```
Each prototype is a self-contained feature in `lib/prototypes/<name>/`. The launcher is a two-tier picker: tap a FeatureGroup, then tap a PrototypeEntry to open the screen.

**Build and run commands:**
```bash
# Run on physical device (release mode for performance)
flutter run --release -d <device-id>

# Debug build (no deploy)
flutter build ios --debug

# Run tests
flutter test

# Analyze code (must pass clean)
flutter analyze
```

After each major piece of work, hot reload the app so the participant sees progress on their phone. This keeps engagement high.

## Before You Start

1. **Read the plan** -- the participant planned their prototype. Check their vault for the implementation plan. If there's no plan, use Superpowers to create one first.

2. **Read the spec** -- if `/flash-prototype:extract` or `/flash-prototype:adapt` was run, there's a `design_spec.md` in the prototype directory with color mappings, component mappings, and spacing values. If not, recommend running adapt first: "Let me read your wireframe from Figma first so I know what to build. I'll use `/flash-prototype:adapt` to get the spec."

3. **Check the repo** -- make sure `~/flutter-projects/flash-prototypes/` exists and builds. Run `flutter build ios --debug` to verify before starting feature work.

## Project Structure

Every prototype lives in its own directory:

```
lib/prototypes/<feature>/
  <feature>_screen.dart          -- Main screen (has Riverpod, orchestrates widgets)
  design_spec.md                 -- From /extract (color/component mappings)
  models/
    models.dart                  -- Data models (become domain entities in production)
    mock_data.dart               -- Hardcoded sample data (deleted in production)
  providers/
    <feature>_provider.dart      -- Riverpod state (becomes Bloc in production)
  widgets/
    widget_a.dart                -- Dumb widgets (port directly to production)
    widget_b.dart
```

Create this structure at the start. The directory name should be snake_case and descriptive (e.g., `savings_goal`, `price_alert`, `portfolio_dashboard`).

## The Dumb Widget Boundary

This is the most important architectural rule. Every widget in `widgets/` must be **dumb**:

- **Constructor params and callbacks only** -- data comes in through the constructor, actions go out through callbacks
- **No Riverpod imports** -- no `ref`, no `Provider`, no `ConsumerWidget` in widget files
- **No business logic** -- widgets render and handle interactions, nothing more

This exists because production teams need to extract these widgets and wire them to Bloc state management. If a widget depends on Riverpod, they have to rewrite it. If it's dumb, they just wire the constructor params to their Bloc and it works.

```dart
// GOOD -- dumb widget, ports to production as-is
class SavingsProgressCard extends StatelessWidget {
  final String goalName;
  final double currentAmount;
  final double targetAmount;
  final VoidCallback onAddMoney;

  const SavingsProgressCard({
    super.key,
    required this.goalName,
    required this.currentAmount,
    required this.targetAmount,
    required this.onAddMoney,
  });

  @override
  Widget build(BuildContext context) { ... }
}
```

```dart
// BAD -- Riverpod dependency, production team has to rewrite
class SavingsProgressCard extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goal = ref.watch(savingsProvider);  // Can't extract this
    ...
  }
}
```

**The screen does the wiring:** The `_screen.dart` file is a `ConsumerWidget` or `ConsumerStatefulWidget` that reads from providers and passes data down to dumb widgets. Orchestration logic (onboarding flows, sheet chaining, conditional reveals) lives in the screen, not in widgets.

## Color Tokens

Import from `package:flash_prototypes/flash/theme/color.dart`. Never use hardcoded hex values.

**Core palette:**

| Token | Hex | Use for |
|-------|-----|---------|
| `primary` | #2C2C84 | Deep blue -- brand color, text on light bg |
| `darkNight` | #1F1F49 | Dark navy -- dark screen backgrounds |
| `secondary` | #CBF15E | Lime green -- CTAs, accents, highlights |
| `dayBreak` | #C8D1FF | Lavender -- secondary text on dark backgrounds |
| `gray1` | #F9F9F9 | Lightest gray -- subtle backgrounds |
| `gray2` | #F5F5F5 | Light gray -- card backgrounds |
| `gray3` | #F3F2F2 | Gray -- borders, input outlines |
| `gray4` | #DBDADA | Medium gray -- disabled states |
| `gray5` | #C6C6C6 | Gray -- outlined button borders |
| `gray6` | #A2A2A2 | Dark gray -- placeholder text |
| `red` | #EE423A | Error, destructive actions |
| `tangelo` | #FE5900 | Warnings |
| `honeyComb` | #FBB325 | Gold highlights |
| `boskyGreen` | #51C073 | Success, positive change |

```dart
// GOOD
import 'package:flash_prototypes/flash/theme/color.dart';
Container(color: darkNight)
Text('Amount', style: textTheme.titleLarge?.copyWith(color: Colors.white))

// BAD
Container(color: Color(0xFF1F1F49))
Container(color: Colors.black)  // Flash doesn't use pure black
```

**If a color isn't in the token list -- STOP.** Don't invent tokens. Flag it:

```dart
// FLAGGED: not in production color.dart -- needs design decision
const _customHighlight = Color(0xFFE4E8FF);
```

## Text Styles

Always use `Theme.of(context).textTheme`. The full scale (all Raleway, 1.4 line-height):

| Style | Size | Weight | Use for |
|-------|------|--------|---------|
| `displayLarge` | 36 | bold | Hero numbers |
| `displayMedium` | 28 | bold | Section headers |
| `headlineLarge` | 24 | bold | Page titles |
| `headlineMedium` | 20 | bold | Card titles |
| `titleLarge` | 18 | w600 | AppBar titles, section labels |
| `titleSmall` | 16 | w600 | Button text |
| `labelLarge` | 16 | w500 | Body text |
| `labelSmall` | 14 | w600 | Chips, badges |
| `bodyLarge` | 14 | w500 | Secondary body |
| `bodySmall` | 12 | w500 | Captions, hints |

```dart
// GOOD
Text('Gold', style: Theme.of(context).textTheme.titleLarge)
Text('24K', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: dayBreak))

// BAD
Text('Gold', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600))
```

**On dark backgrounds**, text defaults to `primary` (dark blue) from the theme -- invisible. Always add `.copyWith(color: Colors.white)` or use `dayBreak` for secondary text.

## Production Components

These are already extracted in `lib/flash/components/`. Always check if one exists before building your own:

| Component | Import | Use for |
|-----------|--------|---------|
| `ScreenLayout` | `flash/components/screen_layout.dart` | Page scaffold with AppBar |
| `PrimaryButton` | `flash/components/buttons/primary_button.dart` | Main CTAs |
| `SecondaryButton` | `flash/components/buttons/secondary_button.dart` | Secondary actions |
| `CloseIconButton` | `flash/components/buttons/close_icon_button.dart` | Close X button |
| `FlashBottomSheet` | `flash/components/bottom_sheet/flash_bottom_sheet.dart` | Sheet container |
| `showModal()` | `flash/components/bottom_sheet/show_modal.dart` | Present a sheet |
| `BottomSheetHeader` | `flash/components/bottom_sheet/bottom_sheet_header.dart` | Sheet header row |
| `BottomSheetHandle` | `flash/components/bottom_sheet/bottom_sheet_handle.dart` | Drag handle |
| `BottomSheetCloseButton` | `flash/components/bottom_sheet/bottom_sheet_close_button.dart` | Close button |
| `Badge` | `flash/components/badge.dart` | Status badges |
| `FlashChip` | `flash/components/flash_chip.dart` | Filter/selection chips |

## Building Incrementally

Build one piece at a time. After each piece, hot reload so the participant sees progress on their phone. This keeps engagement high and catches issues early.

**Recommended build order:**

1. **Scaffold + launcher registration** -- create the directory structure, add a minimal screen with just an AppBar and background color, register it in `main.dart`. Hot reload. The participant sees their screen name in the launcher.

2. **Mock data + provider** -- create the data models and hardcoded sample data. Create the Riverpod provider. No visible change yet, but the data layer is ready.

3. **Layout skeleton** -- build the screen's overall structure (header area, content area, CTA area). Use placeholder text. Hot reload. The participant sees the bones of their screen.

4. **Widgets one by one** -- build each widget from the spec. After each widget, hot reload. The participant sees the screen fill in piece by piece.

5. **Polish** -- spacing, colors, edge cases. Final hot reload.

### Registering in the Launcher

Add the new prototype to `lib/main.dart`:

```dart
// In the imports at the top:
import 'prototypes/<feature>/<feature>_screen.dart';

// In the features list:
FeatureGroup(
  title: '<Feature Name>',
  description: '<One-line description>',
  variants: [
    PrototypeEntry(
      title: '<Feature Name>',
      description: '<What this prototype shows>',
      screen: <FeatureName>Screen(),
    ),
  ],
),
```

## Patterns and Gotchas

### Dark screens need AppBar overrides

The app theme is light. On dark-background screens, AppBar title and icons default to dark blue (invisible).

```dart
appBar: AppBar(
  backgroundColor: darkNight,       // or primary
  foregroundColor: Colors.white,
  titleTextStyle: Theme.of(context).textTheme.titleLarge?.copyWith(
    color: Colors.white,
  ),
  iconTheme: const IconThemeData(color: Colors.white),
  title: const Text('Feature Name'),
),
```

### TextFields use theme decoration by default

Plain `TextField` with `InputDecoration` already looks like production (borderRadius 14, gray3 border, secondary on focus). No custom decoration needed.

```dart
// This already looks like Flash:
TextField(
  decoration: InputDecoration(
    labelText: 'Amount',
    hintText: 'Enter amount',
    suffixText: 'EGP',
  ),
),
```

### Bottom sheets

```dart
showModalBottomSheet(
  context: context,
  backgroundColor: Colors.transparent,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
  ),
  clipBehavior: Clip.antiAlias,
  builder: (_) => YourSheet(...),
);
```

Or use the extracted `showModal()` from `lib/flash/components/bottom_sheet/show_modal.dart`.

### Container.clipBehavior does NOT clip children inside borders

`Container(clipBehavior: Clip.antiAlias)` with border+borderRadius clips to the OUTER edge. Children bleed at corners.

```dart
// Correct: separate border from clipping
Container(
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(12),
    border: Border.all(width: 1),
  ),
  child: ClipRRect(
    borderRadius: BorderRadius.circular(11), // outer - border
    child: Column(...)
  ),
)
```

### Pinned CTAs (buttons at screen bottom)

If the spec says a CTA is pinned to the bottom, use `Column` with `Expanded` scrollable content + bottom widget outside the scroll:

```dart
Column(
  children: [
    Expanded(
      child: SingleChildScrollView(
        child: // ... content
      ),
    ),
    // Pinned CTA -- always visible
    Padding(
      padding: const EdgeInsets.all(20),
      child: PrimaryButton(onPressed: ..., child: Text('Continue')),
    ),
  ],
)
```

### Icons

Use SVGs from Figma saved to `assets/icons/`. Render with `SvgPicture.asset()`. Exception: standard navigation icons (`Icons.arrow_back`, `Icons.close`) are fine from Material.

**SVG cleanup for flutter_svg:** Figma MCP exports SVGs with CSS features that flutter_svg can't render. Clean every SVG:
- Replace `fill="var(--fill-0, #2C2C84)"` with the fallback hex: `fill="#2C2C84"`
- Replace `width="100%" height="100%"` with numeric values from the `viewBox`
- Remove `style="display: block;"` attributes

**Monochrome vs multicolor icons:**
- Monochrome (single fill color): use `ColorFilter.mode(color, BlendMode.srcIn)` to tint
- Multicolor (icon names with "color", "twotone", "flat"): render without ColorFilter -- their original colors are the design

**Register asset directories in `pubspec.yaml`** (Flutter asset dirs are NOT recursive!):
```yaml
flutter:
  assets:
    - assets/icons/    # required -- assets/ alone won't find files in subdirectories
```
Symptom of missing registration: `SvgPicture.asset` renders blank with no error.

### ElevatedButton uses theme

The theme configures ElevatedButton with `primary` background, `secondary` text, 12px radius, 0 elevation. Just use it:

```dart
ElevatedButton(
  onPressed: onTap,
  child: Text('Continue'),
)
```

## State Management

Riverpod (`flutter_riverpod`). Each prototype gets its own provider in `providers/`:

```dart
// Simple state notifier pattern
final savingsProvider = StateNotifierProvider<SavingsNotifier, SavingsState>((ref) {
  return SavingsNotifier();
});

class SavingsState {
  final String goalName;
  final double currentAmount;
  final double targetAmount;
  // ...
}

class SavingsNotifier extends StateNotifier<SavingsState> {
  SavingsNotifier() : super(SavingsState(...));

  void addContribution(double amount) {
    state = state.copyWith(currentAmount: state.currentAmount + amount);
  }
}
```

Riverpod lives in providers/ and the screen file only. Never in widgets/.

## Mock Data Only

All data is hardcoded. No real API calls, no backend dependencies, no network requests. Mock data lives in `models/mock_data.dart`:

```dart
final mockSavingsGoal = SavingsGoal(
  name: 'New MacBook Pro',
  targetAmount: 85000,
  currentAmount: 42500,
  contributions: [
    Contribution(amount: 5000, date: DateTime(2026, 3, 1)),
    // ...
  ],
);
```

Use realistic Egyptian financial data -- amounts in EGP, Egyptian bank names, local merchant names. This makes the prototype feel real.

## Checklist Before Done

- [ ] No hardcoded hex colors -- all from `color.dart` or flagged
- [ ] No raw `TextStyle()` -- all from `Theme.of(context).textTheme.*`
- [ ] All widgets in `widgets/` are dumb (no Riverpod imports)
- [ ] Dark screens have explicit AppBar color overrides
- [ ] Production components used where available
- [ ] Registered in `main.dart` launcher
- [ ] `flutter analyze` passes clean
- [ ] App runs on device via hot reload
