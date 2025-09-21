import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import difflib
import time
import re

# Try to import Selenium, fallback gracefully if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Selenium import failed: {e}")
    st.info("""
    **Deployment Issue Detected:** 
    
    If you're seeing this on Streamlit Cloud:
    1. Check that `packages.txt` contains: `chromium-browser` and `chromium-chromedriver`
    2. Check that `requirements.txt` contains: `selenium` and `webdriver-manager`
    3. Try redeploying the app
    4. The app will use fallback mode with limited functionality
    """)
    SELENIUM_AVAILABLE = False

st.set_page_config(page_title="CeX Price Checker", page_icon="💷", layout="centered")

# Version 2.1 - Enhanced debugging and Firefox support
st.title("💷 CeX Sell Price Checker")

# Show status based on Selenium availability
if SELENIUM_AVAILABLE:
    st.success("✅ **Full Mode** - Selenium enabled for complete functionality")
    st.info("🐈 Browser will be downloaded automatically on first run (may take 1-2 minutes)")
else:
    st.warning("⚠️ **Limited Mode** - Using fallback method (some features may not work)")
    st.info("🔧 Sample CSV download still works. For full functionality, check deployment logs.")

st.markdown(
    """
    Welcome to the **CeX Price Checker**! This tool helps you get the latest "We Sell For" prices 
    from CeX (UK) for your products. Simply upload a CSV file with product names and get instant pricing data.
    
    🔍 **How it works:**
    1. Download the sample CSV template below
    2. Replace the sample products with your own
    3. Upload the CSV file
    4. Get instant pricing results with product matches!
    """
)

# Sample CSV download section
st.markdown("### 📥 Download Sample CSV")
st.write("Need a template? Download this sample CSV file to get started:")

# Create sample data
sample_data = pd.DataFrame({
    "Product Name": [
        "iPhone 14 128GB",
        "PlayStation 5 Console",
        "Nintendo Switch OLED",
        "MacBook Air M2",
        "iPad Pro 11-inch",
        "Samsung Galaxy S23",
        "AirPods Pro 2nd Gen",
        "Xbox Series X"
    ]
})

# Convert to CSV bytes
sample_csv = sample_data.to_csv(index=False).encode('utf-8')

# Show preview of sample data
with st.expander("👁️ Preview Sample CSV Content"):
    st.dataframe(sample_data, width='stretch')
    st.caption("This is what the sample CSV contains. You can replace these with your own products.")

# Download button for sample CSV
st.download_button(
    label="📄 Download Sample CSV Template",
    data=sample_csv,
    file_name="cex_price_checker_template.csv",
    mime="text/csv",
    help="Download this template CSV file, add your products, then upload it back to get prices!"
)

st.markdown("---")

# Tips section
with st.expander("💡 Tips for Better Results"):
    st.markdown(
        """
        **To get the best price matches:**
        - Be specific with product names (e.g., "iPhone 14 128GB Blue" vs "iPhone")
        - Include key details like storage size, color, condition when known
        - Use official product names when possible
        - The tool will find the best match based on similarity to your search terms
        
        **Examples of good product names:**
        - ✅ "PlayStation 5 Console White"
        - ✅ "Apple MacBook Air M2 13-inch 256GB"
        - ✅ "Samsung Galaxy S23 Ultra 256GB"
        - ❌ "PS5" (too vague)
        - ❌ "Laptop" (too generic)
        """
    )

# File upload section
st.markdown("### 📤 Upload Your CSV")
uploaded_file = st.file_uploader(
    "Choose your CSV file with product names", 
    type=["csv"],
    help="Your CSV should have a 'Product Name' column with the products you want to price check."
)

@st.cache_data(ttl=300)  # Cache results for 5 minutes
def fetch_cex_price(product_name):
    """Search CeX and return the best matched product and its sell price."""
    if not product_name or not product_name.strip():
        return None, None, None
    
    # Try Selenium first if available, fallback to requests method
    if SELENIUM_AVAILABLE:
        return fetch_cex_price_selenium(product_name)
    else:
        return fetch_cex_price_fallback(product_name)

