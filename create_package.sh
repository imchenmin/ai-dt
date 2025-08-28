#!/bin/bash

# Package creation script for AI-Driven Test Generator
# Excludes files and directories specified in .gitignore

PACKAGE_NAME="ai-dt"
VERSION="1.0.1"
PACKAGE_DIR="${PACKAGE_NAME}-${VERSION}"

# Create package directory
mkdir -p "${PACKAGE_DIR}"

# Copy all files, excluding .gitignore patterns
echo "Creating package: ${PACKAGE_DIR}"
echo "Copying files (excluding .gitignore patterns)..."

# Use rsync to copy files while respecting .gitignore patterns
rsync -av --progress \
    --exclude-from=.gitignore \
    --exclude='.git/' \
    --exclude='.claude/' \
    --exclude='${PACKAGE_DIR}/' \
    --exclude='*.tar.gz' \
    . "${PACKAGE_DIR}/"

# Create tar.gz package
echo "Creating tar.gz package..."
tar -czf "${PACKAGE_NAME}-${VERSION}.tar.gz" "${PACKAGE_DIR}"

# Clean up
echo "Cleaning up..."
rm -rf "${PACKAGE_DIR}"

echo "Package created: ${PACKAGE_NAME}-${VERSION}.tar.gz"
echo "Package contents:"
tar -tzf "${PACKAGE_NAME}-${VERSION}.tar.gz" | head -20
echo "..."

# Show package size
echo "Package size:"
du -h "${PACKAGE_NAME}-${VERSION}.tar.gz"