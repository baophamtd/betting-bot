"""
Paylocity Clock In/Out Automation Client
Handles login and timekeeping actions on access.paylocity.com
"""

import time
import logging
import subprocess
import re
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

    def _detect_chrome_version(self, chrome_binary):
        """Detect the installed Chrome version dynamically"""
        if not chrome_binary:
            return None
        
        import platform
        
        try:
            # On macOS, try reading from Info.plist first (more reliable)
            if platform.system() == 'Darwin' and chrome_binary.endswith('Google Chrome'):
                try:
                    info_plist_path = chrome_binary.replace('/Contents/MacOS/Google Chrome', '/Contents/Info.plist')
                    if os.path.exists(info_plist_path):
                        # Try using plistlib or defaults command
                        result = subprocess.run(
                            ['defaults', 'read', info_plist_path, 'CFBundleShortVersionString'],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        if result.returncode == 0:
                            version_str = result.stdout.strip()
                            match = re.search(r'^(\d+)\.', version_str)
                            if match:
                                major_version = int(match.group(1))
                                self.logger.info(f"✅ Detected Chrome version: {major_version} (from Info.plist: {version_str})")
                                return major_version
                except Exception:
                    pass  # Fall through to --version method
            
            # Try --version flag (works on Linux and Windows, sometimes macOS)
            result = subprocess.run(
                [chrome_binary, '--version'],
                capture_output=True,
                text=True,
                timeout=10  # Increased timeout
            )
            
            # Check both stdout and stderr for version info
            version_output = (result.stdout or result.stderr or "").strip()
            
            if version_output:
                # Extract major version number (e.g., "141" from "Google Chrome 141.0.6961.77")
                match = re.search(r'(\d+)\.\d+\.\d+\.\d+', version_output)
                if match:
                    major_version = int(match.group(1))
                    self.logger.info(f"✅ Detected Chrome version: {major_version} (from: {version_output})")
                    return major_version
                else:
                    # Fallback: try to find any version pattern
                    match = re.search(r'(\d+)', version_output)
                    if match:
                        major_version = int(match.group(1))
                        self.logger.info(f"✅ Detected Chrome version: {major_version} (from: {version_output})")
                        return major_version
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️ Chrome version detection timed out")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not detect Chrome version: {e}")
        
        return None

    def start(self):
        """Initialize the browser driver"""
        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')  # Use new headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
            
            # Anti-detection options
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Try to find Chrome binary explicitly (helps with auto-update issues)
            import platform
            system = platform.system()
            
            # Common Chrome binary locations by OS
            chrome_paths = {
                'Linux': [
                    '/usr/bin/google-chrome',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium',
                    '/snap/bin/chromium'
                ],
                'Darwin': [  # macOS
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    '/Applications/Chromium.app/Contents/MacOS/Chromium'
                ],
                'Windows': [
                    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
                ]
            }
            
            # Try to find Chrome binary
            chrome_binary = None
            for path in chrome_paths.get(system, []):
                if os.path.exists(path):
                    chrome_binary = path
                    self.logger.info(f"🔍 Found Chrome at: {path}")
                    break
            
            if chrome_binary:
                options.binary_location = chrome_binary
            
            # Automatically detect Chrome version to match driver
            detected_version = self._detect_chrome_version(chrome_binary)
            if detected_version:
                self.logger.info(f"🔧 Using detected Chrome version: {detected_version}")
                self.driver = uc.Chrome(options=options, version_main=detected_version)
            else:
                # Fallback to auto-detection if version detection fails
                self.logger.info("⚠️ Could not detect Chrome version, falling back to auto-detection")
                self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("🚀 Paylocity client started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Paylocity client: {e}")
            self.logger.error(f"💡 Try updating Chrome or running: pip install --upgrade undetected-chromedriver")
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

            # Wait for login to complete - handle "Skip for Now" and wait for dashboard
            self.logger.info("⏳ Waiting for login to complete...")
            max_wait = 60  # Increased wait time for full login flow
            poll_interval = 3
            elapsed = 0
            skip_clicked = False
            
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                # First, check for "Skip for Now" button and click it (only once)
                if not skip_clicked:
                    try:
                        skip_button_selectors = [
                            "//button[contains(text(), 'Skip for Now')]",
                            "//a[contains(text(), 'Skip for Now')]",
                            "//input[@value='Skip for Now']",
                            "//button[contains(@class, 'skip')]",
                            "//a[contains(@class, 'skip')]"
                        ]
                        
                        for selector in skip_button_selectors:
                            try:
                                skip_button = self.driver.find_element(By.XPATH, selector)
                                if skip_button.is_displayed():
                                    self.logger.info(f"🔄 Found 'Skip for Now' button, clicking...")
                                    skip_button.click()
                                    time.sleep(5)  # Wait longer for page to load after skip
                                    skip_clicked = True
                                    break
                            except NoSuchElementException:
                                continue
                    except Exception as e:
                        pass  # Continue checking for login success
                
                # Look for dashboard elements that indicate successful login
                try:
                    # Check for dashboard indicators (more flexible)
                    dashboard_indicators = [
                        # Look for user name or company info
                        "//*[contains(text(), 'Good evening')]",
                        "//*[contains(text(), 'XL Industries')]",
                        "//*[contains(text(), '301469')]",
                        # Look for main navigation
                        "//*[contains(text(), 'HR & Payroll')]",
                        "//*[contains(text(), 'Employees')]",
                        # Look for dashboard widgets
                        "//*[contains(text(), 'Time off')]",
                        "//*[contains(text(), 'Pay')]",
                        "//*[contains(text(), 'Time')]",
                        # Look for Clock In/Out buttons (case insensitive)
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                        "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                        "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]"
                    ]
                    
                    for indicator in dashboard_indicators:
                        try:
                            element = self.driver.find_element(By.XPATH, indicator)
                            if element.is_displayed():
                                self.logger.info(f"✅ Login successful! Found dashboard element: {indicator}")
                                return True
                        except NoSuchElementException:
                            continue
                    
                    # Also check if URL changed to dashboard
                    current_url = self.driver.current_url
                    if "go.paylocity.com" in current_url and ("home" in current_url or "dashboard" in current_url):
                        self.logger.info(f"✅ Login successful! URL indicates dashboard: {current_url}")
                        return True
                    
                    self.logger.info(f"⏳ Waiting for dashboard to load... ({elapsed}s)")
                        
                except Exception as e:
                    self.logger.info(f"⏳ Checking for dashboard elements... ({elapsed}s)")
                    
            self.logger.warning(f"⚠️ Waited {max_wait}s but couldn't confirm login")
            return False

        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False

    def handle_skip_for_now(self):
        """Handle the 'Skip for Now' button if it appears"""
        try:
            self.logger.info("🔄 Looking for 'Skip for Now' button...")
            
            skip_button_selectors = [
                "//button[contains(text(), 'Skip for Now')]",
                "//a[contains(text(), 'Skip for Now')]",
                "//input[@value='Skip for Now']",
                "//button[contains(@class, 'skip')]",
                "//a[contains(@class, 'skip')]"
            ]
            
            for selector in skip_button_selectors:
                try:
                    skip_button = self.driver.find_element(By.XPATH, selector)
                    if skip_button.is_displayed():
                        self.logger.info(f"✅ Found 'Skip for Now' button, clicking...")
                        skip_button.click()
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
                    
            self.logger.info("ℹ️ No 'Skip for Now' button found")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error handling 'Skip for Now': {e}")
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
            
            # Look for clock in button (case insensitive)
            clock_in_selectors = [
                # Exact button class found from inspection
                "//button[contains(@class, 'button_button__xfI5Z') and .//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Look for button containing span with class button_text__kMv0x AND clock in text
                "//button[.//span[@class='button_text__kMv0x' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Look for button containing span with "clock in" text (most specific)
                "//button[.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Traditional selectors
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//button[contains(@class, 'clock-in')]",
                "//button[contains(@id, 'clock-in')]"
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

    def locate_clock_out_button(self):
        """Locate the Clock out button without clicking it"""
        try:
            self.logger.info("🕐 Looking for Clock out button...")
            
            # Look for clock out button
            clock_out_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//button[text()='clock out']",
                "//button[contains(text(), 'Clock out')]",
                "//button[contains(text(), 'clock out')]",
                "//button[contains(@class, 'clock-out')]",
                "//input[@value='Clock out']",
                "//button[contains(@id, 'clock-out')]"
            ]
            
            for selector in clock_out_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found Clock out button: {selector}")
                        self.logger.info(f"   Button text: '{button.text}'")
                        self.logger.info(f"   Button enabled: {button.is_enabled()}")
                        self.logger.info(f"   Button displayed: {button.is_displayed()}")
                        return True
                        
                except NoSuchElementException:
                    continue
            
            # If no Clock out button found, check what buttons are actually available
            self.logger.info("🔍 No Clock out button found. Checking available time-related buttons...")
            available_buttons = []
            
            # Look for common time-related buttons
            time_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'end lunch')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'lunch')]"
            ]
            
            for selector in time_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed():
                            available_buttons.append(f"'{button.text}' (enabled: {button.is_enabled()})")
                except:
                    continue
            
            if available_buttons:
                self.logger.info(f"📋 Available time-related buttons: {', '.join(available_buttons)}")
            else:
                self.logger.info("📋 No time-related buttons found on current page")
                    
            self.logger.warning("⚠️ Clock out button not found - user may not be clocked in")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Locate clock out button failed: {e}")
            return False

    def clock_out(self):
        """Clock out action"""
        try:
            self.logger.info("🕕 Attempting to clock out...")
            
            # Look for clock out button (case insensitive)
            clock_out_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//button[text()='clock out']",
                "//button[contains(text(), 'Clock out')]",
                "//button[contains(text(), 'clock out')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//button[contains(@class, 'clock-out')]",
                "//button[contains(@id, 'clock-out')]"
            ]
            
            for selector in clock_out_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info(f"✅ Found Clock Out button: {selector}")
                        button.click()
                        time.sleep(2)
                        self.logger.info("✅ Clocked out!")
                        return True
                        
                except NoSuchElementException:
                    continue
                    
            self.logger.warning("⚠️ Clock out button not found or not available")
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
                
            # Look for lunch start button (mirror robustness of Clock In)
            lunch_start_selectors = [
                # Specific button structure with nested span (case-insensitive)
                "//button[contains(@class, 'button_button__xfI5Z') and .//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]]",
                # Span with known text class and case-insensitive match
                "//button[.//span[@class='button_text__kMv0x' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]]",
                # Any button containing a span with 'start lunch'
                "//button[.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]]",
                # Case-insensitive traditional selectors for 'start lunch'
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]",
                # Alternative label some UIs use: 'Lunch Out' (case-insensitive)
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'lunch out')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'lunch out')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'lunch out')]",
                # Fallbacks by class/id
                "//button[contains(@class, 'lunch-start')]",
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

    def locate_lunch_end_button(self):
        """Locate the End Lunch button without clicking it"""
        try:
            self.logger.info("🍽️ Looking for End Lunch button...")
            
            # Look for lunch end button
            lunch_end_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'end lunch')]",
                "//button[contains(text(), 'End Lunch')]",
                "//button[contains(text(), 'end lunch')]",
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
                        self.logger.info(f"   Button text: '{button.text}'")
                        self.logger.info(f"   Button enabled: {button.is_enabled()}")
                        self.logger.info(f"   Button displayed: {button.is_displayed()}")
                        return True
                        
                except NoSuchElementException:
                    continue
            
            # If no End Lunch button found, check what buttons are actually available
            self.logger.info("🔍 No End Lunch button found. Checking available time-related buttons...")
            available_buttons = []
            
            # Look for common time-related buttons
            time_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock out')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start lunch')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'end lunch')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'lunch')]"
            ]
            
            for selector in time_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed():
                            available_buttons.append(f"'{button.text}' (enabled: {button.is_enabled()})")
                except:
                    continue
            
            if available_buttons:
                self.logger.info(f"📋 Available time-related buttons: {', '.join(available_buttons)}")
            else:
                self.logger.info("📋 No time-related buttons found on current page")
                    
            self.logger.warning("⚠️ End Lunch button not found - user may not be currently on lunch")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Locate lunch end button failed: {e}")
            return False

    def end_lunch(self):
        """End lunch break"""
        try:
            self.logger.info("🍽️ Attempting to end lunch...")
            
            if not self.find_time_entry_page():
                return False
                
            # Look for lunch end button
            lunch_end_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'end lunch')]",
                "//button[contains(text(), 'End Lunch')]",
                "//button[contains(text(), 'end lunch')]",
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
            
            # Skip navigation - we're already on the dashboard with status info
            # if not self.find_time_entry_page():
            #     return None
                
            # Look for status indicators on the dashboard
            status_selectors = [
                "//*[contains(text(), 'clocked in')]",
                "//*[contains(text(), 'clocked out')]", 
                "//*[contains(text(), 'Clocked In')]",
                "//*[contains(text(), 'Clocked Out')]",
                "//*[contains(text(), '→ Clocked in')]",
                "//*[contains(text(), '→ Clocked out')]",
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
