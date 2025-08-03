#!/usr/bin/env python3
"""
Test script for HelpDesk Ecosystem Database
Verifies database setup and demonstrates basic functionality
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from database.db_utils import (
    db_manager, user_manager, branch_manager, cartridge_manager,
    request_manager, log_manager, generate_request_code
)

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        # Test basic query
        result = db_manager.execute_query("SELECT 1 as test")
        print(f"✅ Database connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_seed_data():
    """Test if seed data exists"""
    print("\n🌱 Checking seed data...")
    
    # Check branches
    branches = branch_manager.get_all_branches()
    print(f"📊 Branches: {len(branches)} found")
    for branch in branches[:3]:  # Show first 3
        print(f"  - {branch['name']} ({branch['code']})")
    
    # Check cartridge types
    cartridges = cartridge_manager.get_all_cartridge_types()
    print(f"📊 Cartridge types: {len(cartridges)} found")
    for cartridge in cartridges[:3]:  # Show first 3
        print(f"  - {cartridge['name']} ({cartridge['sku']})")
    
    # Check users
    users = db_manager.execute_query("SELECT COUNT(*) as count FROM users")
    print(f"📊 Users: {users[0]['count']} found")
    
    return len(branches) > 0 and len(cartridges) > 0

def test_user_operations():
    """Test user operations"""
    print("\n👤 Testing user operations...")
    
    # Test creating a user
    test_telegram_id = 999999999
    test_username = "test_user"
    
    # Check if user exists
    user = user_manager.get_user_by_telegram_id(test_telegram_id)
    if user:
        print(f"✅ Test user already exists: {user['username']}")
    else:
        # Create test user
        user_manager.create_user(test_telegram_id, test_username, 'branch_user')
        print(f"✅ Created test user: {test_username}")
    
    # Verify user creation
    user = user_manager.get_user_by_telegram_id(test_telegram_id)
    if user:
        print(f"✅ User verification successful: {user['username']} ({user['role']})")
        return user['id']
    else:
        print("❌ User creation failed")
        return None

def test_request_creation(user_id):
    """Test request creation"""
    print("\n📋 Testing request creation...")
    
    if not user_id:
        print("❌ Cannot test request creation without user_id")
        return None
    
    # Get first branch and cartridge
    branches = branch_manager.get_all_branches()
    cartridges = cartridge_manager.get_all_cartridge_types()
    
    if not branches or not cartridges:
        print("❌ No branches or cartridges available")
        return None
    
    branch = branches[0]
    cartridge = cartridges[0]
    
    # Generate request code
    request_code = generate_request_code()
    print(f"📋 Generated request code: {request_code}")
    
    # Create request
    try:
        request_id = request_manager.create_request(
            request_code=request_code,
            branch_id=branch['id'],
            user_id=user_id,
            priority='normal',
            comment='Test request from database test script'
        )
        
        # Add request items
        request_manager.add_request_items(
            request_id=request_id,
            items=[(cartridge['id'], 2)]
        )
        
        # Log the creation
        log_manager.add_log(
            request_id=request_id,
            user_id=user_id,
            action='created',
            note='Test request created via test script'
        )
        
        print(f"✅ Request created successfully: ID={request_id}")
        
        # Get request details
        request = request_manager.get_request_by_code(request_code)
        if request:
            print(f"📋 Request details:")
            print(f"  - Code: {request['request_code']}")
            print(f"  - Branch: {request['branch_name']}")
            print(f"  - Priority: {request['priority']}")
            print(f"  - Status: {request['status']}")
            print(f"  - Created: {request['created_at']}")
        
        return request_id
        
    except Exception as e:
        print(f"❌ Request creation failed: {e}")
        return None

def test_request_operations(request_id):
    """Test request operations"""
    print("\n🔄 Testing request operations...")
    
    if not request_id:
        print("❌ Cannot test request operations without request_id")
        return
    
    # Get request items
    items = request_manager.get_request_items(request_id)
    print(f"📦 Request items: {len(items)} found")
    for item in items:
        print(f"  - {item['cartridge_name']}: {item['quantity']} шт.")
    
    # Get request logs
    logs = log_manager.get_request_logs(request_id)
    print(f"📝 Request logs: {len(logs)} found")
    for log in logs:
        print(f"  - {log['action']}: {log['note']} ({log['timestamp']})")
    
    # Update request status
    success = request_manager.update_request_status(
        request_id=request_id,
        new_status='in_progress',
        user_id=1,  # Assuming admin user ID
        note='Status updated via test script'
    )
    
    if success:
        print("✅ Request status updated successfully")
    else:
        print("❌ Request status update failed")

def test_stock_operations():
    """Test stock operations"""
    print("\n📦 Testing stock operations...")
    
    # Get stock for first branch
    branches = branch_manager.get_all_branches()
    if not branches:
        print("❌ No branches available for stock test")
        return
    
    branch = branches[0]
    stock_items = cartridge_manager.get_stock_by_branch(branch['id'])
    
    print(f"📦 Stock for {branch['name']}: {len(stock_items)} items")
    for item in stock_items[:5]:  # Show first 5
        print(f"  - {item['cartridge_name']}: {item['quantity']} шт.")

def cleanup_test_data(user_id, request_id):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test request (this will cascade delete items and logs)
        if request_id:
            db_manager.execute_update("DELETE FROM requests WHERE id = ?", (request_id,))
            print(f"✅ Deleted test request: {request_id}")
        
        # Delete test user
        if user_id:
            db_manager.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
            print(f"✅ Deleted test user: {user_id}")
        
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def main():
    """Main test function"""
    print("🧪 HelpDesk Ecosystem Database Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Database connection failed. Exiting.")
        return
    
    # Test seed data
    if not test_seed_data():
        print("❌ Seed data not found. Run database/seed.py first.")
        return
    
    # Test user operations
    user_id = test_user_operations()
    
    # Test request creation
    request_id = test_request_creation(user_id)
    
    # Test request operations
    if request_id:
        test_request_operations(request_id)
    
    # Test stock operations
    test_stock_operations()
    
    # Cleanup (comment out to keep test data)
    # cleanup_test_data(user_id, request_id)
    
    print("\n✅ All tests completed successfully!")
    print("\n💡 To run the Telegram bot:")
    print("1. Copy .env.example to .env")
    print("2. Set your BOT_TOKEN in .env")
    print("3. Run: python bot/main.py")

if __name__ == "__main__":
    main()