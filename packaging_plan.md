# Packaging Plan: Desktop App Distribution

## Overview
Add `--package-mac` and `--package-win` flags to any-agent CLI that bundle agents into standalone desktop applications for end-users (non-developers).

## Target Users
- End-users who want to download and run agents without development setup
- Only need to provide API keys, no Python/Docker knowledge required

## Architecture

### Technology Stack
- **UI Framework:** Tauri (wraps existing React UI)
- **Python Bundling:** python-build-standalone
- **Dependency Management:** uv (matches project tooling)
- **Output Format:**
  - macOS: `.dmg` installer
  - Windows: MSI + NSIS installers (Tauri default)

### Application Structure
```
PackagedAgent.app/
├── Contents/
│   ├── MacOS/
│   │   └── tauri-app (Tauri launcher)
│   ├── Resources/
│   │   ├── react-ui/ (production build)
│   │   └── python-runtime/
│   │       ├── python (standalone runtime)
│   │       ├── agent/ (agent code)
│   │       ├── any_agent/ (framework)
│   │       └── run_agent.py (custom entrypoint)
│   └── Info.plist
```

### Runtime Flow
1. User launches app → Tauri window opens with loading spinner
2. Tauri spawns Python sidecar subprocess (`run_agent.py`)
3. Python finds available port, prints to stdout: `{"port": 8080, "status": "ready"}`
4. Tauri captures stdout via IPC, emits event to React
5. Also sets environment variable as fallback
6. React connects to `localhost:<port>`
7. On app close, Tauri terminates Python subprocess

## CLI Commands

### Basic Usage
```bash
any-agent ./my_agent --package-mac
any-agent ./my_agent --package-win
```

### Testing Without Full Build
```bash
any-agent ./my_agent --package-mac --test
# Runs Tauri app locally without creating .dmg
```

### Flags
- `--package-mac`: Build macOS .dmg installer
- `--package-win`: Build Windows installers
- `--test`: Run packaged app without creating installer (for testing)

## Developer Experience

### Prerequisites Check
Before packaging, check and inform if missing:
- Node.js / npm
- Rust toolchain
- Tauri CLI
- Xcode Command Line Tools (macOS only)

### Interactive Setup Prompts
Collect metadata during packaging:
1. App name (e.g., "My Trading Bot")
2. Version (e.g., "1.0.0")
3. Icon file path (use generic default if not provided)
4. Author name
5. Description

### Build Artifacts
All packaging artifacts stored in `.any_agent/`:

```
.any_agent/
├── package-manifest.json (metadata for rebuilds)
├── tauri-app/ (full Tauri project - can be modified)
│   ├── src/ (React UI)
│   ├── src-tauri/ (Rust code, config, sidecars)
│   ├── package.json
│   └── tauri.conf.json
└── dist/
    └── MyAgent_1.0.0_x64.dmg (final output)
```

### Rebuild Behavior
If `.any_agent/` already exists:
- **Prompt:** Ask to rebuild from scratch or use existing manifest
- **Full rebuild:** Always recreate entire bundle (no incremental builds)
- Clean, predictable behavior

### Code Signing (macOS)
- **Optional:** Prompt during packaging
- Requires Apple Developer account ($99/year)
- Skip with warning if declined (app will show security warning on first launch)

## End-User Experience

### Installation
1. Download `.dmg` (macOS) or installer (Windows)
2. macOS: Drag to Applications folder
3. Windows: Run installer

### First Launch
1. App opens with loading spinner ("Starting agent...")
2. Python backend starts in background
3. If no config file exists:
   - Create template in `~/Library/Application Support/MyAgent/config.json` (macOS)
   - Or `%APPDATA%/MyAgent/config.json` (Windows)
   - App functionality disabled until API keys added

### Configuration File
**Location:**
- macOS: `~/Library/Application Support/<AppName>/config.json`
- Windows: `%APPDATA%/<AppName>/config.json`

**Format:** Simple, flat JSON
```json
{
  "GOOGLE_API_KEY": "your-key-here",
  "ANTHROPIC_API_KEY": "your-key-here",
  "OPENAI_API_KEY": "your-key-here",
  "AWS_REGION": "us-west-2",
  "GOOGLE_MODEL": "gemini-pro"
}
```

