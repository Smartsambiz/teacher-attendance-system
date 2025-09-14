#!/usr/bin/env bash
set -e

echo "=== Starting Build Process ==="

echo "Python path: $(which python)"
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la
echo "=== Installing Dependencies ==="

pip install -r requirements.txt

echo "=== Running Database Migrations and Collecting Static Files ==="
python manage.py collectstatic --noinput
python manage.py migrate

echo "=== Build Process Completed ==="