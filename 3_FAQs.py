import streamlit as st

st.set_page_config(page_title="Quantexo FAQs", layout="wide")

st.title("❓ Frequently Asked Questions")

with st.expander("🔍 General Questions"):
    st.markdown("""
    **Q: Why don't I see any signals for my stock?**  
    A: This typically means no strong patterns were detected in the recent price action according to our algorithms.
    
    **Q: How often is the data updated?**  
    A: End-of-day data is updated daily by 8:00 PM NPT.
    """)

with st.expander("📈 Technical Questions"):
    st.markdown("""
    **Q: What's the difference between 🟢 and 🐂 signals?**  
    A: 🟢 indicates aggressive buying with strong volume, while 🐂 shows particularly large bullish candles (>70% range).
    
    **Q: Why do some signals disappear when I zoom?**  
    A: This is normal chart behavior - signals remain but may be hidden at certain zoom levels.
    """)

with st.expander("💾 Data Questions"):
    st.markdown("""
    **Q: Where does the data come from?**  
    A: Our Google Sheets aggregation of NEPSE market data.
    
    **Q: How can I get historical data?**  
    A: Currently we provide 1 year of historical data.
    """)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)