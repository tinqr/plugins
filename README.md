# tinqr plugins

Claude Code plugins by [tinqr](https://github.com/tinqr).

## Install from this marketplace

```bash
claude marketplace add github.com/tinqr/plugins
```

Then install any plugin:

```bash
claude plugin install tinqr/marrow
claude plugin install tinqr/codemap
claude plugin install tinqr/workshop-setup
```

Or install directly from each plugin's repo (no marketplace needed):

```bash
claude plugin install github.com/tinqr/marrow
claude plugin install github.com/tinqr/codemap
```

## Plugins

### marrow v1.0.0

Persistent memory for AI coding tools. Automatic session context, note processing, and knowledge management through plain markdown files.

- 3 hooks (session orient, note validation, auto-commit)
- 12 skills for daily use (/process, /connect, /audit, /tasks, /next, /revisit, /remember, /process-all, /review, plus 3 internal)
- Conversational setup: run `/marrow:setup` to create your personalized vault

```bash
claude plugin install tinqr/marrow
```

### codemap v1.4.0

Auto-generated codebase context for AI agents. Tree-sitter parsing, PageRank ranking, incremental updates, zero-config setup.

- Skills: `/codemap:query`, `/codemap:setup`, `/codemap:init`, `/codemap:refresh`
- Deployed on 4+ projects, 50 tests

```bash
claude plugin install tinqr/codemap
```

### workshop-setup v1.0.0

Guided Flutter development environment setup for non-technical workshop participants. Installs Xcode/Android Studio, Homebrew, Flutter, clones the project, builds on a physical device.

- Designed for Apple Silicon Macs
- Handles iPhone and Android paths
- Plain language for designers and PMs

```bash
claude plugin install tinqr/workshop-setup
```
