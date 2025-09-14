#!/usr/bin/env python3
"""Check if UI is built before packaging."""

import sys
from pathlib import Path

def check_ui_built():
    """Check if the React UI is built and ready for packaging."""
    ui_dir = Path(__file__).parent.parent / "src" / "any_agent" / "ui"
    dist_dir = ui_dir / "dist"
    
    # Check essential UI build files
    required_files = [
        dist_dir / "index.html",
        dist_dir / "assets"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print("❌ UI build check failed!")
        print("Missing required UI build files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print()
        print("🔨 Build the UI first:")
        print("  python -m any_agent.ui build")
        print("  # or")
        print("  cd src/any_agent/ui && npm run build")
        return False
    
    # Check for assets
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        
        print("✅ UI build check passed!")
        print(f"📦 Found {len(js_files)} JS files and {len(css_files)} CSS files")
        print(f"📍 Build location: {dist_dir}")
        return True
    else:
        print("❌ UI assets directory not found!")
        return False

if __name__ == "__main__":
    if check_ui_built():
        sys.exit(0)
    else:
        sys.exit(1)