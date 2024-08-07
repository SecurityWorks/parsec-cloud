# This script is used to create a signed release of Parsec
# using a single command from the pre-built windows artefact.

# This is meant to be run in the `client/electron` directory.

# Stop at first error
$ErrorActionPreference = "Stop"

# Check node version
$expected_node_version = "v18.12.0"
$node_version = node --version
if (-Not ($node_version -eq $expected_node_version)) {
    fnm use $expected_node_version
}

# Cleanup dist directory
if (Test-Path dist) {
    rm dist -r -force
}

# Install node-modules
npm clean-install

# Build and sign the release
npm run electron:sign
