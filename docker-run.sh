#!/usr/bin/env bash
# Rebuild llm-workspace from source and start it. Same as ./start.sh --rebuild.
exec "$(dirname "$0")/start.sh" --rebuild
