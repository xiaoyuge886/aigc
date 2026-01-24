# Kilo Code Support

Planning with Files is fully supported on Kilo Code through native integration.

## Quick Start

1. Open your project in Kilo Code
2. Rules load automatically from global (`~/.kilocode/rules/`) or project (`.kilocode/rules/`) directories
3. Start a complex task — Kilo Code will automatically create planning files

## Installation

### Quick Install (Project-Level)

Clone or copy the skill to your project's `.kilocode/skills/` directory:

**Unix/Linux/macOS:**
```bash
# Option A: Clone the repository
git clone https://github.com/OthmanAdi/planning-with-files.git

# Copy the skill to Kilo Code's skills directory
mkdir -p .kilocode/skills
cp -r planning-with-files/skills/planning-with-files .kilocode/skills/planning-with-files

# Copy the rules file (optional, but recommended)
mkdir -p .kilocode/rules
cp planning-with-files/.kilocode/rules/planning-with-files.md .kilocode/rules/planning-with-files.md
```

**Windows (PowerShell):**
```powershell
# Option A: Clone the repository
git clone https://github.com/OthmanAdi/planning-with-files.git

# Copy the skill to Kilo Code's skills directory
New-Item -ItemType Directory -Force -Path .kilocode\skills
Copy-Item -Recurse -Force planning-with-files\skills\planning-with-files .kilocode\skills\planning-with-files

# Copy the rules file (optional, but recommended)
New-Item -ItemType Directory -Force -Path .kilocode\rules
Copy-Item -Force planning-with-files\.kilocode\rules\planning-with-files.md .kilocode\rules\planning-with-files.md

# Copy PowerShell scripts (optional, but recommended)
Copy-Item -Force planning-with-files\scripts\init-session.ps1 .kilocode\skills\planning-with-files\scripts\init-session.ps1
Copy-Item -Force planning-with-files\scripts\check-complete.ps1 .kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

### Manual Installation (Project-Level)

Copy the skill directory to your project:

**Unix/Linux/macOS:**
```bash
# From the cloned repository
mkdir -p .kilocode/skills
cp -r planning-with-files/skills/planning-with-files .kilocode/skills/planning-with-files

# Copy the rules file (optional, but recommended)
mkdir -p .kilocode/rules
cp planning-with-files/.kilocode/rules/planning-with-files.md .kilocode/rules/planning-with-files.md
```

**Windows (PowerShell):**
```powershell
# From the cloned repository
New-Item -ItemType Directory -Force -Path .kilocode\skills
Copy-Item -Recurse -Force planning-with-files\skills\planning-with-files .kilocode\skills\planning-with-files

# Copy the rules file (optional, but recommended)
New-Item -ItemType Directory -Force -Path .kilocode\rules
Copy-Item -Force planning-with-files\.kilocode\rules\planning-with-files.md .kilocode\rules\planning-with-files.md

# Copy PowerShell scripts (optional, but recommended)
Copy-Item -Force planning-with-files\scripts\init-session.ps1 .kilocode\skills\planning-with-files\scripts\init-session.ps1
Copy-Item -Force planning-with-files\scripts\check-complete.ps1 .kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

### Global Installation (User-Level)

To make the skill available across all projects:

**Unix/Linux/macOS:**
```bash
# Copy to global skills directory
mkdir -p ~/.kilocode/skills
cp -r planning-with-files/skills/planning-with-files ~/.kilocode/skills/planning-with-files

# Copy the rules file (optional, but recommended)
mkdir -p ~/.kilocode/rules
cp planning-with-files/.kilocode/rules/planning-with-files.md ~/.kilocode/rules/planning-with-files.md
```

**Windows (PowerShell):**
```powershell
# Copy to global skills directory (replace YourUsername with your actual username)
New-Item -ItemType Directory -Force -Path C:\Users\YourUsername\.kilocode\skills
Copy-Item -Recurse -Force planning-with-files\skills\planning-with-files C:\Users\YourUsername\.kilocode\skills\planning-with-files

# Copy the rules file (optional, but recommended)
New-Item -ItemType Directory -Force -Path C:\Users\YourUsername\.kilocode\rules
Copy-Item -Force planning-with-files\.kilocode\rules\planning-with-files.md C:\Users\YourUsername\.kilocode\rules\planning-with-files.md

# Copy PowerShell scripts (optional, but recommended)
Copy-Item -Force planning-with-files\scripts\init-session.ps1 C:\Users\YourUsername\.kilocode\skills\planning-with-files\scripts\init-session.ps1
Copy-Item -Force planning-with-files\scripts\check-complete.ps1 C:\Users\YourUsername\.kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

### Verifying Installation

After installation, verify the skill is loaded:

1. **Restart Kilo Code** (if needed)
2. Ask the agent: "Do you have access to the planning-with-files skill?"
3. The agent should confirm the skill is loaded
4. Rules also load automatically from `~/.kilocode/rules/planning-with-files.md` (global) or `.kilocode/rules/planning-with-files.md` (project)

**Testing PowerShell Scripts (Windows):**

After installation, you can test the PowerShell scripts:

```powershell
# Test init-session.ps1
.\.kilocode\skills\planning-with-files\scripts\init-session.ps1

