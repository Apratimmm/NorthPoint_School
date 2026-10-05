#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt
npm install

echo "Building Tailwind CSS..."
node_modules/.bin/tailwindcss -i static/tailwind.css -o static/dist/tailwind.css --minify

echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

rm -rf staticfiles/admin staticfiles/cloudinary

echo "Build complete!"
