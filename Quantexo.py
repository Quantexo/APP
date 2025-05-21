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

st.markdown(
    """ <style>
    .stApp {
    background-color: darkslategray;
    } </style>
    """,
    unsafe_allow_html=True
)
       
# --- SECTOR TO COMPANY MAPPING ---
sector_to_companies = {
    "Index": {"NEPSE"},
    "Sub-Index": {"BANKING", "DEVBANK", "FINANCE", "HOTELS", "HYDROPOWER", "INVESTMENT","LIFEINSU","MANUFACUTRE","MICROFINANCE","NONLIFEINSU", "OTHERS", "TRADING"},
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
        
        # Get current time in Nepal timezone
        nepal_tz = pytz.timezone('Asia/Kathmandu')
        last_updated = datetime.now(nepal_tz)

        # Filter data based on company symbol
        df['symbol'] = df['symbol'].astype(str).str.strip().str.upper()
        filtered_df = df[df['symbol'].str.upper() == symbol.upper()]
        return filtered_df, last_updated
    except Exception as e:
        st.error(f"🔴 Error fetching data: {str(e)}")
        return pd.DataFrame(), None

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
        if (
            row['open'] > row['close'] and
            row['close'] <= row['low'] + (row['high'] - row['low']) * 0.1 and
            row['volume'] > avg_volume[i] * 2 and
            body > prev_body and
            '🔴' not in recent_tags.values
        ):
            df.at[i, 'tag'] = '🔴'
        if (
            row['close'] > row['open'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df.loc[df['tag'] == '⛔', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] < row['open']:
                    df.at[j, 'tag'] = '⛔'
                    break
        if (
            row['open'] > row['close'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df.loc[df['tag'] == '🚀', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] > row['open']:
                    df.at[j, 'tag'] = '🚀'
                    break
        if (
            i >= 10 and
            row['close'] > max(df['high'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df['tag'].iloc[i - 8:i] == '💥').any():
                df.at[i, 'tag'] = '💥'
        if (
            i >= 10 and
            row['close'] < min(df['low'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df['tag'].iloc[i - 8:i] == '💣').any():
                df.at[i, 'tag'] = '💣'
        if (
            row['close'] > row['open'] and
            body > (row['high'] - row['low']) * 0.85 and
            row['volume'] > avg_volume[i] * 2
        ):
            df.at[i, 'tag'] = '🐂'
        if (
            row['open'] > row['close'] and
            body > (row['high'] - row['low']) * 0.85 and
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

if company_symbol:
    sheet_name = "Daily Price"
    df, last_updated = get_sheet_data(company_symbol, sheet_name)

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
                "🔚 LTP: %{customdata[4]:.2f}<br>" +
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
                    "🔚 LTP: %{customdata[3]:.2f}<br>" +
                    "📊 Point Change: %{customdata[4]:.2f}<br>" +
                    f"{tag_labels.get(tag, tag)}<extra></extra>"
                )
            ))
        def get_custom_filename(company_symbol):
            """Generate a custom filename with timestamp"""
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            now = datetime.now(nepal_tz)
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            return f"{company_symbol}_chart_{timestamp}_Quantexo🕵️"
        # Calculate 20 days ahead of the last date
        last_date = df['date'].max()
        extended_date = last_date + timedelta(days=20)
        fig.update_layout(
            height=800,
            width=1800,
            config = {'displayModeBar': True, 'displaylogo': False, 'toImageButtonOptions': {
                'filename': get_custom_filename(company_symbol), 
                'format': 'png',
            }},
            plot_bgcolor="darkslategray",
            paper_bgcolor="darkslategray",
            font_color="white",
            xaxis=dict(title="Date", tickangle=-45, showgrid=False, range=[(df['date'].max() - pd.Timedelta(days=365)), extended_date]), #extend x-axis to show space after latest date
            yaxis=dict(title="Price", showgrid=False, zeroline=True, zerolinecolor="gray", autorange=True),
            margin=dict(l=0, r=0, b=0, t=0),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,  # Adjust this value to move further down if needed
                xanchor="center",
                x=0.5,
                font=dict(size=14),
                bgcolor="rgba(0,0,0,0)"  # Optional: keeps legend background transparent)
            ),
            # Add zoom and pan capabilities
            dragmode="zoom",  # Enable box zoom
            annotations=[
                dict(
                    text=f"Quantexo 🕵️ <br> {company_symbol}",
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
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=2, label="2y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        df['date'] = pd.to_datetime(df['date'])
        last_data_date = df['date'].max().strftime("%Y-%m-%d")
        if last_updated:
            formatted_time = last_updated.strftime("%Y-%m-%d %H:%M:%S")
            cols = st.columns(2)
            cols[0].caption(f"⏱️ Data fetched: {formatted_time}")
            cols[1].caption(f"📅 Latest data point: {last_data_date}")
        st.plotly_chart(fig, use_container_width=False)
        st.markdown(f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const button = document.createElement('button');
            button.innerText = '📸 Custom Snapshot';
            button.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
            `;
            button.onclick = function() {{
                Plotly.downloadImage(document.querySelector('.plotly-graph-div'), {{
                    format: 'png',
                    filename: '{get_custom_filename(company_symbol)}',
                    height: 800,
                    width: 1800
                }});
            }};
            document.querySelector('.plotly-graph-div').appendChild(button);
        }});
        </script>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"⚠️ Processing error: {str(e)}")
else:
    st.info("ℹ👆🏻 Enter a company symbol to get analysed chart 👆🏻")

def show_legend():
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
if st.sidebar.button("📚 Signal Reference Guide"):
    show_legend()
def show_source():
    with st.expander("ℹ️ About Data Source"):
        st.markdown("""
        **Data Source Information:*
        - **Source**: NEPSE market data via Google Sheets
        - **Update Frequency**: End-of-trading hour (EOTH) data updated daily by 3:30 PM NPT
        - **History**: Contains up to 2 year of historical data
        - **Fields**: Open, High, Low, Close, Volume for all listed companies
        **Note**: This is official data extracted from [NEPSE](https://nepalstock.com/).
        """)
if st.sidebar.button("ℹ️ About Data Source"):
    show_legend()
def show_faqs():
    with st.expander("🔍 General Questions"):
        st.markdown("""
        **Q: Why don't I see any signals for my stock?**  
        A: This typically means no strong patterns were detected in the recent price action according to our algorithms.

        **Q: How often is the data updated?**  
        A: After the end of continuous session, data is updated daily by 3:30 PM NPT.
        """)

    with st.expander("📈 Technical Questions"):
        st.markdown("""
        **Q: What's the difference between 🟢 and 🐂 signals?**  
        A: 🟢 indicates aggressive buying with strong volume, while 🐂 shows particularly large bullish candles (>85% range).

        **Q: Why do some signals disappear when I zoom?**  
        A: This is normal chart behavior - signals remain but may be hidden at certain zoom levels.
        """)

    with st.expander("💾 Data Questions"):
        st.markdown("""
        **Q: Where does the data come from?**  
        A: Our Google Sheets aggregation of NEPSE market data (Extracted from [NEPSE](https://nepalstock.com/)).

        **Q: How can I get historical data?**  
        A: Currently we provide 1.5 year of historical data.
        """)
if st.sidebar.button("❓ Frequently Asked Questions"):
    show_faqs()