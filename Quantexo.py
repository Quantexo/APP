import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import pytz
import kaleido
import plotly.io as pio

# --- Page Setup ---

st.set_page_config(page_title="Quantexo", layout="wide")

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """ <style>
    .stApp {
    background-color: darkslategray;
    } </style> <div class='header-container'> <div class='header-title'>Quantexo🕵️</div> <div class='header-subtitle'>💰 Advanced Insights for Bold Trades</div> </div>
    """,
    unsafe_allow_html=True
)
# Add this near your signal detection logic or in a separate help section
SIGNAL_DOCS = {
    "🟢": {
        "name": "Aggressive Buying",
        "description": "Strong bullish candle closing near high with high volume, indicating buyer dominance",
        "interpretation": "Potential start of an uptrend or continuation pattern"
    },
    "🔴": {
        "name": "Aggressive Selling",
        "description": "Strong bearish candle closing near low with high volume, indicating seller dominance",
        "interpretation": "Potential start of a downtrend or continuation pattern"
    },
    "⛔": {
        "name": "Buyer Absorption",
        "description": "Bullish candle followed by price failing to drop below its open",
        "interpretation": "Buyers absorbing all selling pressure - potential reversal signal"
    },
    "🚀": {
        "name": "Seller Absorption",
        "description": "Bearish candle followed by price failing to rise above its open",
        "interpretation": "Sellers absorbing all buying pressure - potential reversal signal"
    },
    "💥": {
        "name": "Bullish Pivot Point Breakout",
        "description": "Price breaks above recent high with strong volume",
        "interpretation": "Potential start of new uptrend or breakout continuation"
    },
    "💣": {
        "name": "Bearish Pivot Point Breakdown",
        "description": "Price breaks below recent low with strong volume",
        "interpretation": "Potential start of new downtrend or breakdown continuation"
    },
    "🐂": {
        "name": "Bullish Point of Interest",
        "description": "Large bullish candle occupying >70% of range with high volume",
        "interpretation": "Strong buying interest at this price level"
    },
    "🐻": {
        "name": "Bearish Point of Interest",
        "description": "Large bearish candle occupying >70% of range with high volume",
        "interpretation": "Strong selling interest at this price level"
    }
}

# Add this section near the top of your code, after imports but before main logic
def show_help_section():
    """Displays the comprehensive help documentation in an expandable section"""
    with st.expander("📚 Quantexo Help Documentation", expanded=False):
        st.markdown("""
        ## 📊 Signal Reference Guide
        """)
        
        # Display signal documentation in a clean table format
        cols = st.columns([0.5, 1, 2, 2])
        with cols[0]: st.markdown("**Symbol**")
        with cols[1]: st.markdown("**Name**")
        with cols[2]: st.markdown("**Description**")
        with cols[3]: st.markdown("**Interpretation**")
        
        for symbol, info in SIGNAL_DOCS.items():
            cols = st.columns([0.5, 1, 2, 2])
            with cols[0]: st.markdown(f"<h3>{symbol}</h3>", unsafe_allow_html=True)
            with cols[1]: st.markdown(info["name"])
            with cols[2]: st.markdown(info["description"])
            with cols[3]: st.markdown(info["interpretation"])
            st.divider()
        
        st.markdown("""
        ---
        ## 🖥️ How to Use
        
        ### Basic Usage:
        1. **Select Sector** from dropdown (optional)
        2. **Choose Company** or enter symbol manually
        3. **View** automatically detected signals
        4. **Hover** over signals for detailed information
        
        ### Advanced Features:
        - **Scan All**: Analyze all companies at once
        - **Download**: Export results as CSV
        - **Interactive Chart**: Zoom/pan with mouse
        
        ---
        ## 🔢 Technical Indicators Used
        
        - **Volume Analysis**: 2x average volume threshold
        - **Price Action**: Candle body >70% of range
        - **Breakouts**: New 10-day high/low
        - **Absorption**: Follow-through price action
        
        ---
        ## 📈 Data Information
        
        **Source**: 
        - NEPSE market data via Google Sheets API
        
        **Update Frequency**: 
        - End-of-day (EOD) updates by 8:00 PM NPT
        
        **Data Fields**:
        - Date, Open, High, Low, Close, Volume
        
        **Note**: 
        - Data is cached for 1 hour (refresh to update)
        - Historical data available for 1 year
        
        ---
        ## ⚠️ Risk Disclaimer
        
        This tool provides technical analysis only. 
        - Not financial advice
        - Past performance ≠ future results
        - Always do your own research
        - Invest at your own risk
        """)
