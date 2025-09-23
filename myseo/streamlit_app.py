#!/usr/bin/env python3
"""
Streamlit Google Ads Keyword Research App
A web interface for keyword research using Google Ads API
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
import logging
from typing import List
from seo import SimpleKeywordResearch, KeywordMetrics
import time

# Configure page
st.set_page_config(
    page_title="Google Ads Keyword Research",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
    }
    .keyword-highlight {
        background: #e3f2fd;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        margin: 0.1rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'kr_instance' not in st.session_state:
    st.session_state.kr_instance = None

def initialize_keyword_research():
    """Initialize the keyword research tool with error handling"""
    try:
        if st.session_state.kr_instance is None:
            with st.spinner("🔧 Initializing Google Ads API connection..."):
                st.session_state.kr_instance = SimpleKeywordResearch()
            st.success("✅ Successfully connected to Google Ads API")
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize Google Ads API: {str(e)}")
        st.info("Please check your environment variables and API credentials")
        return False

def format_currency(value):
    """Format currency values"""
    if value == 0:
        return "$0.00"
    return f"${value:.2f}"

def format_number(value):
    """Format large numbers with commas"""
    return f"{value:,}"

def create_keyword_dataframe(results: List[KeywordMetrics]) -> pd.DataFrame:
    """Convert keyword results to a pandas DataFrame"""
    data = []
    for result in results:
        data.append({
            'Keyword': result.keyword,
            'Monthly Searches': result.search_volume,
            'Competition': result.competition,
            'Competition Index': result.competition_index,
            'Low Bid (USD)': result.low_bid_usd,
            'High Bid (USD)': result.high_bid_usd,
            'Avg Bid (USD)': (result.low_bid_usd + result.high_bid_usd) / 2 if result.high_bid_usd > 0 else 0
        })
    return pd.DataFrame(data)

def create_visualizations(df: pd.DataFrame):
    """Create visualizations for keyword data"""
    if df.empty:
        st.warning("No data available for visualization")
        return
    
    # Create tabs for different visualizations
    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
        "📊 Search Volume Distribution", 
        "⚔️ Competition Analysis", 
        "💰 Bid Analysis",
        "🎯 Opportunity Matrix"
    ])
    
    with viz_tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Search volume histogram
            fig_hist = px.histogram(
                df, 
                x='Monthly Searches', 
                nbins=20,
                title='Search Volume Distribution',
                labels={'Monthly Searches': 'Monthly Search Volume', 'count': 'Number of Keywords'}
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Top keywords by search volume
            top_keywords = df.nlargest(10, 'Monthly Searches')
            fig_top = px.bar(
                top_keywords, 
                x='Monthly Searches', 
                y='Keyword',
                orientation='h',
                title='Top 10 Keywords by Search Volume'
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)
    
    with viz_tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Competition distribution pie chart
            competition_counts = df['Competition'].value_counts()
            fig_pie = px.pie(
                values=competition_counts.values, 
                names=competition_counts.index,
                title='Competition Level Distribution'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Competition index vs search volume scatter
            fig_scatter = px.scatter(
                df, 
                x='Competition Index', 
                y='Monthly Searches',
                color='Competition',
                hover_data=['Keyword'],
                title='Competition vs Search Volume'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    with viz_tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Bid range analysis
            df_bids = df[df['High Bid (USD)'] > 0].copy()
            if not df_bids.empty:
                fig_bid_box = px.box(
                    df_bids, 
                    y=['Low Bid (USD)', 'High Bid (USD)'],
                    title='Bid Range Distribution'
                )
                st.plotly_chart(fig_bid_box, use_container_width=True)
            else:
                st.info("No bid data available for visualization")
        
        with col2:
            # Average bid vs search volume
            df_valid_bids = df[(df['Avg Bid (USD)'] > 0) & (df['Monthly Searches'] > 0)]
            if not df_valid_bids.empty:
                fig_bid_scatter = px.scatter(
                    df_valid_bids,
                    x='Avg Bid (USD)',
                    y='Monthly Searches',
                    size='Competition Index',
                    hover_data=['Keyword'],
                    title='Avg Bid vs Search Volume'
                )
                st.plotly_chart(fig_bid_scatter, use_container_width=True)
            else:
                st.info("No valid bid data for scatter plot")
    
    with viz_tab4:
        # Opportunity matrix: High volume, low competition
        fig_matrix = px.scatter(
            df,
            x='Competition Index',
            y='Monthly Searches',
            size='Avg Bid (USD)',
            color='Competition',
            hover_data=['Keyword'],
            title='Keyword Opportunity Matrix (Bottom-right = Best opportunities)'
        )
        fig_matrix.add_vline(x=0.5, line_dash="dash", line_color="gray", annotation_text="Medium Competition")
        fig_matrix.add_hline(y=df['Monthly Searches'].median(), line_dash="dash", line_color="gray", annotation_text="Median Volume")
        st.plotly_chart(fig_matrix, use_container_width=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Google Ads Keyword Research Tool</h1>
        <p>Discover high-performing keywords with competitive analysis and search volume data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Environment check
        st.subheader("🔍 Environment Status")
        required_vars = [
            "GOOGLE_ADS_DEVELOPER_TOKEN",
            "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_CUSTOMER_ID"
        ]
        
        env_status = {}
        for var in required_vars:
            env_status[var] = "✅" if os.getenv(var) else "❌"
            st.write(f"{env_status[var]} {var}")
        
        if all(status == "✅" for status in env_status.values()):
            st.success("All required environment variables are set!")
            api_ready = initialize_keyword_research()
        else:
            st.error("Missing required environment variables")
            st.info("Please set up your .env file with Google Ads API credentials")
            api_ready = False
        
        st.divider()
        
        # Research parameters
        st.subheader("🎯 Research Parameters")
        
        keywords_input = st.text_area(
            "Seed Keywords (one per line)",
            value="python programming\nweb development\ndata science",
            height=100,
            help="Enter seed keywords that will be used to generate related keyword ideas"
        )
        
        location = st.selectbox(
            "Target Location",
            ["United States", "United Kingdom", "Canada","India"],
            help="Geographic location for keyword research"
        )
        
        max_results = st.slider(
            "Maximum Results",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Maximum number of keyword suggestions to retrieve"
        )
        
        include_adult = st.checkbox(
            "Include Adult Keywords",
            value=False,
            help="Whether to include adult-themed keywords in results"
        )
    
    # Main content area
    if not api_ready:
        st.error("❌ Google Ads API not ready. Please check your configuration.")
        return
    
    # Research section
    st.header("🚀 Keyword Research")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔍 Start Keyword Research", type="primary"):
            keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
            
            if not keywords:
                st.error("Please enter at least one seed keyword")
                return
            
            try:
                with st.spinner(f"🔄 Researching keywords for: {', '.join(keywords)}..."):
                    progress_bar = st.progress(0)
                    progress_bar.progress(25, "Connecting to Google Ads API...")
                    
                    results = st.session_state.kr_instance.search_keywords(
                        keywords=keywords,
                        location=location,
                        max_results=max_results,
                        include_adult_keywords=include_adult
                    )
                    
                    progress_bar.progress(75, "Processing results...")
                    st.session_state.research_results = results
                    progress_bar.progress(100, "Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()
                
                st.success(f"✅ Found {len(results)} keyword ideas!")
                
            except Exception as e:
                st.error(f"❌ Research failed: {str(e)}")
                st.exception(e)
    
    with col2:
        if st.session_state.research_results:
            if st.button("💾 Download CSV"):
                df = create_keyword_dataframe(st.session_state.research_results)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=csv,
                    file_name=f"keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.session_state.research_results:
            if st.button("🔄 Clear Results"):
                st.session_state.research_results = None
                st.rerun()
    
    # Results section
    if st.session_state.research_results:
        st.divider()
        st.header("📊 Results Analysis")
        
        results = st.session_state.research_results
        df = create_keyword_dataframe(results)
        
        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Keywords", len(results))
        
        with col2:
            avg_volume = sum(r.search_volume for r in results) / len(results)
            st.metric("Avg Search Volume", f"{avg_volume:,.0f}")
        
        with col3:
            high_volume = len([r for r in results if r.search_volume > 1000])
            st.metric("High Volume (>1K)", high_volume)
        
        with col4:
            low_competition = len([r for r in results if r.competition == "LOW"])
            st.metric("Low Competition", low_competition)
        
        with col5:
            valid_bids = [r for r in results if r.high_bid_usd > 0]
            if valid_bids:
                avg_bid = sum(r.high_bid_usd for r in valid_bids) / len(valid_bids)
                st.metric("Avg High Bid", f"${avg_bid:.2f}")
            else:
                st.metric("Avg High Bid", "N/A")
        
        # Visualizations
        st.subheader("📈 Data Visualizations")
        create_visualizations(df)
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        
        # Filter options
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            min_volume = st.number_input(
                "Minimum Search Volume",
                min_value=0,
                max_value=int(df['Monthly Searches'].max()) if not df.empty else 0,
                value=0
            )
        
        with filter_col2:
            competition_filter = st.multiselect(
                "Competition Level",
                options=df['Competition'].unique().tolist() if not df.empty else [],
                default=df['Competition'].unique().tolist() if not df.empty else []
            )
        
        with filter_col3:
            max_bid = st.number_input(
                "Maximum Avg Bid ($)",
                min_value=0.0,
                max_value=float(df['Avg Bid (USD)'].max()) if not df.empty and df['Avg Bid (USD)'].max() > 0 else 100.0,
                value=float(df['Avg Bid (USD)'].max()) if not df.empty and df['Avg Bid (USD)'].max() > 0 else 100.0,
                step=0.1
            )
        
        # Apply filters
        if not df.empty:
            filtered_df = df[
                (df['Monthly Searches'] >= min_volume) &
                (df['Competition'].isin(competition_filter)) &
                (df['Avg Bid (USD)'] <= max_bid)
            ]
            
            st.write(f"Showing {len(filtered_df)} of {len(df)} keywords")
            
            # Style the dataframe
            styled_df = filtered_df.style.format({
                'Monthly Searches': '{:,}',
                'Competition Index': '{:.2f}',
                'Low Bid (USD)': '${:.2f}',
                'High Bid (USD)': '${:.2f}',
                'Avg Bid (USD)': '${:.2f}'
            }).background_gradient(subset=['Monthly Searches'], cmap='Greens')
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Top opportunities
            st.subheader("🎯 Top Opportunities")
            st.write("Keywords with high search volume and low competition:")
            
            opportunities = filtered_df[
                (filtered_df['Monthly Searches'] > filtered_df['Monthly Searches'].median()) &
                (filtered_df['Competition'] == 'LOW')
            ].sort_values('Monthly Searches', ascending=False).head(10)
            
            if not opportunities.empty:
                for idx, row in opportunities.iterrows():
                    with st.expander(f"🔑 {row['Keyword']} - {format_number(row['Monthly Searches'])} searches"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Competition:** {row['Competition']}")
                            st.write(f"**Competition Index:** {row['Competition Index']:.2f}")
                        with col2:
                            st.write(f"**Low Bid:** {format_currency(row['Low Bid (USD)'])}")
                            st.write(f"**High Bid:** {format_currency(row['High Bid (USD)'])}")
                        with col3:
                            st.write(f"**Avg Bid:** {format_currency(row['Avg Bid (USD)'])}")
            else:
                st.info("No high-opportunity keywords found with current filters.")

if __name__ == "__main__":
    main()