#!/usr/bin/env python3
"""
Setup script for HelpDesk Ecosystem
Helps users get started with the project
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_database():
    """Setup database with schema and seed data"""
    print("🗄️ Setting up database...")
    
    try:
        # Run seed script
        subprocess.check_call([sys.executable, "database/seed.py"])
        print("✅ Database setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_environment():
    """Setup environment configuration"""
    print("⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("⚠️ .env file already exists, skipping...")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("💡 Please edit .env file with your configuration")
        return True
    else:
        print("❌ .env.example not found")
        return False

def run_tests():
    """Run database tests"""
    print("🧪 Running database tests...")
    
    try:
        subprocess.check_call([sys.executable, "test_database.py"])
        print("✅ Tests completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "uploads",
        "logs",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration:")
    print("   - Set BOT_TOKEN (get from @BotFather)")
    print("   - Set ADMIN_IDS (your Telegram ID)")
    print("   - Configure other settings as needed")
    
    print("\n2. Start the Telegram bot:")
    print("   python3 bot/main.py")
    
    print("\n3. Optional: Start web panel (Django):")
    print("   python3 manage.py runserver")
    
    print("\n📚 Documentation:")
    print("- README.md - Project overview")
    print("- ROADMAP.md - Development roadmap")
    print("- database/schema.sql - Database structure")
    
    print("\n🔧 Available commands:")
    print("- python3 test_database.py - Test database functionality")
    print("- python3 database/seed.py - Re-seed database")
    print("- python3 bot/main.py - Start Telegram bot")

def main():
    """Main setup function"""
    print("🚀 HelpDesk Ecosystem Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment
    if not setup_environment():
        return False
    
    # Create directories
    create_directories()
    
    # Setup database
    if not setup_database():
        return False
    
    # Run tests
    if not run_tests():
        return False
    
    # Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)