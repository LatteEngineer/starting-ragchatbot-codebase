#!/bin/bash

# Run code quality checks
echo "Running flake8 to check code quality..."
uv run flake8 backend/ main.py

if [ $? -eq 0 ]; then
    echo "✅ Linting passed!"
else
    echo "❌ Linting failed. Please fix the issues above."
    exit 1
fi