if st.sidebar.button("📚 Open Help Documentation"):
    show_help_section()
        
# --- SECTOR TO COMPANY MAPPING ---
sector_to_companies = {
    "Commercial Banks": {"ADBL","CZBIL","EBL","GBIME","HBL","KBL","LSL","MBL","NABIL","NBL","NICA","NIMB","NMB","PCBL","PRVU","SANIMA","SBI","SBL","SCB"},
    "Development Banks": {"CORBL","EDBL","GBBL","GRDBL","JBBL","KSBBL","LBBL","MDB","MLBL","MNBBL","NABBC","SADBL","SAPDBL","SHINE","SINDU"},
    "Finance": {"BFC","CFCL","GFCL","GMFIL","GUFL","ICFC","JFL","MFIL","MPFL","NFS","PFL","PROFL","RLFL","SFCL","SIFC"},
    "Hotels": {"CGH","CITY","KDL","OHL","SHL","TRH"},
    "Hydro Power": {"AHPC", "AHL", "AKJCL", "AKPL", "API", "BARUN", "BEDC", "BHDC", "BHPL", "BGWT", "BHL", "BNHC", "BPCL", "CHCL", "CHL", "CKHL", "DHPL", "DOLTI", "DORDI", "EHPL", "GHL", "GLH", "GVL", "HDHPC", "HHL", "HPPL", "HURJA", "IHL", "JOSHI", "KKHC", "KPCL", "KBSH", "LEC", "MAKAR", "MANDU", "MBJC", "MEHL", "MEL", "MEN", "MHCL", "MHNL", "MKHC", "MKHL", "MKJC", "MMKJL", "MHL", "MCHL", "MSHL", "NGPL", "NHDL", "NHPC", "NYADI", "PPL", "PHCL", "PMHPL", "PPCL", "RADHI", "RAWA", "RHGCL", "RFPL", "RIDI", "RHPL", "RURU", "SAHAS", "SHEL", "SGHC", "SHPC", "SIKLES", "SJCL", "SMH", "SMHL", "SMJC", "SPC", "SPDL", "SPHL", "SPL", "SSHL", "TAMOR", "TPC", "TSHL", "TVCL", "UHEWA", "ULHC", "UMHL", "UMRH", "UNHPL", "UPCL", "UPPER", "USHL", "USHEC", "VLUCL"},
    "Investment": {"CHDC","CIT","ENL","HATHY","HIDCL","NIFRA","NRN"},
    "Life Insurance":{"ALICL","CLI","CREST","GMLI","HLI","ILI","LICN","NLIC","NLICL","PMLI","RNLI","SJLIC","SNLI","SRLI"},
    "Manufacturing and Processing": {"BNL","BNT","GCIL","HDL","NLO","OMPL","SARBTM","SHIVM","SONA","UNL"},
    "Microfinance": {"ACLBSL","ALBSL","ANLB","AVYAN","CBBL","CYCL","DDBL","DLBS","FMDBL","FOWAD","GBLBS","GILB","GLBSL","GMFBS","HLBSL","ILBS","JBLB","JSLBB","KMCDB","LLBS","MATRI","MERO","MLBBL","MLBS","MLBSL","MSLB","NADEP","NESDO","NICLBSL","NMBMF","NMFBS","NMLBBL","NUBL","RSDC","SAMAJ","SHLB","SKBBL","SLBBL","SLBSL","SMATA","SMB","SMFBS","SMPDA","SWBBL","SWMF","ULBSL","UNLB","USLB","VLBS","WNLB"},
    "Non Life Insurance": {"HEI","IGI","NICL","NIL","NLG","NMIC","PRIN","RBCL","SALICO","SGIC"},
    "Others": {"HRL","MKCL","NRIC","NRM","NTC","NWCL"},
    "Trading": {"BBC","STC"}
}

#---UI LAYOUT---
col1, col2, col3, col4 = st.columns([0.5,0.5,0.5,0.5])

# --- Sector Selection ---
with col1:
    selected_sector = st.selectbox("Select Sector", options=[""]+ list(sector_to_companies.keys()), label_visibility="collapsed")

