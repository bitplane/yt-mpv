#!/usr/bin/env bash

source .venv/bin/activate

MODULE_NAME=$(echo "$1" | tr '-' '_')
pytest --cov="src/$MODULE_NAME" --cov-report=html .

