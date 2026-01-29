#!/bin/bash
set -e

THEME_NAME="premium-v3"
INSTALL_DIR="/boot/grub/themes/$THEME_NAME"
SOURCE_DIR="$(pwd)/grub-theme"
GRUB_CONFIG="/etc/default/grub"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Check Root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root"
    exit 1
fi

# 2. Validation
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "Theme directory '$SOURCE_DIR' not found."
    exit 1
fi

if [ ! -f "$SOURCE_DIR/theme.txt" ]; then
    log_error "theme.txt not found in '$SOURCE_DIR'."
    exit 1
fi

# 2.1 Verify Theme content
if command -v python3 &> /dev/null && [ -f "verify_theme.py" ]; then
    log_info "Verifying theme integrity..."
    if ! python3 verify_theme.py; then
        log_error "Theme verification failed."
        exit 1
    fi
else
    log_warn "Skipping deep theme verification (python3 or verify_theme.py not found)."
fi

# 3. Check dependencies
if ! command -v grub-mkfont &> /dev/null; then
    log_warn "grub-mkfont not found. Font generation might fail or needs to be skipped."
    # We will try to continue, but if fonts are missing, theme might look bad.
    # If the user doesn't have grub-mkfont, they might be on a system where it's named grub2-mkfont
    if command -v grub2-mkfont &> /dev/null; then
        MKFONT="grub2-mkfont"
    else
        log_error "Neither grub-mkfont nor grub2-mkfont found. Cannot generate fonts."
        exit 1
    fi
else
    MKFONT="grub-mkfont"
fi

# 4. Generate Fonts
log_info "Generating fonts using $MKFONT..."

generate_font() {
    local ttf="$1"
    local size="$2"
    local name="$3" # Explicit name base
    # Output to theme root so grub-mkconfig finds them easily
    local output="$SOURCE_DIR/${name} Regular ${size}.pf2"

    # Check if ttf exists
    if [ ! -f "$ttf" ]; then
        log_warn "Font source $ttf not found."
        return
    fi

    log_info "Generating $name size $size..."
    $MKFONT -s "$size" --no-bitmap -o "$output" "$ttf"
}

# Sizes used in theme.txt
# We use explicit names. theme.txt asks for "Inter Regular 24" -> "Inter" is usually the family name.
generate_font "$SOURCE_DIR/fonts/Inter.ttf" 24 "Inter"
generate_font "$SOURCE_DIR/fonts/Inter.ttf" 20 "Inter"
generate_font "$SOURCE_DIR/fonts/Inter.ttf" 16 "Inter"

# JetBrains Mono
# theme.txt asks for "JetBrains Mono Regular 14".
# The TTF likely has "JetBrains Mono" as family.
generate_font "$SOURCE_DIR/fonts/JetBrainsMono.ttf" 20 "JetBrains Mono"
generate_font "$SOURCE_DIR/fonts/JetBrainsMono.ttf" 14 "JetBrains Mono"
generate_font "$SOURCE_DIR/fonts/JetBrainsMono.ttf" 12 "JetBrains Mono"

# 5. Backup Valid Theme
# We look for the current theme in GRUB_CONFIG
CURRENT_THEME=$(grep "^GRUB_THEME=" "$GRUB_CONFIG" | cut -d'"' -f2 | cut -d"'" -f2)

if [ -n "$CURRENT_THEME" ] && [ -f "$CURRENT_THEME" ]; then
    BACKUP_DIR="/boot/grub/themes/backup_$(date +%s)"
    THEME_FOLDER=$(dirname "$CURRENT_THEME")
    log_info "Backing up current theme ($THEME_FOLDER) to $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$THEME_FOLDER/"* "$BACKUP_DIR/"
else
    log_info "No custom theme configured or file not found. Backing up /boot/grub/themes just in case if it exists."
    if [ -d "/boot/grub/themes" ]; then
         cp -r /boot/grub/themes /boot/grub/themes_backup_$(date +%s)
    fi
fi

# 6. Install Theme
log_info "Installing theme to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR/"* "$INSTALL_DIR/"

# 7. Update Config
log_info "Updating $GRUB_CONFIG..."

# Comment out existing GRUB_THEME line
sed -i 's/^GRUB_THEME=/#GRUB_THEME=/' "$GRUB_CONFIG"

# Add new GRUB_THEME line
echo "GRUB_THEME=\"$INSTALL_DIR/theme.txt\"" >> "$GRUB_CONFIG"

# Also ensure GRUB_GFXMODE is set to handle the resolution if needed, but we won't force it blindly.
# But often themes need 1080p.
if ! grep -q "^GRUB_GFXMODE=" "$GRUB_CONFIG"; then
    echo 'GRUB_GFXMODE="1920x1080,auto"' >> "$GRUB_CONFIG"
fi

# 8. Update GRUB
log_info "Updating GRUB..."
if command -v update-grub &> /dev/null; then
    update-grub
elif command -v grub-mkconfig &> /dev/null; then
    grub-mkconfig -o /boot/grub/grub.cfg
elif command -v grub2-mkconfig &> /dev/null; then
    grub2-mkconfig -o /boot/grub2/grub.cfg
else
    log_warn "Could not find update-grub or grub-mkconfig. Please update grub manually."
fi

log_info "Theme installed successfully!"
