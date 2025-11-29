"""
Data Quality Monitoring Dashboard
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(page_title="Data Quality Monitoring", page_icon="📊", layout="wide")

st.title("📊 Data Quality Monitoring Dashboard")

# Load stats
STATS_DIR = Path("airflow/dags/data/stats")
stats_data = []

if STATS_DIR.exists():
    for file in STATS_DIR.glob("*.json"):
        with open(file) as f:
            stats_data.append(json.load(f))

if not stats_data:
    st.warning("No ingestion statistics found yet.")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_files = len(stats_data)
    total_rows = sum(s['total_rows'] for s in stats_data)
    total_valid = sum(s['valid_rows'] for s in stats_data)
    total_invalid = sum(s['invalid_rows'] for s in stats_data)
    
    col1.metric("Total Files", total_files)
    col2.metric("Total Rows", total_rows)
    col3.metric("Valid Rows", total_valid, delta=f"{(total_valid/total_rows*100):.1f}%") 
    col4.metric("Invalid Rows", total_invalid, delta=f"{(total_invalid/total_rows*100):.1f}%", delta_color="inverse")
    
    # Charts
    st.subheader("Data Quality Overview")
    
    col1, col2 = st.columns(2)
    
    # Valid vs Invalid chart
    with col1:
        st.write("**Valid vs Invalid Data**")
        chart_data = pd.DataFrame({
            'Category': ['Valid', 'Invalid'],
            'Count': [total_valid, total_invalid]
        })
        st.bar_chart(chart_data.set_index('Category'))
    
    # Issues by type
    with col2:
        issue_types = {}
        for stat in stats_data:
            for issue in stat.get('issues', []):
                itype = issue['type']
                issue_types[itype] = issue_types.get(itype, 0) + issue['count']
        
        if issue_types:
            st.write("**Data Quality Issues by Type**")
            issue_df = pd.DataFrame({
                'Issue Type': list(issue_types.keys()),
                'Count': list(issue_types.values())
            })
            st.bar_chart(issue_df.set_index('Issue Type'))
    
    # Table of recent stats
    st.subheader("Recent Ingestion Statistics")
    df = pd.DataFrame(stats_data)
    st.dataframe(df[['timestamp', 'filename', 'total_rows', 'valid_rows', 'invalid_rows']], use_container_width=True)
    
    # Detailed issues
    st.subheader("Detailed Quality Issues")
    for idx, stat in enumerate(stats_data[-5:]):  # Show last 5
        with st.expander(f"📄 {stat['filename']} - {stat['timestamp'][:19]}"):
            st.write(f"**Total Rows:** {stat['total_rows']}")
            st.write(f"**Valid:** {stat['valid_rows']} | **Invalid:** {stat['invalid_rows']}")
            if stat.get('issues'):
                st.write("**Issues Found:**")
                for issue in stat['issues']:
                    st.write(f"- **{issue['type']}** ({issue['criticality']}): {issue['count']} occurrences in column '{issue['column']}'")
