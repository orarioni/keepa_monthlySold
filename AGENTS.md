# AGENTS.md

## Project guidance
- This repository contains business automation code.
- Prefer minimal, reversible changes.
- Do not hardcode secrets.
- Keep Windows local build in mind.
- Do not add cloud-only packaging steps unless explicitly requested.

## Build guidance
- Assume final executable builds happen on a local Windows machine.
- Prepare source code, config templates, batch launcher, and build documentation.
- Prefer PyInstaller onedir assumptions unless the task explicitly says otherwise.

## File handling
- Resolve input/output/config/log paths relative to the script or executable directory.
- Preserve original Excel columns and append new columns.

## Safety and reliability
- Continue processing even if some ASIN requests fail.
- Log failures clearly.
- Avoid destructive changes to existing files unless requested.

## Documentation
- Update README when adding setup, config, or build requirements.