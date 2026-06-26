#!/usr/bin/env bash

# Usage:
#   ./snapshot.sh /path/to/project
#   source utils/snapshot.sh ./cardputer_webshell/webshell

#set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <project_path>"
    exit 1
fi

PROJECT_PATH="$1"

if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: '$PROJECT_PATH' is not a directory"
    exit 1
fi

OUTPUT_FILE="snapshot.md"

> "$OUTPUT_FILE"

find "$PROJECT_PATH" \
    \( -type d \( \
        -name ".git" \
        -o -name "__pycache__" \
        -o -name ".venv" \
        -o -name "node_modules" \
        -o -name ".mypy_cache" \
        -o -name ".pytest_cache" \
    \) -prune \) -o \
    -type f -print |
while IFS= read -r file; do

    # Skip binary files
    if ! grep -Iq . "$file"; then
        continue
    fi

    rel_path="${file#$PROJECT_PATH/}"

    # Choose Markdown language from extension
    case "${file##*.}" in
        py)      lang="python" ;;
        sh)      lang="bash" ;;
        bash)    lang="bash" ;;
        zsh)     lang="zsh" ;;
        c)       lang="c" ;;
        h)       lang="c" ;;
        cpp|cc|cxx|hpp) lang="cpp" ;;
        rs)      lang="rust" ;;
        go)      lang="go" ;;
        js)      lang="javascript" ;;
        ts)      lang="typescript" ;;
        jsx)     lang="jsx" ;;
        tsx)     lang="tsx" ;;
        java)    lang="java" ;;
        kt)      lang="kotlin" ;;
        swift)   lang="swift" ;;
        html)    lang="html" ;;
        css)     lang="css" ;;
        scss)    lang="scss" ;;
        json)    lang="json" ;;
        yaml|yml) lang="yaml" ;;
        toml)    lang="toml" ;;
        xml)     lang="xml" ;;
        md)      lang="markdown" ;;
        sql)     lang="sql" ;;
        dockerfile) lang="dockerfile" ;;
        *)       lang="" ;;
    esac

    echo "$rel_path:" >> "$OUTPUT_FILE"
    echo "\`\`\`$lang" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo >> "$OUTPUT_FILE"

done

echo "Snapshot created in $OUTPUT_FILE"
