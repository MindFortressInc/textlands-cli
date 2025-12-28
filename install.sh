#!/bin/bash
#
# TextLands CLI Installer
# Usage: curl -fsSL https://textlands.com/install.sh | bash
#
# This script detects your platform and installs the appropriate binary.
#

set -e

VERSION="${TEXTLANDS_VERSION:-latest}"
REPO="textlands/cli"
INSTALL_DIR="${TEXTLANDS_INSTALL_DIR:-$HOME/.local/bin}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}==>${NC} $1"
}

success() {
    echo -e "${GREEN}==>${NC} $1"
}

warn() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

error() {
    echo -e "${RED}Error:${NC} $1"
    exit 1
}

# Detect platform
detect_platform() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)

    case "$os" in
        linux*)
            OS="linux"
            ;;
        darwin*)
            OS="macos"
            ;;
        mingw*|msys*|cygwin*)
            OS="windows"
            ;;
        *)
            error "Unsupported operating system: $os"
            ;;
    esac

    case "$arch" in
        x86_64|amd64)
            ARCH="x64"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            ;;
        *)
            error "Unsupported architecture: $arch"
            ;;
    esac

    BINARY_NAME="textlands-${OS}-${ARCH}"
    if [ "$OS" = "windows" ]; then
        BINARY_NAME="${BINARY_NAME}.exe"
    fi
}

# Get latest version from GitHub
get_latest_version() {
    if [ "$VERSION" = "latest" ]; then
        VERSION=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')
        if [ -z "$VERSION" ]; then
            error "Failed to get latest version"
        fi
    fi
}

# Download binary
download() {
    local url="https://github.com/${REPO}/releases/download/v${VERSION}/${BINARY_NAME}"
    local dest="${INSTALL_DIR}/textlands"

    info "Downloading TextLands CLI v${VERSION}..."
    info "Platform: ${OS}-${ARCH}"

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Download
    if command -v curl &> /dev/null; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget &> /dev/null; then
        wget -q "$url" -O "$dest"
    else
        error "Neither curl nor wget found. Please install one of them."
    fi

    # Make executable
    chmod +x "$dest"

    success "Installed to $dest"
}

# Add to PATH if needed
setup_path() {
    local shell_rc=""
    local path_line="export PATH=\"\$PATH:$INSTALL_DIR\""

    # Check if already in PATH
    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        return
    fi

    # Detect shell
    case "$SHELL" in
        */zsh)
            shell_rc="$HOME/.zshrc"
            ;;
        */bash)
            if [ -f "$HOME/.bashrc" ]; then
                shell_rc="$HOME/.bashrc"
            else
                shell_rc="$HOME/.bash_profile"
            fi
            ;;
        */fish)
            shell_rc="$HOME/.config/fish/config.fish"
            path_line="set -gx PATH \$PATH $INSTALL_DIR"
            ;;
    esac

    if [ -n "$shell_rc" ]; then
        if ! grep -q "$INSTALL_DIR" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# TextLands CLI" >> "$shell_rc"
            echo "$path_line" >> "$shell_rc"
            warn "Added $INSTALL_DIR to PATH in $shell_rc"
            warn "Run 'source $shell_rc' or restart your terminal"
        fi
    else
        warn "Add $INSTALL_DIR to your PATH manually"
    fi
}

# Verify installation
verify() {
    if [ -x "${INSTALL_DIR}/textlands" ]; then
        success "TextLands CLI installed successfully!"
        echo ""
        echo "Run 'textlands --help' to get started."
        echo "Run 'textlands realms' to see available realms."
        echo "Run 'textlands play' to start playing!"
    else
        error "Installation failed"
    fi
}

# Main
main() {
    echo ""
    echo "  ╔════════════════════════════════════╗"
    echo "  ║      TextLands CLI Installer       ║"
    echo "  ╚════════════════════════════════════╝"
    echo ""

    detect_platform
    get_latest_version
    download
    setup_path
    verify

    echo ""
}

main "$@"