**Default Template:** Generic set of common keys
- Framework-agnostic (any framework can use any model endpoint)
- End-users ignore unused keys
- Keys commented as placeholders in template

### App Behavior
- **Window:** Resizable with min/max bounds, no fullscreen
- **Close behavior:** Quit completely (terminate Python backend)
- **Port:** Dynamic (finds available port, no conflicts)
- **Startup:** Shows loading spinner while backend initializes
- **Errors:** Display Python errors directly in UI for troubleshooting

### Logging & Debugging
**Log File:**
- macOS: `~/Library/Logs/<AppName>/app.log`
- Windows: `%LOCALAPPDATA%/<AppName>/logs/app.log`

**Debug Console:**
- Hidden by default
- Enable via keyboard shortcut for advanced troubleshooting

## Technical Implementation Details

### Python Runtime
- **Source:** python-build-standalone (pre-built distributions)
- **Version:** Match system Python version (`python3 --version` on build machine)
- **Bundle scope:** Minimal runtime + agent dependencies + any-agent framework
- **Strip:** Remove dev dependencies, tests for smaller bundle

### Custom Entrypoint Script
Generate `run_agent.py` that:
- Has hardcoded paths to bundled Python, agent code, config
- Imports pre-detected adapter (no runtime detection)
- Finds available port dynamically
- Prints port to stdout for Tauri IPC
- Sets environment variable as fallback
- Handles graceful shutdown (simple, no health monitoring)

**Example:**
```python
# Generated run_agent.py
import sys
import socket
from pathlib import Path

# Set up bundled paths
bundle_root = Path(__file__).parent
sys.path.insert(0, str(bundle_root / "agent"))
sys.path.insert(0, str(bundle_root / "any_agent"))

# Find available port
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

port = find_free_port()

# Communicate port to Tauri
print(f'{{"port": {port}, "status": "ready"}}', flush=True)

# Also set as env var fallback
import os
os.environ['AGENT_PORT'] = str(port)

# Import pre-detected adapter
from any_agent.adapters.adk_adapter import ADKAdapter

# Load config, start server
config_path = Path.home() / "Library/Application Support/MyAgent/config.json"
adapter = ADKAdapter(agent_path=bundle_root / "agent", config_path=config_path)
adapter.run(port=port)
```

### React UI Modifications
- **Loading state:** Add spinner/message while waiting for backend port
- **Production build:** Always build with `vite build --mode production`
- **Port handling:** Listen for Tauri IPC event with backend port, connect dynamically
- **Config instructions:** Show message if backend fails (point to config file location)

### Dependency Management
- Use `uv sync` to create bundled virtual environment
- Match developer's tested Python version
- Include only runtime dependencies (strip dev/test deps)
- Bundle any-agent framework code
- Bundle agent-specific dependencies

### Version Locking
- Packaged app uses exact version of any-agent that created it
- No auto-upgrades or version changes
- Developer must rebuild with new any-agent version for updates
- Predictable, stable behavior

### Error Handling
- **Prerequisites missing:** Show helpful install instructions, exit
- **Build failure:** Clean up `.any_agent/` directory automatically
- **Backend startup failure:** Display error in UI with logs
- **Port conflicts:** Dynamic port prevents this
- **Missing API keys:** Disable app functionality, show config file location

## Future Enhancements (Not in Initial Scope)

### Deferred Features
- **Auto-updates:** Tauri built-in update mechanism (requires hosting infrastructure)
- **CI/CD support:** Non-interactive mode via env vars or CLI flags
- **First-run wizard:** GUI dialog for API key collection (start with config file)
- **Settings UI:** In-app configuration editor (start with manual file editing)
- **Multi-profile configs:** Support dev/prod environments (keep flat/simple)
- **Health monitoring:** Process monitoring and auto-restart (keep simple)

## Open Questions / Future Decisions
- Should we validate icon file format/size during packaging?
- What's the minimum Python version to support in standalone runtime?
- Should we include framework logos as default icons per-framework?
- How to handle agent updates after distribution (versioning strategy)?
- Should we support bundling custom system dependencies (beyond Python)?

## Success Criteria
- Developer runs one command, answers 5 prompts, gets distributable installer
- End-user downloads, installs, adds API keys, agent works
- No Python/Docker/development environment required for end-users
- Works on macOS initially, Windows support follows same pattern
