import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Tool",
    page_icon="📈",
    layout="wide"
)

# Helper functions
def format_currency(value):
    """Format large numbers as currency with appropriate suffix"""
    if value is None or pd.isna(value):
        return "N/A"
    
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.2f}"

def format_number(value):
    """Format large numbers with appropriate suffix"""
    if value is None or pd.isna(value):
        return "N/A"
    
    if value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    elif value >= 1e3:
        return f"{value/1e3:.2f}K"
    else:
        return f"{value:,.2f}"

def format_percent(value):
    """Format decimal as percentage"""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.2f}%"

# Title and description
st.title("Stock Analysis Tool")
st.markdown("Get comprehensive stock information including price data, financials, options, and more.")

# Sidebar for ticker input
with st.sidebar:
    st.header("Settings")
    ticker_input = st.text_input(
        "Enter Stock Ticker",
        value="AAPL",
        help="Enter a stock ticker symbol (e.g., AAPL, MSFT, TSLA)"
    ).upper().strip()
    
    analyze_button = st.button("Analyze Stock", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Examples")
    st.markdown("- AAPL (Apple)")
    st.markdown("- MSFT (Microsoft)")
    st.markdown("- TSLA (Tesla)")
    st.markdown("- GOOGL (Google)")
    st.markdown("- NVDA (Nvidia)")
    
    st.markdown("---")
    st.markdown("### Recently Searched")
    
    # Initialize session state for recently searched tickers
    if 'recent_tickers' not in st.session_state:
        st.session_state.recent_tickers = []
    
    # Add current ticker to recent searches if analyze button is clicked
    if analyze_button and ticker_input:
        if ticker_input not in st.session_state.recent_tickers:
            st.session_state.recent_tickers.insert(0, ticker_input)
            # Keep only last 5 searches
            st.session_state.recent_tickers = st.session_state.recent_tickers[:5]
    
    # Display recent tickers as clickable buttons
    if st.session_state.recent_tickers:
        for ticker in st.session_state.recent_tickers:
            if st.button(ticker, key=f"recent_{ticker}", use_container_width=True):
                st.session_state.selected_ticker = ticker
                st.rerun()
    else:
        st.markdown("*No recent searches*")

# Main content
if analyze_button or ticker_input or 'selected_ticker' in st.session_state:
    # Use selected ticker from recent searches if available
    if 'selected_ticker' in st.session_state:
        ticker_input = st.session_state.selected_ticker
        del st.session_state.selected_ticker
    
    if not ticker_input:
        st.error("Please enter a valid ticker symbol")
    else:
        with st.spinner(f"Fetching data for {ticker_input}..."):
            try:
                # Get stock data
                stock = yf.Ticker(ticker_input)
                info = stock.info
                
                # Validate ticker
                if not info or 'symbol' not in info:
                    st.error(f"Unable to find data for ticker '{ticker_input}'. Please verify the ticker symbol is correct.")
                else:
                    # Company Header
                    st.header(f"{info.get('longName', ticker_input)}")
                    st.markdown(f"**Ticker:** {info.get('symbol', 'N/A')} | **Exchange:** {info.get('exchange', 'N/A')} | **Sector:** {info.get('sector', 'N/A')}")
                    
                    # Live Price Tracking
                    st.subheader("Live Price Tracker")
                    
                    # Auto-refresh toggle
                    col_refresh1, col_refresh2 = st.columns([3, 1])
                    with col_refresh1:
                        auto_refresh = st.checkbox("Enable auto-refresh (updates every 10 seconds)", value=False)
                    with col_refresh2:
                        if st.button("Refresh Now", type="secondary"):
                            st.rerun()
                    
                    # Get live price data
                    live_data = stock.history(period="1d", interval="1m")
                    
                    if not live_data.empty:
                        latest_price = live_data['Close'].iloc[-1]
                        previous_close = info.get('previousClose', 0)
                        
                        # Calculate change
                        if previous_close and previous_close > 0:
                            price_change = latest_price - previous_close
                            price_change_pct = (price_change / previous_close) * 100
                        else:
                            price_change = 0
                            price_change_pct = 0
                        
                        # Display live price with color coding
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if price_change >= 0:
                                st.metric(
                                    "Live Price", 
                                    f"${latest_price:.2f}",
                                    f"+${price_change:.2f} (+{price_change_pct:.2f}%)"
                                )
                            else:
                                st.metric(
                                    "Live Price", 
                                    f"${latest_price:.2f}",
                                    f"${price_change:.2f} ({price_change_pct:.2f}%)"
                                )
                        
                        with col2:
                            st.metric("Previous Close", f"${previous_close:.2f}")
                        
                        with col3:
                            st.metric("Day High", f"${live_data['High'].max():.2f}")
                        
                        with col4:
                            st.metric("Day Low", f"${live_data['Low'].min():.2f}")
                        
                        # Intraday price chart with graph type selector
                        st.markdown("**Intraday Price Movement**")
                        
                        chart_type = st.radio(
                            "Chart Type:",
                            ["Line", "Candlestick"],
                            horizontal=True,
                            key="intraday_chart_type"
                        )
                        
                        fig_intraday = go.Figure()
                        
                        if chart_type == "Line":
                            # Clean line chart without fill
                            fig_intraday.add_trace(go.Scatter(
                                x=live_data.index,
                                y=live_data['Close'],
                                mode='lines',
                                name='Price',
                                line=dict(color='#1f77b4', width=2.5),
                                hovertemplate='<b>Time</b>: %{x}<br><b>Price</b>: $%{y:.2f}<extra></extra>'
                            ))
                        else:
                            # Candlestick chart
                            fig_intraday.add_trace(go.Candlestick(
                                x=live_data.index,
                                open=live_data['Open'],
                                high=live_data['High'],
                                low=live_data['Low'],
                                close=live_data['Close'],
                                name='Price',
                                increasing_line_color='#26a69a',
                                decreasing_line_color='#ef5350'
                            ))
                        
                        fig_intraday.update_layout(
                            title=dict(
                                text=f"{ticker_input} - Today's Price Movement",
                                font=dict(size=18, color='#2C3E50')
                            ),
                            xaxis_title="Time",
                            yaxis_title="Price ($)",
                            height=450,
                            hovermode='x unified',
                            showlegend=False,
                            xaxis_rangeslider_visible=False,
                            plot_bgcolor='#f5f5f5',
                            paper_bgcolor='#000000ff',
                            font=dict(color='#f5f5f5')
                        )
                        
                        fig_intraday.update_xaxes(showgrid=True, gridcolor='white')
                        fig_intraday.update_yaxes(showgrid=True, gridcolor='white')
                        
                        st.plotly_chart(fig_intraday, use_container_width=True)
                        
                        # Auto-refresh functionality
                        if auto_refresh:
                            import time
                            time.sleep(10)
                            st.rerun()
                    else:
                        st.warning("Live price data unavailable. Market may be closed.")
                    
                    st.markdown("---")
                    
                    # Current Price - Big Display
                    st.subheader("Market Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        st.metric("Current Price", f"${current_price:,.2f}" if current_price else "N/A")
                    with col2:
                        market_cap = info.get('marketCap')
                        st.metric("Market Cap", format_currency(market_cap))
                    with col3:
                        pe_ratio = info.get('trailingPE')
                        st.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                    with col4:
                        div_yield = info.get('dividendYield')
                        st.metric("Dividend Yield", format_percent(div_yield))
                    
                    st.markdown("---")
                    
                    # Tabs for different sections
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "Overview", "Financials", "Trading Info", "Options & Shorts", "Charts", "News"
                    ])
                    
                    # TAB 1: Overview
                    with tab1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Company Information")
                            overview_data = {
                                'Metric': ['Company Name', 'Ticker', 'Exchange', 'Sector', 'Industry', 'Country', 'Website'],
                                'Value': [
                                    info.get('longName', 'N/A'),
                                    info.get('symbol', 'N/A'),
                                    info.get('exchange', 'N/A'),
                                    info.get('sector', 'N/A'),
                                    info.get('industry', 'N/A'),
                                    info.get('country', 'N/A'),
                                    info.get('website', 'N/A')
                                ]
                            }
                            st.dataframe(pd.DataFrame(overview_data), hide_index=True, use_container_width=True)
                        
                        with col2:
                            st.subheader("Valuation Metrics")
                            valuation_data = {
                                'Metric': [
                                    'Market Cap',
                                    'Enterprise Value',
                                    'P/E Ratio (TTM)',
                                    'Forward P/E',
                                    'PEG Ratio',
                                    'Price/Sales (TTM)',
                                    'Price/Book',
                                    'EV/Revenue',
                                    'EV/EBITDA'
                                ],
                                'Value': [
                                    format_currency(info.get('marketCap')),
                                    format_currency(info.get('enterpriseValue')),
                                    f"{info.get('trailingPE', 'N/A')}",
                                    f"{info.get('forwardPE', 'N/A')}",
                                    f"{info.get('pegRatio', 'N/A')}",
                                    f"{info.get('priceToSalesTrailing12Months', 'N/A')}",
                                    f"{info.get('priceToBook', 'N/A')}",
                                    f"{info.get('enterpriseToRevenue', 'N/A')}",
                                    f"{info.get('enterpriseToEbitda', 'N/A')}"
                                ]
                            }
                            st.dataframe(pd.DataFrame(valuation_data), hide_index=True, use_container_width=True)
                    
                    # TAB 2: Financials
                    with tab2:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Profitability")
                            profitability_data = {
                                'Metric': [
                                    'Profit Margin',
                                    'Operating Margin',
                                    'Gross Margin',
                                    'Return on Equity (ROE)',
                                    'Return on Assets (ROA)'
                                ],
                                'Value': [
                                    format_percent(info.get('profitMargins')),
                                    format_percent(info.get('operatingMargins')),
                                    format_percent(info.get('grossMargins')),
                                    format_percent(info.get('returnOnEquity')),
                                    format_percent(info.get('returnOnAssets'))
                                ]
                            }
                            st.dataframe(pd.DataFrame(profitability_data), hide_index=True, use_container_width=True)
                            
                            st.subheader("Earnings")
                            earnings_data = {
                                'Metric': [
                                    'EPS (TTM)',
                                    'Forward EPS',
                                    'Earnings Growth',
                                    'Revenue Growth'
                                ],
                                'Value': [
                                    f"${info.get('trailingEps', 'N/A')}",
                                    f"${info.get('forwardEps', 'N/A')}",
                                    format_percent(info.get('earningsGrowth')),
                                    format_percent(info.get('revenueGrowth'))
                                ]
                            }
                            st.dataframe(pd.DataFrame(earnings_data), hide_index=True, use_container_width=True)
                        
                        with col2:
                            st.subheader("Financial Health")
                            financial_data = {
                                'Metric': [
                                    'Total Revenue',
                                    'Revenue per Share',
                                    'Total Cash',
                                    'Cash per Share',
                                    'Total Debt',
                                    'Debt/Equity',
                                    'Current Ratio',
                                    'Quick Ratio'
                                ],
                                'Value': [
                                    format_currency(info.get('totalRevenue')),
                                    f"${info.get('revenuePerShare', 'N/A')}",
                                    format_currency(info.get('totalCash')),
                                    f"${info.get('totalCashPerShare', 'N/A')}",
                                    format_currency(info.get('totalDebt')),
                                    f"{info.get('debtToEquity', 'N/A')}",
                                    f"{info.get('currentRatio', 'N/A')}",
                                    f"{info.get('quickRatio', 'N/A')}"
                                ]
                            }
                            st.dataframe(pd.DataFrame(financial_data), hide_index=True, use_container_width=True)
                    
                    # TAB 3: Trading Info
                    with tab3:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Current Trading")
                            trading_data = {
                                'Metric': [
                                    'Current Price',
                                    'Previous Close',
                                    'Open',
                                    'Day Low',
                                    'Day High',
                                    '52 Week Low',
                                    '52 Week High',
                                    'Volume',
                                    'Avg Volume (10d)',
                                    'Avg Volume (3m)'
                                ],
                                'Value': [
                                    f"${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}",
                                    f"${info.get('previousClose', 'N/A')}",
                                    f"${info.get('open', info.get('regularMarketOpen', 'N/A'))}",
                                    f"${info.get('dayLow', 'N/A')}",
                                    f"${info.get('dayHigh', 'N/A')}",
                                    f"${info.get('fiftyTwoWeekLow', 'N/A')}",
                                    f"${info.get('fiftyTwoWeekHigh', 'N/A')}",
                                    format_number(info.get('volume', 'N/A')),
                                    format_number(info.get('averageVolume10days', 'N/A')),
                                    format_number(info.get('averageVolume', 'N/A'))
                                ]
                            }
                            st.dataframe(pd.DataFrame(trading_data), hide_index=True, use_container_width=True)
                        
                        with col2:
                            st.subheader("Share Statistics")
                            share_data = {
                                'Metric': [
                                    'Shares Outstanding',
                                    'Float Shares',
                                    '% Held by Insiders',
                                    '% Held by Institutions',
                                    'Short Ratio',
                                    'Short % of Float'
                                ],
                                'Value': [
                                    format_number(info.get('sharesOutstanding')),
                                    format_number(info.get('floatShares')),
                                    format_percent(info.get('heldPercentInsiders')),
                                    format_percent(info.get('heldPercentInstitutions')),
                                    f"{info.get('shortRatio', 'N/A')}",
                                    format_percent(info.get('shortPercentOfFloat'))
                                ]
                            }
                            st.dataframe(pd.DataFrame(share_data), hide_index=True, use_container_width=True)
                            
                            st.subheader("Analyst Recommendations")
                            analyst_data = {
                                'Metric': [
                                    'Target Mean Price',
                                    'Target High Price',
                                    'Target Low Price',
                                    'Recommendation',
                                    'Number of Analysts'
                                ],
                                'Value': [
                                    f"${info.get('targetMeanPrice', 'N/A')}",
                                    f"${info.get('targetHighPrice', 'N/A')}",
                                    f"${info.get('targetLowPrice', 'N/A')}",
                                    info.get('recommendationKey', 'N/A').upper() if info.get('recommendationKey') else 'N/A',
                                    info.get('numberOfAnalystOpinions', 'N/A')
                                ]
                            }
                            st.dataframe(pd.DataFrame(analyst_data), hide_index=True, use_container_width=True)
                    
                    # TAB 4: Options & Shorts
                    with tab4:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Short Interest Details")
                            try:
                                short_data = {
                                    'Metric': [
                                        'Short Interest',
                                        'Short % of Float',
                                        'Short % of Shares Outstanding',
                                        'Short Ratio (Days to Cover)',
                                        'Shares Short',
                                        'Shares Short (Prior Month)'
                                    ],
                                    'Value': [
                                        format_number(info.get('sharesShort', 'N/A')),
                                        format_percent(info.get('shortPercentOfFloat')),
                                        format_percent(info.get('shortPercentOfSharesOutstanding')),
                                        f"{info.get('shortRatio', 'N/A')} days",
                                        format_number(info.get('sharesShort', 'N/A')),
                                        format_number(info.get('sharesShortPriorMonth', 'N/A'))
                                    ]
                                }
                                st.dataframe(pd.DataFrame(short_data), hide_index=True, use_container_width=True)
                            except Exception as e:
                                st.warning("Short interest data not available")
                        
                        with col2:
                            st.subheader("Options Information")
                            try:
                                options_dates = stock.options
                                
                                if options_dates and len(options_dates) > 0:
                                    st.write(f"**Available expiration dates:** {len(options_dates)}")
                                    st.write(f"**Next 5 expirations:** {', '.join(options_dates[:5])}")
                                    
                                    nearest_expiry = options_dates[0]
                                    opt_chain = stock.option_chain(nearest_expiry)
                                    
                                    options_stats = {
                                        'Metric': [
                                            'Total Call Volume',
                                            'Total Put Volume',
                                            'Put/Call Ratio (Volume)',
                                            'Total Call OI',
                                            'Total Put OI',
                                            'Put/Call Ratio (OI)'
                                        ],
                                        'Value': [
                                            f"{opt_chain.calls['volume'].sum():,.0f}",
                                            f"{opt_chain.puts['volume'].sum():,.0f}",
                                            f"{opt_chain.puts['volume'].sum() / opt_chain.calls['volume'].sum():.2f}" if opt_chain.calls['volume'].sum() > 0 else "N/A",
                                            f"{opt_chain.calls['openInterest'].sum():,.0f}",
                                            f"{opt_chain.puts['openInterest'].sum():,.0f}",
                                            f"{opt_chain.puts['openInterest'].sum() / opt_chain.calls['openInterest'].sum():.2f}" if opt_chain.calls['openInterest'].sum() > 0 else "N/A"
                                        ]
                                    }
                                    st.dataframe(pd.DataFrame(options_stats), hide_index=True, use_container_width=True)
                                else:
                                    st.info("No options data available for this stock")
                            except Exception as e:
                                st.warning("Options data not available")
                        
                        # Dividend info
                        st.subheader("Dividend Information")
                        div_rate = info.get('dividendRate', 0)
                        if div_rate and div_rate > 0:
                            dividend_data = {
                                'Metric': ['Dividend Rate', 'Dividend Yield', 'Payout Ratio', 'Ex-Dividend Date'],
                                'Value': [
                                    f"${div_rate}",
                                    format_percent(info.get('dividendYield')),
                                    format_percent(info.get('payoutRatio')),
                                    info.get('exDividendDate', 'N/A')
                                ]
                            }
                            st.dataframe(pd.DataFrame(dividend_data), hide_index=True, use_container_width=True)
                        else:
                            st.info("This stock does not pay dividends")
                    
                    # TAB 5: Charts
                    with tab5:
                        # Get historical data
                        hist = stock.history(period="3mo")
                        
                        if not hist.empty:
                            # Candlestick chart
                            st.subheader("Price Chart (Last 3 Months)")
                            
                            fig = make_subplots(
                                rows=2, cols=1,
                                shared_xaxes=True,
                                vertical_spacing=0.03,
                                subplot_titles=(f'{ticker_input} Price Chart', 'Volume'),
                                row_width=[0.2, 0.7]
                            )
                            
                            fig.add_trace(
                                go.Candlestick(
                                    x=hist.index,
                                    open=hist['Open'],
                                    high=hist['High'],
                                    low=hist['Low'],
                                    close=hist['Close'],
                                    name='Price'
                                ),
                                row=1, col=1
                            )
                            
                            colors = ['red' if hist['Close'].iloc[i] < hist['Open'].iloc[i] else 'green' 
                                      for i in range(len(hist))]
                            
                            fig.add_trace(
                                go.Bar(
                                    x=hist.index,
                                    y=hist['Volume'],
                                    name='Volume',
                                    marker_color=colors
                                ),
                                row=2, col=1
                            )
                            
                            fig.update_layout(
                                yaxis_title='Price ($)',
                                yaxis2_title='Volume',
                                xaxis_rangeslider_visible=False,
                                height=600,
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Moving averages
                            st.subheader("Moving Averages")
                            
                            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                            
                            fig2 = go.Figure()
                            
                            fig2.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['Close'],
                                mode='lines',
                                name='Close Price',
                                line=dict(color='blue', width=2)
                            ))
                            
                            fig2.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['SMA_20'],
                                mode='lines',
                                name='20-Day SMA',
                                line=dict(color='orange', width=1.5, dash='dash')
                            ))
                            
                            fig2.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['SMA_50'],
                                mode='lines',
                                name='50-Day SMA',
                                line=dict(color='red', width=1.5, dash='dot')
                            ))
                            
                            fig2.update_layout(
                                title=f'{ticker_input} Price with Moving Averages',
                                xaxis_title='Date',
                                yaxis_title='Price ($)',
                                height=500,
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig2, use_container_width=True)
                            
                            # Recent price data table
                            st.subheader("Last 10 Trading Days")
                            st.dataframe(
                                hist[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10),
                                use_container_width=True
                            )
                        else:
                            st.warning("No historical data available for this ticker")
                    
                    # TAB 6: News
                    with tab6:
                        st.subheader("Recent News")
                        try:
                            news = stock.news
                            
                            # Filter out articles with missing data
                            valid_news = []
                            if news and len(news) > 0:
                                for article in news:
                                    # Only include articles with actual title and link
                                    if (article.get('title') and 
                                        article.get('title') != 'N/A' and 
                                        article.get('link') and 
                                        article.get('link') != 'N/A'):
                                        valid_news.append(article)
                            
                            if valid_news and len(valid_news) > 0:
                                for i, article in enumerate(valid_news[:10], 1):
                                    with st.container():
                                        st.markdown(f"**{i}. {article.get('title', 'No title')}**")
                                        publisher = article.get('publisher', 'Unknown')
                                        st.markdown(f"*Publisher: {publisher}*")
                                        link = article.get('link', '#')
                                        st.markdown(f"[Read Article]({link})")
                                        st.markdown("---")
                            else:
                                st.info("News data is currently unavailable for this stock. This is a known limitation with the data provider.")
                                st.markdown("**Alternative:** Visit [Yahoo Finance](https://finance.yahoo.com/quote/{}/news) or [Google Finance](https://www.google.com/finance/quote/{}:NASDAQ) for news.".format(ticker_input, ticker_input))
                        except Exception as e:
                            st.warning("Unable to fetch news data. This feature may be temporarily unavailable.")
                            st.markdown("**Alternative:** Visit [Yahoo Finance](https://finance.yahoo.com/quote/{}/news) or [Google Finance](https://www.google.com/finance/quote/{}:NASDAQ) for news.".format(ticker_input, ticker_input))
                    
            except Exception as e:
                st.error(f"Error fetching stock data: {e}")
                st.info("Please check your internet connection and verify the ticker symbol.")

else:
    # Welcome message when no analysis has been run
    st.info("Enter a stock ticker in the sidebar and click 'Analyze Stock' to get started!")
    
    st.markdown("---")
    
    st.markdown("### What you'll get:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Company Overview**")
        st.markdown("- Company information")
        st.markdown("- Valuation metrics")
        st.markdown("- Current price data")
    
    with col2:
        st.markdown("**Financial Data**")
        st.markdown("- Profitability metrics")
        st.markdown("- Financial health")
        st.markdown("- Earnings information")
    
    with col3:
        st.markdown("**Trading & Charts**")
        st.markdown("- Interactive price charts")
        st.markdown("- Options & short interest")
        st.markdown("- Recent news")

# Footer
st.markdown("---")
st.markdown("**Disclaimer:** This tool is for informational purposes only. Not financial advice. Always do your own research.")
