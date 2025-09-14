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

if [ -f "superuser.json" ]; then
    echo "Loading superuser data..."
    python manage.py loaddata superuser.json
    echo "Superuser loaded successfully"
    
    # Optional: remove the file after loading to prevent accidental reloads
    rm -f superuser.json
    echo "Temporary superuser file removed"
else
    echo "Superuser file not found, skipping load"
fi


echo "=== Build Process Completed ==="