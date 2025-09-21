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

st.title("💷 CeX Sell Price Checker")

# Show status based on Selenium availability
if SELENIUM_AVAILABLE:
    st.success("✅ **Full Mode** - Selenium enabled for complete functionality")
else:
    st.warning("⚠️ **Limited Mode** - Using fallback method (some features may not work)")

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
        
        # Try to use system chromium first (for Streamlit Cloud), fallback to ChromeDriverManager
        try:
            # For Streamlit Cloud - use system chromium
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            # Fallback for local development
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)  # Set timeout
        
        search_url = f"https://uk.webuy.com/search?stext={requests.utils.quote(product_name.strip())}"
        driver.get(search_url)
        
        # Wait for JavaScript content to load with exponential backoff
        for attempt in range(3):
            time.sleep(2 + attempt)  # 2, 3, 4 seconds
            page_source = driver.page_source
            if 'product-detail' in page_source:
                break
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find product links and their associated prices
        product_links = soup.select('a[href*="/product-detail"]')
        
        if not product_links:
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
