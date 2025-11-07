#!/bin/bash
# Show project structure

echo "📁 Comversa Phase 1 - Project Structure"
echo "========================================"
echo ""

tree -L 2 -I 'venv|__pycache__|*.pyc|.DS_Store' --dirsfirst || {
    echo "Note: 'tree' command not installed. Using ls instead:"
    echo ""
    ls -R | grep ":$" | sed -e 's/:$//' -e 's/[^-][^\/]*\//--/g' -e 's/^/   /' -e 's/-/|/'
}
