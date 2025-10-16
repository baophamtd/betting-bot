"""
Paylocity Clock In/Out Automation Client
Handles login and timekeeping actions on access.paylocity.com
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from dotenv import load_dotenv
import os

load_dotenv()

class PaylocityClient:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        
        # Credentials
        self.company_id = os.getenv('PAYLOCITY_COMPANY_ID')
        self.username = os.getenv('PAYLOCITY_USERNAME') 
        self.password = os.getenv('PAYLOCITY_PASSWORD')
        
        # Paylocity URLs
        self.base_url = "https://access.paylocity.com"
        self.login_url = f"{self.base_url}/"
        
        # Login selectors (based on the screenshot)
        self.login_selectors = {
            'company_id': (By.ID, 'CompanyId'),
            'username': (By.ID, 'Username'),
            'password': (By.ID, 'Password'),
            'login_button': (By.XPATH, "//button[contains(text(), 'Login')]"),
            'remember_username': (By.ID, 'RememberUsername')
        }

    def start(self):
        """Initialize the browser driver"""
        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
            
            # Anti-detection options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("🚀 Paylocity client started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Paylocity client: {e}")
            return False

    def login(self):
        """Login to Paylocity"""
        if not self.driver:
            self.logger.error("❌ Driver not initialized")
            return False
            
        if not all([self.company_id, self.username, self.password]):
            self.logger.error("❌ Missing Paylocity credentials in .env file")
            return False

        try:
            self.logger.info("🌐 Navigating to Paylocity login page...")
            self.driver.get(self.login_url)
            time.sleep(3)

            # Wait for login form to load
            wait = WebDriverWait(self.driver, 10)
            
            # Fill Company ID
            self.logger.info("📝 Entering Company ID...")
            company_field = wait.until(EC.presence_of_element_located(self.login_selectors['company_id']))
            company_field.clear()
            company_field.send_keys(self.company_id)
            time.sleep(1)

            # Fill Username
            self.logger.info("👤 Entering username...")
            username_field = self.driver.find_element(*self.login_selectors['username'])
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)

            # Fill Password
            self.logger.info("🔒 Entering password...")
            password_field = self.driver.find_element(*self.login_selectors['password'])
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)

            # Check "Remember My Username" if not already checked
            try:
                remember_checkbox = self.driver.find_element(*self.login_selectors['remember_username'])
                if not remember_checkbox.is_selected():
                    remember_checkbox.click()
                    self.logger.info("✅ Checked 'Remember My Username'")
                time.sleep(1)
            except NoSuchElementException:
                self.logger.info("⚠️ Remember username checkbox not found")

            # Click Login button
            self.logger.info("🔐 Clicking login button...")
            login_button = self.driver.find_element(*self.login_selectors['login_button'])
            login_button.click()

            # Wait for login to complete - look for dashboard or error
            self.logger.info("⏳ Waiting for login to complete...")
            max_wait = 30
            poll_interval = 2
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                # Check if we're logged in (look for dashboard elements)
                try:
                    # Look for common dashboard elements that indicate successful login
                    dashboard_indicators = [
                        "//a[contains(@href, 'TimeEntry')]",
                        "//a[contains(text(), 'Time Entry')]",
                        "//div[contains(@class, 'dashboard')]",
                        "//nav[contains(@class, 'navigation')]",
                        "//button[contains(text(), 'Clock In')]",
                        "//button[contains(text(), 'Clock Out')]"
                    ]
                    
                    for indicator in dashboard_indicators:
                        try:
                            element = self.driver.find_element(By.XPATH, indicator)
                            if element.is_displayed():
                                self.logger.info(f"✅ Login successful! Found dashboard element: {indicator}")
                                return True
                        except NoSuchElementException:
                            continue
                    
                    # Check if still on login page (error indicators)
                    if "access.paylocity.com" in self.driver.current_url and "login" in self.driver.current_url.lower():
                        self.logger.info(f"⏳ Still on login page... ({elapsed}s)")
                        continue
                    else:
                        # URL changed, likely logged in
                        self.logger.info(f"✅ Login successful! URL changed to: {self.driver.current_url}")
                        return True
                        
                except Exception as e:
                    self.logger.info(f"⏳ Checking login status... ({elapsed}s)")
                    
            self.logger.warning(f"⚠️ Waited {max_wait}s but couldn't confirm login")
            return False

        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False

    def find_time_entry_page(self):
        """Navigate to the time entry page"""
        try:
            self.logger.info("🔍 Looking for Time Entry page...")
            
            # Common selectors for time entry navigation
            time_entry_selectors = [
                "//a[contains(@href, 'TimeEntry')]",
                "//a[contains(text(), 'Time Entry')]",
                "//a[contains(text(), 'Time')]",
                "//button[contains(text(), 'Time Entry')]",
                "//div[contains(@class, 'time-entry')]//a",
                "//nav//a[contains(@href, 'time')]"
            ]
            
            for selector in time_entry_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        self.logger.info(f"✅ Found Time Entry link: {selector}")
                        element.click()
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ Could not find Time Entry page link")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error finding Time Entry page: {e}")
            return False

    def clock_in(self):
        """Clock in action"""
        try:
            self.logger.info("🕐 Attempting to clock in...")
            
            if not self.find_time_entry_page():
                return False
                
            # Look for clock in button
            clock_in_selectors = [
                "//button[contains(text(), 'Clock In')]",
                "//button[contains(@class, 'clock-in')]",
                "//input[@value='Clock In']",
                "//button[contains(@id, 'clock-in')]",
                "//a[contains(text(), 'Clock In')]"
            ]
            
            for selector in clock_in_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found Clock In button: {selector}")
                        button.click()
                        time.sleep(2)
                        
                        # Look for success confirmation
                        success_indicators = [
                            "//div[contains(text(), 'Clocked In')]",
                            "//div[contains(text(), 'success')]",
                            "//span[contains(text(), 'Clocked In')]"
                        ]
                        
                        for success_selector in success_indicators:
                            try:
                                success_elem = self.driver.find_element(By.XPATH, success_selector)
                                if success_elem.is_displayed():
                                    self.logger.info("✅ Clock in successful!")
                                    return True
                            except NoSuchElementException:
                                continue
                        
                        self.logger.info("✅ Clock in button clicked")
                        return True
                        
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ Clock In button not found or not available")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Clock in failed: {e}")
            return False

    def clock_out(self):
        """Clock out action"""
        try:
            self.logger.info("🕕 Attempting to clock out...")
            
            if not self.find_time_entry_page():
                return False
                
            # Look for clock out button
            clock_out_selectors = [
                "//button[contains(text(), 'Clock Out')]",
                "//button[contains(@class, 'clock-out')]",
                "//input[@value='Clock Out']",
                "//button[contains(@id, 'clock-out')]",
                "//a[contains(text(), 'Clock Out')]"
            ]
            
            for selector in clock_out_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found Clock Out button: {selector}")
                        button.click()
                        time.sleep(2)
                        
                        # Look for success confirmation
                        success_indicators = [
                            "//div[contains(text(), 'Clocked Out')]",
                            "//div[contains(text(), 'success')]",
                            "//span[contains(text(), 'Clocked Out')]"
                        ]
                        
                        for success_selector in success_indicators:
                            try:
                                success_elem = self.driver.find_element(By.XPATH, success_selector)
                                if success_elem.is_displayed():
                                    self.logger.info("✅ Clock out successful!")
                                    return True
                            except NoSuchElementException:
                                continue
                        
                        self.logger.info("✅ Clock out button clicked")
                        return True
                        
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ Clock Out button not found or not available")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Clock out failed: {e}")
            return False

    def start_lunch(self):
        """Start lunch break"""
        try:
            self.logger.info("🍽️ Attempting to start lunch...")
            
            if not self.find_time_entry_page():
                return False
                
            # Look for lunch start button
            lunch_start_selectors = [
                "//button[contains(text(), 'Start Lunch')]",
                "//button[contains(text(), 'Lunch Out')]",
                "//button[contains(@class, 'lunch-start')]",
                "//input[@value='Start Lunch']",
                "//button[contains(@id, 'lunch-start')]"
            ]
            
            for selector in lunch_start_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found Start Lunch button: {selector}")
                        button.click()
                        time.sleep(2)
                        self.logger.info("✅ Lunch started!")
                        return True
                        
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ Start Lunch button not found or not available")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Start lunch failed: {e}")
            return False

    def end_lunch(self):
        """End lunch break"""
        try:
            self.logger.info("🍽️ Attempting to end lunch...")
            
            if not self.find_time_entry_page():
                return False
                
            # Look for lunch end button
            lunch_end_selectors = [
                "//button[contains(text(), 'End Lunch')]",
                "//button[contains(text(), 'Lunch In')]",
                "//button[contains(@class, 'lunch-end')]",
                "//input[@value='End Lunch']",
                "//button[contains(@id, 'lunch-end')]"
            ]
            
            for selector in lunch_end_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found End Lunch button: {selector}")
                        button.click()
                        time.sleep(2)
                        self.logger.info("✅ Lunch ended!")
                        return True
                        
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ End Lunch button not found or not available")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ End lunch failed: {e}")
            return False

    def get_current_status(self):
        """Get current clock status"""
        try:
            self.logger.info("📊 Checking current status...")
            
            if not self.find_time_entry_page():
                return None
                
            # Look for status indicators
            status_selectors = [
                "//div[contains(@class, 'status')]",
                "//span[contains(@class, 'clock-status')]",
                "//div[contains(text(), 'Clocked')]",
                "//span[contains(text(), 'In') or contains(text(), 'Out')]"
            ]
            
            for selector in status_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        status = element.text.strip()
                        self.logger.info(f"📊 Current status: {status}")
                        return status
                except NoSuchElementException:
                    continue
                    
            self.logger.info("📊 Status not clearly visible")
            return "Unknown"
            
        except Exception as e:
            self.logger.error(f"❌ Error getting status: {e}")
            return None

    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🔒 Browser closed")
            except Exception as e:
                self.logger.error(f"❌ Error closing browser: {e}")