# Test check-complete.ps1
.\.kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

The scripts should create `task_plan.md`, `findings.md`, and `progress.md` files in your project root.

### File Structure

The installation consists of the skill directory and the rules file:

**Skill Directory:**

```
~/.kilocode/skills/planning-with-files/          (Global)
OR
.kilocode/skills/planning-with-files/             (Project)
├── SKILL.md              # Skill definition
├── examples.md           # Real-world examples
├── reference.md          # Advanced reference
├── templates/            # Planning file templates
│   ├── task_plan.md
│   ├── findings.md
│   └── progress.md
└── scripts/              # Utility scripts
    ├── init-session.sh    # Unix/Linux/macOS
    ├── check-complete.sh  # Unix/Linux/macOS
    ├── init-session.ps1  # Windows (PowerShell)
    └── check-complete.ps1 # Windows (PowerShell)
```

**Rules File:**

```
~/.kilocode/rules/planning-with-files.md        (Global)
OR
.kilocode/rules/planning-with-files.md           (Project)
```

**Important**: The `name` field in `SKILL.md` must match the directory name (`planning-with-files`).

## File Locations

| Type | Global Location | Project Location |
|------|-----------------|------------------|
| **Rules** | `~/.kilocode/rules/planning-with-files.md` | `.kilocode/rules/planning-with-files.md` |
| **Skill** | `~/.kilocode/skills/planning-with-files/SKILL.md` | `.kilocode/skills/planning-with-files/SKILL.md` |
| **Templates** | `~/.kilocode/skills/planning-with-files/templates/` | `.kilocode/skills/planning-with-files/templates/` |
| **Scripts (Unix/Linux/macOS)** | `~/.kilocode/skills/planning-with-files/scripts/*.sh` | `.kilocode/skills/planning-with-files/scripts/*.sh` |
| **Scripts (Windows PowerShell)** | `~/.kilocode/skills/planning-with-files/scripts/*.ps1` | `.kilocode/skills/planning-with-files/scripts/*.ps1` |
| **Your Files** | `task_plan.md`, `findings.md`, `progress.md` in project root |

## Quick Commands

**For Global Installation:**

**Unix/Linux/macOS:**
```bash
# Initialize planning files
~/.kilocode/skills/planning-with-files/scripts/init-session.sh

# Verify task completion
~/.kilocode/skills/planning-with-files/scripts/check-complete.sh
```

**Windows (PowerShell):**
```powershell
# Initialize planning files
$env:USERPROFILE\.kilocode\skills\planning-with-files\scripts\init-session.ps1

# Verify task completion
$env:USERPROFILE\.kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

**For Project Installation:**

**Unix/Linux/macOS:**
```bash
# Initialize planning files
./.kilocode/skills/planning-with-files/scripts/init-session.sh

# Verify task completion
./.kilocode/skills/planning-with-files/scripts/check-complete.sh
```

**Windows (PowerShell):**
```powershell
# Initialize planning files
.\.kilocode\skills\planning-with-files\scripts\init-session.ps1

# Verify task completion
.\.kilocode\skills\planning-with-files\scripts\check-complete.ps1
```

## Migrating from Cursor/Windsurf

Planning files are fully compatible. Simply copy your `task_plan.md`, `findings.md`, and `progress.md` files to your new project.

## Additional Resources

**For Global Installation:**
- [Examples](~/.kilocode/skills/planning-with-files/examples.md) - Real-world examples
- [Reference](~/.kilocode/skills/planning-with-files/reference.md) - Advanced reference documentation
- [PowerShell Scripts](~/.kilocode/skills/planning-with-files/scripts/) - Utility scripts for Windows

**For Project Installation:**
- [Examples](.kilocode/skills/planning-with-files/examples.md) - Real-world examples
- [Reference](.kilocode/skills/planning-with-files/reference.md) - Advanced reference documentation
- [PowerShell Scripts](.kilocode/skills/planning-with-files/scripts/) - Utility scripts for Windows
