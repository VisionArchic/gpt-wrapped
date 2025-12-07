#!/bin/bash

# Configuration
APP_NAME="NovaLaunchpad"
BUNDLE_ID="com.visionarchic.NovaLaunchpad"
BUILD_DIR="Build"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
CONTENTS="$APP_BUNDLE/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"
DMG_NAME="${APP_NAME}_Installer.dmg"

# Ensure we are in the script directory
cd "$(dirname "$0")"

# Cleanup
echo "Cleaning up..."
rm -rf "$BUILD_DIR"
rm -f "$DMG_NAME"

# Create App Bundle Structure
echo "Creating app bundle structure..."
mkdir -p "$MACOS"
mkdir -p "$RESOURCES"

# Compile
echo "Compiling Swift sources..."
swiftc -o "$MACOS/$APP_NAME" \
    -target arm64-apple-macosx14.0 \
    -sdk $(xcrun --show-sdk-path) \
    -O \
    -framework SwiftUI \
    -framework Cocoa \
    -framework Carbon \
    -parse-as-library \
    App/*.swift \
    Models/*.swift \
    Services/*.swift \
    UI/Launcher/*.swift \
    UI/Components/*.swift \
    UI/Settings/*.swift \
    Utilities/*.swift

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

# Copy Info.plist
echo "Copying configuration..."
cp "Resources/Info.plist" "$CONTENTS/Info.plist"

# Create PkgInfo
echo "APPL????" > "$CONTENTS/PkgInfo"

# Code Signing (Ad-hoc)
echo "Signing app..."
codesign --force --deep --sign - "$APP_BUNDLE"

# Verify
echo "Verifying build..."
if [ ! -f "$MACOS/$APP_NAME" ]; then
    echo "Error: Executable missing."
    exit 1
fi

# Create DMG
echo "Packaging into DMG..."
DMG_SRC="$BUILD_DIR/dmg_source"
mkdir -p "$DMG_SRC"
cp -r "$APP_BUNDLE" "$DMG_SRC/"
ln -s /Applications "$DMG_SRC/Applications"

# Create disk image
hdiutil create -volname "$APP_NAME Installer" -srcfolder "$DMG_SRC" -ov -format UDZO "$DMG_NAME" > /dev/null

# Cleanup DMG source
rm -rf "$DMG_SRC"

echo "========================================"
echo "✅ Build Complete!"
echo "📱 App: $APP_BUNDLE"
echo "💿 Installer: $PWD/$DMG_NAME"
echo "========================================"
