#!/usr/bin/env python3
"""
Setup script for Certificate Generator
Creates necessary folders and copies template files
"""

import os
import shutil
import json

def create_folder_structure():
    """Create necessary folders for the certificate generator"""
    folders = [
        'static',
        'static/templates',
        'static/previews', 
        'static/fonts',
        'certificates',
        'templates'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✓ Created folder: {folder}")

def copy_template_files():
    """Copy PDF template files to the templates folder"""
    # Check if we have the template files in the current directory
    template_files = ['black_template.pdf', 'brown_floral_template.pdf']
    
    for template_file in template_files:
        if os.path.exists(template_file):
            dest_path = os.path.join('static', 'templates', template_file)
            shutil.copy2(template_file, dest_path)
            print(f"✓ Copied template: {template_file}")
        else:
            print(f"⚠ Template file not found: {template_file}")

def create_default_config():
    """Create default template configuration"""
    config = {
        "black_template.pdf": {
            "name_position": {"x": 0.5, "y": 0.45},
            "font_size": 45,
            "font_color": [1.0, 0.84, 0.0],
            "font_name": "PinyonScriptRegular",
            "text_alignment": "center"
        },
        "brown_floral_template.pdf": {
            "name_position": {"x": 0.5, "y": 0.55},
            "font_size": 40,
            "font_color": [0.4, 0.2, 0.0],
            "font_name": "PinyonScriptRegular",
            "text_alignment": "center"
        }
    }
    
    with open('template_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Created default template configuration")

def create_sample_font():
    """Create a note about fonts"""
    fonts_readme = """
# Fonts Folder

Place your custom TTF font files in this folder.

Recommended fonts for certificates:
- PinyonScript-Regular.ttf (elegant script font)
- Dancing-Script.ttf (casual script font)
- Great-Vibes.ttf (decorative script font)

You can download these fonts from Google Fonts or other font providers.

The application will automatically detect and load TTF files placed in this folder.
"""
    
    with open('static/fonts/README.md', 'w') as f:
        f.write(fonts_readme)
    
    print("✓ Created fonts README")

def main():
    """Main setup function"""
    print("🚀 Setting up Certificate Generator...")
    print("=" * 50)
    
    create_folder_structure()
    copy_template_files()
    create_default_config()
    create_sample_font()
    
    print("=" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Place your PDF template files in the 'static/templates' folder")
    print("2. Place your TTF font files in the 'static/fonts' folder")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run the application: python app.py")
    print("\nThe application will be available at: http://localhost:5000")

if __name__ == "__main__":
    main()