# ---Filter Companies based on Sector ---
with col2:
    if selected_sector:
        filtered_companies = sorted(sector_to_companies[selected_sector])
    else:
        filtered_companies = []
    
    selected_dropdown = st.selectbox(
        "Select Company",
        options=[""] + filtered_companies,
        label_visibility="collapsed",
        key="company"
    )

# ---Manual Input---
with col3:
    user_input = st.text_input(
        "🔍 Enter Company Symbol",
        "",
        label_visibility="collapsed",
        placeholder="🔍 Enter Symbol"
    )

with col4:
    col_search, col_scan = st.columns([1,1])
    with col_search:
        search_clicked = st.button("Search")
    with col_scan:
        scan_all_clicked = st.button("Scan All")

# --- Priority: Manual Entry Overrides Dropdown ---
if search_clicked:
    if user_input.strip():
        company_symbol = user_input.strip().upper()
        st.toast(f"🔎 Analyzing {company_symbol}...", icon="⚙️")
    elif selected_dropdown:
        company_symbol = selected_dropdown
        st.toast(f"🔎 Analyzing {company_symbol}...", icon="⚙️")
    else:
        st.warning("⚠️ Please enter or select a company.")
        st.stop()
else:
    company_symbol = ""

@st.cache_data(ttl=3600)
def get_sheet_data(symbol, sheet_name="Daily Price"):
    try:
        sheet_url = f"https://docs.google.com/spreadsheets/d/1Q_En7VGGfifDmn5xuiF-t_02doPpwl4PLzxb4TBCW0Q/export?format=csv&gid=0"  # Using gid=0 for the first sheet
        df = pd.read_csv(sheet_url)
        df = df.iloc[:, :7]
        df.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        
        # Filter data based on company symbol
        df['symbol'] = df['symbol'].astype(str).str.strip().str.upper()
        return df[df['symbol'].str.upper() == symbol.upper()]
    except Exception as e:
        st.error(f"🔴 Error fetching data: {str(e)}")
        return pd.DataFrame()

