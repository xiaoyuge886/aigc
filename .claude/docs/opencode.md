# OpenCode IDE Support

## Overview

planning-with-files works with OpenCode as a personal or project skill.

## Installation

See [.opencode/INSTALL.md](../.opencode/INSTALL.md) for detailed installation instructions.

### Quick Install (Global)

```bash
mkdir -p ~/.config/opencode/skills
cd ~/.config/opencode/skills
git clone https://github.com/OthmanAdi/planning-with-files.git
```

### Quick Install (Project)

```bash
mkdir -p .opencode/skills
cd .opencode/skills
git clone https://github.com/OthmanAdi/planning-with-files.git
```

## Usage with Superpowers Plugin

If you have [obra/superpowers](https://github.com/obra/superpowers) OpenCode plugin:

```
Use the use_skill tool with skill_name: "planning-with-files"
```

## Usage without Superpowers

Manually read the skill file when starting complex tasks:

```bash
cat ~/.config/opencode/skills/planning-with-files/planning-with-files/SKILL.md
```

## oh-my-opencode Compatibility

If using oh-my-opencode, ensure planning-with-files is not in the `disabled_skills` array:

**~/.config/opencode/oh-my-opencode.json:**
```json
{
  "disabled_skills": []
}
```

## Verification

**Global:**
```bash
ls -la ~/.config/opencode/skills/planning-with-files/planning-with-files/SKILL.md
```

**Project:**
```bash
ls -la .opencode/skills/planning-with-files/planning-with-files/SKILL.md
```

## Learn More

- [Installation Guide](installation.md)
- [Quick Start](quickstart.md)
- [Workflow Diagram](workflow.md)