def fetch_cex_price_selenium(product_name):
    """Search CeX using Selenium (preferred method)."""
    if not product_name or not product_name.strip():
        return None, None, None
    
    driver = None
    try:
        # Setup Chrome options for headless browsing (Streamlit Cloud compatible)
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Configure browser binaries for Streamlit Cloud
        import os
        
        # Debug: Show available binaries
        available_binaries = []
        possible_paths = [
            '/usr/bin/chromium', '/usr/bin/chromium-browser',
            '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
            '/usr/bin/firefox', '/usr/bin/firefox-esr'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                available_binaries.append(path)
        
        if available_binaries:
            st.info(f"🔍 Found browsers: {', '.join(available_binaries)}")
        else:
            st.warning("⚠️ No browser binaries found in standard locations")
        
        # Try Chrome first with explicit binary paths
        try:
            # Set Chrome binary location explicitly
            chrome_binary_paths = [
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable'
            ]
            
            chrome_binary = None
            for path in chrome_binary_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break
            
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
                # Use ChromeDriverManager with automatic browser version detection
                try:
                    # Force fresh ChromeDriver download that matches Chrome version
                    import shutil
                    from pathlib import Path
                    
                    # Clear webdriver-manager cache for Chrome
                    cache_dir = Path.home() / '.wdm' / 'drivers' / 'chromedriver'
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir, ignore_errors=True)
                        st.info("🔄 Cleared ChromeDriver cache to get compatible version")
                    
                    # Install ChromeDriver (compatible API)
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    st.success("✅ Chrome initialized successfully")
                    
                except Exception as chrome_version_error:
                    st.warning(f"Chrome version compatibility issue: {str(chrome_version_error)[:200]}...")
                    raise chrome_version_error
            else:
                raise Exception("No Chrome binary found")
                
        except Exception as chrome_error:
            st.warning(f"Chrome failed ({chrome_error}), trying Firefox...")
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                from webdriver_manager.firefox import GeckoDriverManager
                
                # Set Firefox binary location explicitly
                firefox_binary_paths = [
                    '/usr/bin/firefox',
                    '/usr/bin/firefox-esr'
                ]
                
                firefox_binary = None
                for path in firefox_binary_paths:
                    if os.path.exists(path):
                        firefox_binary = path
                        break
                
                if not firefox_binary:
                    raise Exception("No Firefox binary found")
                
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                firefox_options.add_argument('--no-sandbox')
                firefox_options.add_argument('--disable-dev-shm-usage')
                firefox_options.add_argument('--disable-gpu')
                firefox_options.add_argument('--window-size=1920,1080')
                firefox_options.add_argument('--disable-blink-features=AutomationControlled')
                firefox_options.set_preference('general.useragent.override', 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0')
                firefox_options.set_preference('dom.webdriver.enabled', False)
                firefox_options.binary_location = firefox_binary
                
                st.info(f"🦊 Using Firefox: {firefox_binary}")
                service = Service(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=firefox_options)
                st.success("✅ Firefox initialized successfully!")
                
            except Exception as firefox_error:
                st.error(f"Both Chrome and Firefox failed: {chrome_error}, {firefox_error}")
                raise firefox_error
        driver.set_page_load_timeout(15)  # Set timeout
        
        # Simplify search term for better matching
        search_term = product_name.strip()
        # Remove detailed descriptors for initial search
        search_term = re.sub(r'\s*[,w]\/.*$', '', search_term)
        st.info(f"🔍 Simplified search term: '{search_term}'")
        
        search_url = f"https://uk.webuy.com/search?stext={requests.utils.quote(search_term)}"
        st.info(f"🌐 Searching URL: {search_url}")
        
        try:
            driver.get(search_url)
            
            # Wait for dynamic content with WebDriverWait
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # First wait for page load
            wait = WebDriverWait(driver, 10)
            
            # Try different indicators that the page has loaded
            indicators_to_try = [
                (By.CSS_SELECTOR, 'a[href*="product"]'),
                (By.CSS_SELECTOR, 'div[class*="product"]'),
                (By.CSS_SELECTOR, 'div[class*="search"]'),
                (By.CSS_SELECTOR, 'div[class*="result"]')
            ]
            
            for locator in indicators_to_try:
                try:
                    element = wait.until(EC.presence_of_element_located(locator))
                    st.success(f"✅ Content loaded (found {locator[1]})")
                    break
                except:
                    continue
            
            # Get updated page source after JavaScript execution
            time.sleep(2)  # Short final wait for any remaining updates
            page_source = driver.page_source
            st.info(f"📝 Page content length: {len(page_source)} bytes")
            
        except Exception as nav_error:
            st.error(f"Navigation error: {str(nav_error)}")
            page_source = driver.page_source
                st.warning("⚠️ Content may not have fully loaded")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Verify page loaded correctly
        page_title = soup.find('title')
        if page_title:
            st.info(f"📜 Page loaded: {page_title.get_text().strip()}")
        
        # Check for CeX-specific indicators
        if 'cex' in page_source.lower() or 'webuy' in page_source.lower():
            st.success("✅ CeX website detected in page content")
        else:
            st.warning("⚠️ CeX website indicators not found - may be blocked or loading issue")
        
        # Debug: Show some page structure
        all_links = soup.find_all('a', href=True)
        st.info(f"🔗 Total links on page: {len(all_links)}")
        
        # Look for any href patterns that might be products
        href_patterns = {}
        for link in all_links[:50]:  # Check first 50 links
            href = link.get('href', '')
            if href.startswith('/'):
                path_parts = href.split('/')[1:3]  # Get first two path segments
                pattern = '/'.join(path_parts) if len(path_parts) > 1 else path_parts[0] if path_parts else 'root'
                href_patterns[pattern] = href_patterns.get(pattern, 0) + 1
        
        if href_patterns:
            st.info(f"🔍 Common URL patterns found: {dict(list(href_patterns.items())[:10])}")
        
        # Strategy A: Find product links and their associated prices
        product_links = soup.select('a[href*="/product-detail"]')
        
        # Strategy B: Try to parse embedded JSON in script tags (Nuxt/Vue often embeds data)
        if not product_links:
            scripts = soup.find_all('script')
            import json
            for sc in scripts:
                text = sc.get_text(strip=True)
                if not text or len(text) < 100:
                    continue
                # Look for likely JSON blocks containing product data
                if 'product' in text.lower() or 'items' in text.lower() or 'results' in text.lower():
                    try:
                        # Try to extract JSON object
                        start = text.find('{')
                        end = text.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            obj = json.loads(text[start:end+1])
                            # Heuristic: look for arrays that could be results
                            candidates = []
                            def walk(o):
                                if isinstance(o, dict):
                                    for k,v in o.items():
                                        if isinstance(v, (list,dict)):
                                            walk(v)
                                elif isinstance(o, list):
                                    # look for dict-like list with title/price/url fields
                                    if len(o) > 0 and isinstance(o[0], dict) and any('price' in (k.lower()) for k in o[0].keys()):
                                        candidates.append(o)
                                    else:
                                        for item in o:
                                            walk(item)
                            walk(obj)
                            if candidates:
                                st.info(f"🧩 Extracted {sum(len(c) for c in candidates)} items from embedded JSON")
                                # Convert to synthetic product_links-like structures
                                product_links = []
                                for arr in candidates:
                                    for it in arr:
                                        title = it.get('title') or it.get('name') or ''
                                        url = it.get('url') or it.get('href') or ''
                                        price = it.get('price') or it.get('sellPrice') or it.get('weSellFor')
                                        if title and url:
                                            # Create a minimal soup-like object wrapper
                                            from bs4 import Tag
                                            a = soup.new_tag('a', href=url)
                                            a.string = title
                                            # attach a nearby price wrapper we can find later
                                            if price:
                                                p = soup.new_tag('p', **{'class':'product-main-price'})
                                                p.string = f"£{price}"
                                                wrapper = soup.new_tag('div')
                                                wrapper.append(a)
                                                wrapper.append(p)
                                                product_links.append(a)
                                            else:
                                                product_links.append(a)
                                if product_links:
                                    break
                    except Exception:
                        continue
        
        
        # Debug information
        st.info(f"🔍 Search for '{product_name}': Found {len(product_links)} product links")
        
        # Also check for alternative link patterns if main pattern fails
        if not product_links:
            # Try multiple patterns to find the actual link structure
            patterns_to_try = [
                'a[href*="product"]',
                'a[href*="buy"]', 
                'a[href*="sell"]',
                'a[href*="item"]',
                'a[href*="detail"]',
                'a[class*="product"]',
                'a[class*="item"]'
            ]
            
            for pattern in patterns_to_try:
                alt_links = soup.select(pattern)
                if alt_links:
                    st.info(f"🔍 Pattern '{pattern}' found {len(alt_links)} links")
                    # Show first few links for debugging
                    sample_links = [link.get('href', '') for link in alt_links[:3]]
                    st.info(f"🔍 Sample links: {sample_links}")
                    
                    # Use the first working pattern
                    product_links = alt_links
                    break
        
        if not product_links:
            # Strategy C: Try clicking the first product card or category and re-parse
            try:
                st.info("🧭 Trying to open first result group and re-parse")
                from selenium.webdriver.common.by import By
                cards = driver.find_elements(By.CSS_SELECTOR, 'a, div')
                clicked = False
                for el in cards[:50]:
                    try:
                        text = el.text.strip().lower()
                        if any(k in text for k in ['results', 'iphone', 'product', 'category']):
                            el.click()
                            time.sleep(3)
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                            product_links = soup.select('a[href*="/product-detail"]')
                            if product_links:
                                st.success("✅ Found product links after navigation")
                                break
                    except Exception:
                        continue
            except Exception:
                pass
        
        if not product_links:
            st.warning(f"⚠️ No product links found for '{product_name}'. Site structure may have changed.")
            return None, None, None
        
        best_match = None
        best_price = None
        best_url = None
        highest_ratio = 0
        
        for link in product_links:
            try:
                # Get product title
                title = link.get_text(strip=True)
                if not title or len(title) < 3:  # Skip very short titles
                    continue
                    
                # Get the full URL
                href = link.get("href")
                if not href:
                    continue
                url = "https://uk.webuy.com" + href if href.startswith('/') else href
                
                # Find the price - look for nearest price element
                # Price should be in the same parent container
                parent_container = link.parent
                max_levels = 5  # Limit search levels
                current_level = 0
                
                while parent_container and parent_container.name != 'body' and current_level < max_levels:
                    price_elem = parent_container.select_one('p.product-main-price')
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        # Clean the price text and validate
                        price_clean = re.sub(r'[^\d.]', '', price_text)
                        
                        # Validate price format
                        try:
                            price_value = float(price_clean)
                            if price_value > 0:
                                # Similarity check to pick best match
                                ratio = difflib.SequenceMatcher(None, product_name.lower(), title.lower()).ratio()
                                if ratio > highest_ratio:
                                    highest_ratio = ratio
                                    best_match = title
                                    best_price = price_clean
                                    best_url = url
                        except ValueError:
                            pass  # Invalid price, skip
                        break
                    parent_container = parent_container.parent
                    current_level += 1
            except Exception as link_error:
                # Log individual link errors but continue processing
                continue
                
        # Only return results if we have a reasonable match (>= 30% similarity)
        if highest_ratio >= 0.3:
            return best_match, best_price, best_url
        else:
            return None, None, None
        
    except Exception as e:
        st.error(f"Error fetching price for '{product_name}': {str(e)}")
        return None, None, None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass  # Ignore cleanup errors

def fetch_cex_price_fallback(product_name):
    """Fallback method using requests when Selenium is not available."""
    try:
        st.warning("Using fallback mode - limited functionality. Some prices may not be available.")
        
        # Try simple requests approach (limited success due to JavaScript)
        search_url = f"https://uk.webuy.com/search?stext={requests.utils.quote(product_name.strip())}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for any price patterns in the HTML
            price_pattern = r'£[\d,]+(?:\.\d{2})?'
            prices = re.findall(price_pattern, response.text)
            
            if prices:
                # Return a basic result indicating fallback mode
                return f"Search results found (fallback mode)", prices[0].replace('£', ''), search_url
            else:
                return f"No prices found in fallback mode", None, search_url
        else:
            return None, None, None
            
    except Exception as e:
        st.error(f"Fallback method also failed: {str(e)}")
        return None, None, None


if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Product Name" not in df.columns:
        st.error("CSV must contain a 'Product Name' column.")
    else:
        enriched = []
        product_names = df["Product Name"].tolist()
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, name in enumerate(product_names):
            # Update progress
            progress = (i + 1) / len(product_names)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{len(product_names)}: {name}")
            
            match, price, url = fetch_cex_price(name)
            enriched.append({
                "Product Name": name,
                "CeX Matched Product": match,
                "CeX Sell Price (GBP)": price,
                "CeX URL": url,
                "Scraped At (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        enriched_df = pd.DataFrame(enriched)
        result = pd.concat([df, enriched_df.drop("Product Name", axis=1)], axis=1)

        # Calculate statistics
        total_products = len(result)
        found_matches = len([x for x in enriched if x['CeX Matched Product'] is not None])
        total_value = sum([float(x['CeX Sell Price (GBP)']) for x in enriched if x['CeX Sell Price (GBP)'] is not None])
        
        st.success("✅ Processing complete!")
        
        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Products", total_products)
        with col2:
            st.metric("Matches Found", f"{found_matches}/{total_products}")
        with col3:
            st.metric("Success Rate", f"{(found_matches/total_products)*100:.1f}%")
        with col4:
            st.metric("Total Value", f"£{total_value:.2f}")
        
        st.markdown("### 📊 Results")
        st.dataframe(result, width='stretch')

        # Download enriched CSV
        st.markdown("### 📥 Download Results")
        
        csv_bytes = result.to_csv(index=False).encode("utf-8")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Complete Results (CSV)",
                data=csv_bytes,
                file_name=f"cex_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download your results with CeX pricing data"
            )
        
        with col2:
            # Create a filtered version with only successful matches
            successful_results = result[result['CeX Matched Product'].notna()]
            if len(successful_results) > 0:
                successful_csv = successful_results.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="✨ Download Matches Only (CSV)",
                    data=successful_csv,
                    file_name=f"cex_matches_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download only products that had successful matches"
                )

# --- PayPal Donate Button ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <a href="https://www.paypal.com/donate?business=jonathan@blench.me.uk&currency_code=GBP" target="_blank">
            <img src="https://www.paypalobjects.com/en_GB/i/btn/btn_donateCC_LG.gif" border="0" alt="Donate with PayPal button" />
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
