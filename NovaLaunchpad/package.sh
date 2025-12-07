#!/bin/bash

# Configuration
APP_NAME="NovaLaunchpad"
SCHEME="NovaLaunchpad"
BUILD_DIR="build"
DMG_NAME="${APP_NAME}_Installer.dmg"

# Clean
rm -rf "$BUILD_DIR"
rm -f "$DMG_NAME"

# Build App
echo "Building $APP_NAME..."
mkdir -p "$BUILD_DIR"

# Note: In a real environment, you'd use a .xcodeproj or .xcworkspace. 
# Since we are generating files raw, we need to create a project first or use swift build (if valid Package.swift)
# Assuming the user will create an Xcode project or we can try to compile with swiftc (hard for app bundles with resources).
# Best approach: Assume user puts this in an Xcode project or run xcodebuild if project exists.
# For this script to work, the user needs to create the Xcode project 'NovaLaunchpad.xcodeproj'.

if [ ! -d "$APP_NAME.xcodeproj" ]; then
    echo "Error: $APP_NAME.xcodeproj not found. Please create the Xcode project first."
    echo "Steps:"
    echo "1. Open Xcode -> Create New Project -> App"
    echo "2. Name it NovaLaunchpad"
    echo "3. Replace the generated files with the ones in this directory."
    exit 1
fi

xcodebuild -project "$APP_NAME.xcodeproj" -scheme "$SCHEME" -configuration Release -derivedDataPath "$BUILD_DIR" build

APP_PATH=$(find "$BUILD_DIR/Build/Products/Release" -name "$APP_NAME.app")

if [ -z "$APP_PATH" ]; then
    echo "Build failed."
    exit 1
fi

echo "Build successful. Packaging..."

# Create DMG
# Create a temporary folder for DMG contents
DMG_SRC="dmg_source"
mkdir -p "$DMG_SRC"
cp -r "$APP_PATH" "$DMG_SRC/"
ln -s /Applications "$DMG_SRC/Applications"

# Create DMG file
hdiutil create -volname "$APP_NAME Installer" -srcfolder "$DMG_SRC" -ov -format UDZO "$DMG_NAME"

# Cleanup
rm -rf "$DMG_SRC"

echo "Done! Created $DMG_NAME"
