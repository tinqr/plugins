# flash-prototype

Flash prototype building toolkit for Claude Code. Three skills that cover the full design-to-prototype pipeline.

## Skills

### `/flash-prototype:extract`
Extract a **production-ready Figma design** and match every value to Flash production tokens with pixel accuracy. Full figma-to-code protocol: subagent extraction, precise color/typography matching, icon SVG pipeline, layout model analysis. Produces a `design_spec.md` for the build skill.

### `/flash-prototype:adapt`
Adapt a **rough wireframe** to Flash's visual language. Creatively maps placeholder wireframe colors to Flash production tokens (dark backgrounds become Flash navy, white stays white, accents become lime green). For workshop prototyping from wireframes.

### `/flash-prototype:build`
Build a Flutter prototype using Flash production tokens and components. Works alongside Superpowers for workflow orchestration. Provides domain-specific knowledge: project structure, color tokens, text styles, 11 production components, dumb widget boundary for clean production extraction.

## Pipeline

```
Figma design ──→ /extract ──→ design_spec.md ──→ /build ──→ Flutter prototype
Wireframe    ──→ /adapt   ──→ design_spec.md ──→ /build ──→ Flutter prototype
```

Both extraction skills produce the same `design_spec.md` format. The build skill consumes it alongside Superpowers (planning, subagent-driven development).

## Install

```bash
claude plugin install tinqr/flash-prototype
```

## Requirements

- Flash prototypes repo at `~/flutter-projects/flash-prototypes/`
- Figma MCP configured (for extract and adapt)
- Superpowers plugin (for build workflow)
