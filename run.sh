#!/bin/bash
echo "=== Alternate Reality: Modern Demo ==="
echo "Checking Python environment..."
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found."
  exit 1
fi

if ! python3 -m pip show pygame &>/dev/null; then
  echo "Installing pygame..."
  python3 -m pip install -r requirements.txt
fi

# Regenerate assets if missing
if [ ! -f assets/images/floor.png ]; then
  echo "Generating environment textures..."
  python3 make_assets.py
fi

if [ ! -f assets/interiors/tavern.png ]; then
  echo "Generating interior art..."
  python3 make_interiors.py
fi

echo "Launching game..."
python3 main_pygame.py
