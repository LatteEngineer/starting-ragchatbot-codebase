#!/bin/bash

# Run all code quality checks
echo "🔍 Running code quality checks..."
echo ""

# Check if code is formatted correctly (dry run)
echo "1. Checking code formatting with black..."
uv run black --check .
BLACK_EXIT=$?

echo ""
echo "2. Checking import organization with isort..."
uv run isort --check-only .
ISORT_EXIT=$?

echo ""
echo "3. Running flake8 linter..."
uv run flake8 backend/ main.py
FLAKE8_EXIT=$?

echo ""
echo "================================"
echo "Quality Check Summary:"
echo "================================"

if [ $BLACK_EXIT -eq 0 ]; then
    echo "✅ Black formatting: PASSED"
else
    echo "❌ Black formatting: FAILED (run ./format.sh to fix)"
fi

if [ $ISORT_EXIT -eq 0 ]; then
    echo "✅ Import sorting: PASSED"
else
    echo "❌ Import sorting: FAILED (run ./format.sh to fix)"
fi

if [ $FLAKE8_EXIT -eq 0 ]; then
    echo "✅ Flake8 linting: PASSED"
else
    echo "❌ Flake8 linting: FAILED"
fi

echo "================================"

# Exit with error if any check failed
if [ $BLACK_EXIT -ne 0 ] || [ $ISORT_EXIT -ne 0 ] || [ $FLAKE8_EXIT -ne 0 ]; then
    echo "❌ Some checks failed. Please fix the issues above."
    exit 1
else
    echo "✅ All quality checks passed!"
    exit 0
fi
