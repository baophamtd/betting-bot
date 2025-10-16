"""
Test Paylocity Login
Quick test to verify Paylocity login automation works
"""

import os
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from helpers.tools.paylocity_client import PaylocityClient

def test_paylocity_login():
    """Test Paylocity login functionality"""
    print("🕐 Testing Paylocity Login...")
    
    # Check credentials
    company_id = os.getenv('PAYLOCITY_COMPANY_ID')
    username = os.getenv('PAYLOCITY_USERNAME')
    password = os.getenv('PAYLOCITY_PASSWORD')
    
    if not all([company_id, username, password]):
        print("❌ Missing Paylocity credentials!")
        print("Please add to .env file:")
        print("PAYLOCITY_COMPANY_ID=301469")
        print("PAYLOCITY_USERNAME=your_username")
        print("PAYLOCITY_PASSWORD=your_password")
        return False
    
    print(f"✅ Credentials found: Company ID={company_id}, Username={username}")
    
    # Initialize client
    client = PaylocityClient(headless=False)  # Show browser for testing
    
    try:
        # Start browser
        if not client.start():
            print("❌ Failed to start browser")
            return False
        
        # Attempt login
        print("🔐 Attempting login...")
        if client.login():
            print("✅ Login successful!")
            
            # Take screenshot
            screenshot_path = "logs/paylocity_login_success.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            client.driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Wait a bit to see the page
            time.sleep(5)
            
            return True
        else:
            print("❌ Login failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = test_paylocity_login()
    if success:
        print("\n🎉 Paylocity login test PASSED!")
    else:
        print("\n💥 Paylocity login test FAILED!")
