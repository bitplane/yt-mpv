#!/usr/bin/env bash
# Install script for yt-ulp

set -e  # exit on error

# Define paths
DESKTOP_FILE="yt-ulp.desktop"
LAUNCHER_FILE="yt-ulp-launcher"
INSTALL_DIR="$HOME/.local/share/yt-ulp"    # installation directory
APP_DIR="$HOME/.local/share/applications"  # applications directory for .desktop
BIN_DIR="$HOME/.local/bin"                 # user-local bin for the launcher
VENV_DIR="$INSTALL_DIR/venv"               # virtual environment directory

echo "Installing YouTube ULP handler..."

# Create necessary directories
mkdir -p "$APP_DIR" "$BIN_DIR" "$INSTALL_DIR"

# Install the .desktop file (copy to applications dir)
# If Exec path in desktop file is relative, we might need to update it to the
# full path of the launcher.
DESKTARGET="$APP_DIR/$DESKTOP_FILE"
cp "$DESKTOP_FILE" "$DESKTARGET"
echo "Copied desktop entry to $DESKTARGET"

# Make sure the desktop file is updated with correct Exec path
# (Replace "Exec=yt-ulp-launcher" with the full path to the launcher in BIN_DIR)
sed -i "s#Exec=yt-ulp-launcher#Exec=$BIN_DIR/yt-ulp-launcher#g" "$DESKTARGET"

# Update desktop database to register the new URL scheme handlers
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$APP_DIR" || true
fi
# Also use xdg-mime to be safe (sets our handler as default for the scheme)
if command -v xdg-mime &> /dev/null; then
    xdg-mime default "$DESKTOP_FILE" x-scheme-handler/x-yt-ulp
    xdg-mime default "$DESKTOP_FILE" x-scheme-handler/x-yt-ulps
fi

echo "Registered x-yt-ulp and x-yt-ulps URL schemes."

# Install the launcher script to user bin and make executable
cp "$LAUNCHER_FILE" "$BIN_DIR/yt-ulp-launcher"
chmod +x "$BIN_DIR/yt-ulp-launcher"
echo "Installed launcher script to $BIN_DIR/yt-ulp-launcher"

# Set up Python virtual environment using uv (a fast Python package manager)
# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "uv (Python package manager) not found, installing it..."
    python3 -m pip install --user uv  # ensure uv is available to create venv
fi

# Create virtual environment and install packages
if [ ! -d "$VENV_DIR" ]; then
    uv virtualenv "$VENV_DIR"
fi

# Activate the virtual environment
# (shellcheck disable=SC1091)
source "$VENV_DIR/bin/activate"

# Install/upgrade required Python packages in the venv
echo "Installing/upgrading Python dependencies (yt-dlp, internetarchive)..."
uv install -U yt-dlp internetarchive  # -U to upgrade

# Deactivate venv to avoid contaminating rest of script
deactivate

# Prompt for Archive.org credentials if in a terminal and not configured
if [ -t 1 ]; then
    # Check if user already configured internetarchive
    IA_CONFIG="$HOME/.config/ia.ini"
    IA_CONFIG_ALT="$HOME/.config/internetarchive/ia.ini"
    if [[ -f "$IA_CONFIG" || -f "$IA_CONFIG_ALT" ]]; then
        echo "Archive.org credentials already configured."
    else
        echo "No Archive.org credentials. Launching 'ia configure' for setup"
        # Run the `ia configure` command (it will prompt for email and password)
        "$VENV_DIR/bin/ia" configure
        echo "Archive.org credentials configured."
    fi
else
    echo "Install script not running in an interactive shell."
    echo "Please ensure your Archive.org credentials are configured for uploads"
    echo "For example, run: ~/.local/bin/ia configure"
fi

echo "Installation complete."
echo "You can now add the bookmarklet to your browser and use x-yt-ulp:// links"
