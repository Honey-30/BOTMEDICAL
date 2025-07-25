"""
Simple test script to verify the backend setup
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test core modules
        from app.core.config import settings
        print("✓ Config imported")
        
        from app.core.database import Base, get_db
        print("✓ Database imported")
        
        from app.core.security import get_password_hash
        print("✓ Security imported")
        
        # Test models
        from app.models.user import User
        from app.models.project import Project
        from app.models.task import Task
        from app.models.notification import Notification
        print("✓ Models imported")
        
        # Test services
        from app.services.ai_service import AIService
        print("✓ Services imported")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection"""
    try:
        from app.core.database import test_connection
        if test_connection():
            print("✓ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Backend Setup\n")
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print()
    
    # Test database
    if not test_database():
        success = False
    
    print()
    
    if success:
        print("✅ All tests passed! Backend is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    exit(main())