#!/bin/bash
set -e

echo "=================================================="
echo "🤖 Starting J.A.R.V.I.S. Brain Core on Home Assistant..."
echo "🏠 Machine: HP t620 (x86_64)"
echo "📌 Version: v2.7.1 (Central Brain Core 24/7)"
echo "=================================================="

OPTIONS_FILE="/data/options.json"

if [ -f "$OPTIONS_FILE" ]; then
    echo "📋 Loading Add-on configuration from $OPTIONS_FILE..."
    export GEMINI_API_KEY=$(jq -r '.gemini_api_key // empty' $OPTIONS_FILE)
    export MAC_AGENT_URL=$(jq -r '.mac_agent_url // "http://192.168.1.100:5050"' $OPTIONS_FILE)
    export SPEECH_LANGUAGE=$(jq -r '.speech_language // "th"' $OPTIONS_FILE)
fi

echo "🚀 Starting Jarvis API Server on port 5050..."
python -u server.py
