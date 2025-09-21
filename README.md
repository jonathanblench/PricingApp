# CeX Price Checker 💷

A Streamlit web application that fetches the latest "We Sell For" prices from CeX (UK) for your products.

## 🚨 Recent Updates

**Fixed JavaScript Loading Issue**: The original code wasn't working because the CeX website now uses modern JavaScript (Nuxt.js) to load content dynamically. This has been fixed by implementing Selenium with Chrome WebDriver to wait for JavaScript content to load.

## 🌟 Features

- **Sample CSV Download**: Download a template CSV with example products
- **Batch Processing**: Upload a CSV with multiple products for bulk price checking
- **Progress Tracking**: Real-time progress bar during processing  
- **Smart Matching**: Uses similarity scoring to find the best product matches
- **Results Statistics**: View success rates and total values
- **Multiple Download Options**: Download complete results or matches only
- **Caching**: Results are cached for 5 minutes to improve performance

## 📋 Requirements

- Python 3.9+
- Chrome browser (installed automatically via webdriver-manager)
- Required packages (install with pip):
  ```bash
  pip install streamlit pandas requests beautifulsoup4 selenium webdriver-manager
  ```

## 🚀 Usage

1. **Start the application**:
   ```bash
   streamlit run price_checker.py
   ```

2. **Download the sample CSV template** to see the expected format

3. **Edit the CSV** with your own products:
   - Replace sample products with your own
   - Be specific with product names for better matches
   - Include details like storage size, color, condition

4. **Upload your CSV** and wait for processing

5. **Download results** in your preferred format

## 💡 Tips for Better Results

**Good product names:**
- ✅ "PlayStation 5 Console White"  
- ✅ "Apple MacBook Air M2 13-inch 256GB"
- ✅ "Samsung Galaxy S23 Ultra 256GB"

**Avoid vague names:**
- ❌ "PS5" (too vague)
- ❌ "Laptop" (too generic)

## 🔧 Technical Details

### How it works:
1. Uses Selenium WebDriver to load CeX search pages
2. Waits for JavaScript content to fully render
3. Extracts product titles and prices using BeautifulSoup
4. Matches products using difflib similarity scoring
5. Returns best matches with ≥30% similarity threshold

### Performance optimizations:
- Headless Chrome browser for faster processing
- Disabled images and plugins to speed up page loads  
- Exponential backoff for content loading
- Results caching to avoid repeat requests
- Browser cleanup on completion/error

## 📊 Output Format

The results CSV includes:
- **Product Name**: Your original search term
- **CeX Matched Product**: Best matching product found
- **CeX Sell Price (GBP)**: Current selling price 
- **CeX URL**: Direct link to the product page
- **Scraped At (UTC)**: Timestamp of when data was fetched

## 🛠️ Troubleshooting

- **No matches found**: Try more specific product names
- **Slow processing**: Each product takes 3-5 seconds due to JavaScript loading
- **Browser errors**: Chrome will be installed automatically via webdriver-manager

## 📄 Sample Products Included

The template includes these sample products:
- iPhone 14 128GB
- PlayStation 5 Console  
- Nintendo Switch OLED
- MacBook Air M2
- iPad Pro 11-inch
- Samsung Galaxy S23
- AirPods Pro 2nd Gen
- Xbox Series X

## ⚖️ Legal & Usage

- For personal/educational use only
- Respects CeX website structure and load times
- No aggressive scraping - includes delays between requests
- Use responsibly and in accordance with CeX terms of service