def detect_signals(df):
    results = []
    df['point_change'] = df['close'].diff().fillna(0)
    df['tag'] = ''

    min_window = min(20, max(5, len(df) // 2)) 
    avg_volume = df['volume'].rolling(window=min_window).mean().fillna(method='bfill').fillna(df['volume'].mean())

    for i in range(min(3, len(df)-1), len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        next_candles = df.iloc[i + 1:min(i + 6, len(df))]
        body = abs(row['close'] - row['open'])
        prev_body = abs(prev['close'] - prev['open'])
        recent_tags = df['tag'].iloc[max(0, i - 9):i]
        
        if (
            row['close'] > row['open'] and
            row['close'] >= row['high'] - (row['high'] - row['low']) * 0.1 and
            row['volume'] > avg_volume[i] * 2 and
            body > prev_body and
            '🟢' not in recent_tags.values
        ):
            df.at[i, 'tag'] = '🟢'
        elif (
            row['open'] > row['close'] and
            row['close'] <= row['low'] + (row['high'] - row['low']) * 0.1 and
            row['volume'] > avg_volume[i] * 2 and
            body > prev_body and
            '🔴' not in recent_tags.values
        ):
            df.at[i, 'tag'] = '🔴'
        elif (
            row['close'] > row['open'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df.loc[df['tag'] == '⛔', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] < row['open']:
                    df.at[j, 'tag'] = '⛔'
                    break
        elif (
            row['open'] > row['close'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df.loc[df['tag'] == '🚀', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] > row['open']:
                    df.at[j, 'tag'] = '🚀'
                    break
        elif (
            i >= 10 and
            row['high'] > max(df['high'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df['tag'].iloc[i - 8:i] == '💥').any():
                df.at[i, 'tag'] = '💥'
        elif (
            i >= 10 and
            row['low'] < min(df['low'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df['tag'].iloc[i - 8:i] == '💣').any():
                df.at[i, 'tag'] = '💣'
        elif (
            row['close'] > row['open'] and
            body > (row['high'] - row['low']) * 0.7 and
            row['volume'] > avg_volume[i] * 2
        ):
            df.at[i, 'tag'] = '🐂'
        elif (
            row['open'] > row['close'] and
            body > (row['high'] - row['low']) * 0.7 and
            row['volume'] > avg_volume[i] * 2
        ):
            df.at[i, 'tag'] = '🐻'

        if df.at[i, 'tag']:
            results.append({
                'symbol': row['symbol'],
                'tag': df.at[i, 'tag'],
                'date': row['date'].strftime('%Y-%m-%d')
            })
    return results

if scan_all_clicked:
    st.subheader("📊 Signal Scan Results for All Companies")
    all_results = []
    sheet_name = "Daily Price"

    loading_container = st.empty()
    with loading_container.container():
        st.markdown("⏳ Preparing scan...")
        progress_bar = st.progress(0)
        status_text = st.empty()

    # Flatten all companies
    all_companies = sorted(set().union(*sector_to_companies.values()))

    progress = st.progress(0, text="🔍 Scanning...")

    for i, symbol in enumerate(all_companies):
        progress= (i+1) / len(all_companies)
        progress_bar.progress(progress)
        status_text.text(f"🔍 Scanning {symbol} ({i+1}/{len(all_companies)})")

        df = get_sheet_data(symbol, sheet_name)
        if df.empty:
            continue

        df.columns = [col.lower() for col in df.columns]
        df['symbol'] = symbol
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[^\d.]', '', regex=True), errors='coerce')
            df = df.dropna()
            df.sort_values('date', inplace=True)
            df.reset_index(drop=True, inplace=True)

            if len(df) > 10:
                df = df.tail(10).copy()  # Make a copy to avoid SettingWithCopyWarning
                df.reset_index(drop=True, inplace=True)

            if len(df) > 3:  # Need at least 3 days for some signals
                results = detect_signals(df)
                # Only keep signals from the most recent day (last row)
                if results and len(results) > 0:
                    latest_signal = max(results, key=lambda x: x['date'])
                    all_results.append(latest_signal)
        except Exception as e:
            st.warning(f"⚠️ Error processing {symbol}: {str(e)}")

    loading_container.empty()
    progress_bar.empty()
    status_text.empty()

    if all_results:
        st.toast("✅ Scan completed!", icon="✅")
        result_df = pd.DataFrame(all_results)
        result_df = result_df.sort_values(by="date", ascending=False)
        
        # Add sector information to the results
        sector_map = {}
        for sector, companies in sector_to_companies.items():
            for company in companies:
                sector_map[company] = sector
        result_df['sector'] = result_df['symbol'].map(sector_map)
        
        # Reorder columns
        result_df = result_df[['date', 'symbol', 'sector', 'tag']]
        
        # Format the date nicely
        result_df['date'] = pd.to_datetime(result_df['date']).dt.strftime('%Y-%m-%d')

        st.dataframe(result_df, use_container_width=True)

        nepali_tz = pytz.timezone('Asia/Kathmandu')
        now = datetime.now(nepali_tz)
        timestamp_str = now.strftime("%Y-%B-%d_%I-%M%p")
        file_name = f"Detected.Signal__{timestamp_str}_Quantexo🕵️_NEPSE.csv"

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name= file_name,
            mime='text/csv'
        )
    else:
        st.toast("ℹ️ No signals found", icon="ℹ️")

if company_symbol:
    sheet_name = "Daily Price"
    df = get_sheet_data(company_symbol, sheet_name)

    if df.empty:
        st.warning(f"No data found for {company_symbol}")
        st.stop()

    try:
        # Convert column names to lowercase
        df.columns = [col.lower() for col in df.columns]

        # Check required columns
        required_cols = {'date', 'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(set(df.columns)):
            st.error("❌ Missing required columns: date, open, high, low, close, volume")
            st.stop()

        # Convert and validate dates
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if df['date'].isnull().any():
            st.error("❌ Invalid date format in some rows")
            st.stop()

        # Validate numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('[^\d.]', '', regex=True),  # Remove non-numeric chars
                errors='coerce'
            )
            if df[col].isnull().any():
                bad_rows = df[df[col].isnull()][['date', col]].head()
                st.error(f"❌ Found {df[col].isnull().sum()} invalid values in {col} column. Examples:")
                st.dataframe(bad_rows)
                st.stop()

        # Remove any rows with NA values
        df = df.dropna()
        if len(df) == 0:
            st.error("❌ No valid data after cleaning")
            st.stop()

        # Sort and reset index
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Detect signals
        results = detect_signals(df)

        

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['close'],
            mode='lines', name='Close Price',
            line=dict(color='lightblue', width=2),
            customdata=df[['date', 'open', 'high', 'low', 'close', 'point_change']],
            hovertemplate=(
                "📅 Date: %{customdata[0]|%Y-%m-%d}<br>" +
                "🟢 Open: %{customdata[1]:.2f}<br>" +
                "📈 High: %{customdata[2]:.2f}<br>" +
                "📉 Low: %{customdata[3]:.2f}<br>" +
                "💰 LTP: %{customdata[4]:.2f}<br>" +
                "📊 Point Change: %{customdata[5]:.2f}<extra></extra>"
            )
        ))  

        tag_labels = {
            '🟢': '🟢 Aggressive Buyers',
            '🔴': '🔴 Aggressive Sellers',
            '⛔': '⛔ Buyer Absorption',
            '🚀': '🚀 Seller Absorption',
            '💥': '💥 Bullish POR',
            '💣': '💣 Bearish POR',
            '🐂': '🐂 Bullish POI',
            '🐻': '🐻 Bearish POI'
        }

        signals = df[df['tag'] != '']
        for tag in signals['tag'].unique():
            subset = signals[signals['tag'] == tag]
            fig.add_trace(go.Scatter(
                x=subset['date'], y=subset['close'],
                mode='markers+text',
                name=tag_labels.get(tag, tag),
                text=[tag] * len(subset),
                textposition='top center',
                textfont=dict(size=20),
                marker=dict(size=14, symbol="circle", color='white'),
                customdata=subset[['open', 'high', 'low', 'close', 'point_change']].values,
                hovertemplate=(
                    "📅 Date: %{x|%Y-%m-%d}<br>" +
                    "🟢 Open: %{customdata[0]:.2f}<br>" +
                    "📈 High: %{customdata[1]:.2f}<br>" +
                    "📉 Low: %{customdata[2]:.2f}<br>" +
                    "🔚 Close: %{customdata[3]:.2f}<br>" +
                    "📊 Point Change: %{customdata[4]:.2f}<br>" +
                    f"{tag_labels.get(tag, tag)}<extra></extra>"
                )
            ))
        
        # Calculate 15 days ahead of the last date
        last_date = df['date'].max()
        extended_date = last_date + timedelta(days=15)
        fig.update_layout(
            height=800,
            width=1800,
            plot_bgcolor="darkslategray",
            paper_bgcolor="darkslategray",
            font_color="white",
            xaxis=dict(title="Date", tickangle=-45, showgrid=False, range=[df['date'].min(), extended_date]), #extend x-axis to show space after latest date
            yaxis=dict(title="Price", showgrid=False, zeroline=True, zerolinecolor="gray", autorange=True),
            margin=dict(l=50, r=50, b=130, t=50),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,  # Adjust this value to move further down if needed
                xanchor="center",
                x=0.5,
                font=dict(size=14),
                bgcolor="rgba(0,0,0,0)"  # Optional: keeps legend background transparent)
            ),
            # Add zoom and pan capabilities
            dragmode="zoom",  # Enable box zoom
            annotations=[
                dict(
                    text=f"{company_symbol} <br> Quantexo",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor="center", yanchor="middle",
                    font=dict(size=25, color="rgba(59, 59, 59)"),
                    showarrow=False
                )
            ]
        )
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        with st.spinner("Rendering interactive chart..."):
            st.plotly_chart(fig, use_container_width=False)
            st.success("✅ Chart rendered!")
        with st.expander("📚 Signal Reference Guide", expanded=False):
            st.markdown("""
            **Signal Legend:**
            - 🟢 Aggressive Buying
            - 🔴 Aggressive Selling
            - ⛔ Buyer Absorption  
            - 🚀 Seller Absorption
            - 💥 Bullish Breakout
            - 💣 Bearish Breakdown
            - 🐂 Bullish POI
            - 🐻 Bearish POI
            """)
        with st.expander("ℹ️ About Data Source"):
            st.markdown("""
            **Data Source Information:**

            - **Source**: NEPSE market data via Google Sheets
            - **Update Frequency**: End-of-day (EOD) data updated daily by 8:00 PM NPT
            - **History**: Contains up to 1 year of historical data
            - **Fields**: Open, High, Low, Close, Volume for all listed companies

            **Note**: This is unofficial data. For official data, please refer to [NEPSE](https://www.nepalstock.com.np/).
            """)
    except Exception as e:
        st.error(f"⚠️ Processing error: {str(e)}")
else:
    st.info("ℹ👆🏻 Enter a company symbol to get analysed chart 👆🏻")