# TextLands CLI

Play TextLands from your terminal.

## Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://textlands.com/install.sh | bash
```

### Package Managers

```bash
# pip (Python 3.10+)
pip install textlands

# Homebrew (macOS/Linux)
brew tap MindFortressInc/textlands
brew install textlands

# npm (Node.js 16+)
npm install -g textlands
```

### Download Binary

Pre-built binaries available on [GitHub Releases](https://github.com/MindFortressInc/textlands-cli/releases):

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon) | `textlands-macos-arm64` |
| macOS (Intel) | `textlands-macos-x64` |
| Linux (x64) | `textlands-linux-x64` |
| Windows (x64) | `textlands-windows-x64.exe` |

## Quick Start

```bash
# List available realms
textlands realms

# Start playing
textlands play

# Or jump straight into a realm
textlands play <realm-id>
```

## Commands

| Command | Description |
|---------|-------------|
| `textlands realms` | List available realms |
| `textlands play [REALM]` | Start or resume playing |
| `textlands status` | Show current session |
| `textlands login` | Authenticate with API key |
| `textlands logout` | Clear credentials |
| `textlands config` | Configure settings |

## In-Game Commands

While playing:

- `/look` or `/l` - Look around
- `/inventory` or `/i` - Check inventory
- `/rest` or `/r` - Rest and recover
- `/help` or `/h` - Show help
- `/quit` or `/q` - Exit game

Or just type what you want to do:
- "search the room"
- "talk to the bartender"
- "attack the goblin"

## Configuration

The CLI stores config in `~/.textlands/`:
- `config.json` - Settings and session state
- API keys are stored in system keyring when available

Environment variables:
- `TEXTLANDS_API_URL` - Override API URL
- `TEXTLANDS_API_KEY` - Set API key
- `TEXTLANDS_INSTALL_DIR` - Custom install directory (for install.sh)

## Development

```bash
# Clone and install
git clone https://github.com/MindFortressInc/textlands-cli
cd cli
pip install -e ".[dev]"

# Run tests
pytest

# Local API testing
textlands config --api-url http://localhost:8002

# Build binary locally
pip install pyinstaller
pyinstaller --onefile textlands_cli/main.py
```

## License

MIT
