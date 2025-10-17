#!/bin/bash

# Format Python code with black and isort
echo "Running isort to organize imports..."
uv run isort .

echo "Running black to format code..."
uv run black .

echo "✅ Code formatting complete!"
