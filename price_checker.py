import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import difflib

st.set_page_config(page_title="CeX Price Checker", page_icon="💷", layout="centered")

st.title("💷 CeX Sell Price Checker")

st.write("Upload a CSV of product names, and I'll fetch the latest **CeX We Sell For** prices.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

def fetch_cex_price(product_name):
    """Search CeX and return the best matched product and its sell price."""
    search_url = f"https://uk.webuy.com/search?stext={requests.utils.quote(product_name)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(search_url, headers=headers)
    if resp.status_code != 200:
        return None, None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.select("div.productSearch div.row")

    best_match = None
    best_price = None
    best_url = None
    highest_ratio = 0

    for r in results:
        title_tag = r.select_one("a.prodLink")
        price_tag = r.select_one("div.text-red strong")
        if not title_tag or not price_tag:
            continue

        title = title_tag.get_text(strip=True)
        url = "https://uk.webuy.com" + title_tag.get("href")

        # Similarity check to pick best match
        ratio = difflib.SequenceMatcher(None, product_name.lower(), title.lower()).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = title
            best_price = price_tag.get_text(strip=True).replace("£", "")
            best_url = url

    return best_match, best_price, best_url


if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Product Name" not in df.columns:
        st.error("CSV must contain a 'Product Name' column.")
    else:
        enriched = []
        for name in df["Product Name"]:
            match, price, url = fetch_cex_price(name)
            enriched.append({
                "Product Name": name,
                "CeX Matched Product": match,
                "CeX Sell Price (GBP)": price,
                "CeX URL": url,
                "Scraped At (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })

        enriched_df = pd.DataFrame(enriched)
        result = pd.concat([df, enriched_df.drop("Product Name", axis=1)], axis=1)

        st.success("✅ Processing complete!")
        st.dataframe(result)

        # Download enriched CSV
        csv_bytes = result.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Enriched CSV",
            data=csv_bytes,
            file_name="products_with_cex_prices.csv",
            mime="text/csv"
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
