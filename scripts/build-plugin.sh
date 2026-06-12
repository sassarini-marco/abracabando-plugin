#!/usr/bin/env bash
set -euo pipefail

# Build plugin package for distribution
# Usage: ./scripts/build-plugin.sh [version]
# If version is not provided, reads from abracabando/.claude-plugin/plugin.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/abracabando"

# Extract version from plugin.json or use argument
if [ $# -eq 1 ]; then
    VERSION="$1"
else
    VERSION=$(grep -o '"version":\s*"[^"]*"' "$PLUGIN_DIR/.claude-plugin/plugin.json" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
fi

if [ -z "$VERSION" ]; then
    echo "Error: Could not determine version"
    exit 1
fi

echo "Building abracabando plugin version $VERSION"

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
PACKAGE_NAME="abracabando-$VERSION"
PACKAGE_DIR="$BUILD_DIR/$PACKAGE_NAME"

trap 'rm -rf "$BUILD_DIR"' EXIT

mkdir -p "$PACKAGE_DIR"

# Copy plugin files (exclude tests, bench, and dev files)
cp -r "$PLUGIN_DIR/.claude-plugin" "$PACKAGE_DIR/"
cp -r "$PLUGIN_DIR/skills" "$PACKAGE_DIR/"
cp -r "$PLUGIN_DIR/examples" "$PACKAGE_DIR/"
cp "$PLUGIN_DIR/.mcp.json" "$PACKAGE_DIR/"
cp "$PLUGIN_DIR/README.md" "$PACKAGE_DIR/"
cp "$PLUGIN_DIR/CHANGELOG.md" "$PACKAGE_DIR/"
cp "$REPO_ROOT/LICENSE" "$PACKAGE_DIR/"

# Create dist directory and zip
mkdir -p "$REPO_ROOT/dist"
cd "$BUILD_DIR"
zip -r "$REPO_ROOT/dist/$PACKAGE_NAME.zip" "$PACKAGE_NAME"

echo ""
echo "✓ Package created: dist/$PACKAGE_NAME.zip"
ls -lh "$REPO_ROOT/dist/$PACKAGE_NAME.zip"
echo ""
echo "Contents:"
unzip -l "$REPO_ROOT/dist/$PACKAGE_NAME.zip" | head -30