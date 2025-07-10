"""
Quick verification script for Healthcare Chatbot setup
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_setup():
    """Verify that all components are properly set up."""
    print("🔍 Verifying Healthcare Chatbot Setup...")
    print("=" * 50)
    
    # Check environment file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("❌ .env file missing")
        return False
    
    # Check templates
    template_files = [
        'templates/base.html',
        'templates/index.html', 
        'templates/about.html',
        'templates/dashboard_new.html'
    ]
    
    for template in template_files:
        if os.path.exists(template):
            print(f"✅ {template} found")
        else:
            print(f"❌ {template} missing")
            
    # Check app structure
    app_files = [
        'app/__init__.py',
        'app/models.py',
        'requirements.txt',
        'run.py'
    ]
    
    for app_file in app_files:
        if os.path.exists(app_file):
            print(f"✅ {app_file} found")
        else:
            print(f"❌ {app_file} missing")
    
    # Test imports
    try:
        from dotenv import load_dotenv
        print("✅ dotenv import successful")
    except ImportError:
        print("❌ dotenv not installed")
        
    try:
        from flask import Flask
        print("✅ Flask import successful")
    except ImportError:
        print("❌ Flask not installed")
        
    # Check if we can import the app
    try:
        from app.models import db, User
        print("✅ App models import successful")
    except ImportError as e:
        print(f"⚠️  App models import failed: {e}")
        print("   This might be okay - will use fallback mode")
    
    print("=" * 50)
    print("🚀 Setup verification complete!")
    print("💡 Run 'python run.py' to start the application")
    
    return True

if __name__ == '__main__':
    verify_setup()
