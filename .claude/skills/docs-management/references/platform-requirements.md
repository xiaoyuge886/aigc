# Platform-Specific Requirements

## Windows Users

**MUST use PowerShell (recommended) or prefix Git Bash commands with `MSYS_NO_PATHCONV=1`**

Git Bash on Windows converts Unix paths (e.g., `/en/docs/`) to Windows paths (e.g., `C:/Program Files/Git/en/docs/`), which breaks filter patterns.

**Solutions:**

1. **Use PowerShell** (recommended):

   ```powershell
   pwsh -Command "python scripts/core/scrape_docs.py --filter '/en/docs/'"
   ```

2. **Use MSYS_NO_PATHCONV=1** with Git Bash:

   ```bash
   MSYS_NO_PATHCONV=1 python scripts/core/scrape_docs.py --filter "/en/docs/"
   ```

See [Troubleshooting Guide](troubleshooting.md#git-bash-path-conversion) for complete details.

## Path Doubling Prevention

**ABSOLUTE PROHIBITION: NEVER use `cd` with `&&` in PowerShell when running scripts from this skill.**

**The Problem:** If your current working directory is already inside the skill directory (or any subdirectory), using relative paths causes PowerShell to resolve paths relative to the current directory instead of the repository root, resulting in path doubling where path segments appear twice (e.g., `skill-dir/skill-dir/scripts/script.py`).

**REQUIRED Solutions (choose one):**

1. **✅ ALWAYS use helper scripts** (recommended - they handle path resolution automatically):
   - Helper scripts use `Path(__file__).resolve()` to get absolute script location
   - They can be called from any directory and will resolve paths correctly
   - Example pattern: Use scripts that internally resolve their own location

2. **✅ Use absolute path resolution** (if not using helper script):
   - Get absolute path first using `Get-Item` or `Resolve-Path` in PowerShell
   - Store in variable, then execute with absolute path
   - Example pattern: `$scriptPath = (Get-Item "<relative-path>").FullName; python $scriptPath`

3. **✅ Use separate commands** (never `cd` with `&&`):
   - Change directory first, then run command separately
   - Or ensure you're at repository root before using relative paths
   - Example pattern: `Set-Location <repo-root>` then `python <relative-path-to-script>`

**NEVER DO THIS:**

- ❌ **Never chain `cd` with `&&`**: `cd <relative-path> && python <script>` causes path doubling if already in a subdirectory
- ❌ **Never assume current directory**: Relative paths resolve relative to current working directory, not repository root
- ❌ **Never use relative paths when current dir is inside skill directory**: This causes path doubling

**Detection:** If you see errors containing doubled path segments (e.g., `skill-dir/skill-dir/scripts/script.py` or "Cannot find path" errors showing the same path segment twice), you have path doubling. Stop immediately and use one of the REQUIRED solutions above.

**For all scripts in this skill:** Always run from repository root using relative paths, OR use helper scripts that handle path resolution automatically. Never assume the current working directory. When in doubt, use absolute path resolution or helper scripts.
