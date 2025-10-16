#!/usr/bin/env python3
"""
Debug script to test Clock out button detection with detailed logging
"""

import sys
import os
import time
import logging
from pathlib import Path
from selenium.webdriver.common.by import By

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from helpers.tools.paylocity_client import PaylocityClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_clock_out_button():
    """Debug Clock out button detection"""
    client = PaylocityClient(headless=False)  # Run with GUI to see what's happening
    
    try:
        print("🚀 Starting Paylocity client...")
        if not client.start():
            print("❌ Failed to start client")
            return False
            
        print("🔐 Logging in...")
        if not client.login():
            print("❌ Login failed")
            return False
            
        print("🔍 Debugging Clock out button detection...")
        
        # Test each selector individually with detailed logging
        clock_out_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
            "//button[text()='clock out']",
            "//button[contains(text(), 'Clock out')]",
            "//button[contains(text(), 'clock out')]",
            "//button[contains(@class, 'clock-out')]",
            "//input[@value='Clock out']",
            "//button[contains(@id, 'clock-out')]"
        ]
        
        for i, selector in enumerate(clock_out_selectors, 1):
            print(f"\n🧪 Testing selector {i}: {selector}")
            try:
                elements = client.driver.find_elements(By.XPATH, selector)
                print(f"   Found {len(elements)} elements")
                
                for j, element in enumerate(elements):
                    try:
                        text = element.text
                        enabled = element.is_enabled()
                        displayed = element.is_displayed()
                        tag = element.tag_name
                        print(f"   Element {j}: <{tag}> '{text}' (enabled: {enabled}, displayed: {displayed})")
                        
                        if displayed and enabled and 'clock out' in text.lower():
                            print(f"   ✅ MATCH FOUND!")
                            return True
                    except Exception as e:
                        print(f"   Error getting element {j} details: {e}")
                        
            except Exception as e:
                print(f"   ❌ Selector failed: {e}")
        
        print("\n❌ No Clock out button found with any selector")
        return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False
        
    finally:
        if client.driver:
            print("🛑 Closing browser...")
            client.driver.quit()

if __name__ == "__main__":
    print("🔍 Debugging Clock out button detection...")
    success = debug_clock_out_button()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
