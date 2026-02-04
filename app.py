import streamlit as st
import sys
import os

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.sheets_connector import get_connector

st.set_page_config(
    page_title="Recruiters Assistant",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Recruiters Assistant")
st.subheader("AI-Powered Recruitment Pipeline Manager")

st.markdown("""
### Welcome! 
This system helps you manage your recruitment pipeline with AI assistance.

**Available Tools:**
- 📊 **Pipeline Dashboard** - View and manage all candidates
- 📅 **Interview Scheduler** - Auto-schedule L1 & L2 interviews
- 👻 **Anti-Ghosting Bot** - Keep candidates engaged during notice period  

---
👈 **Select a tool from the sidebar to get started!**
""")

# ============================================
# REAL-TIME METRICS FROM GOOGLE SHEETS
# ============================================
st.markdown("---")
st.subheader("📈 Quick Status")

# Load real data
@st.cache_data(ttl=60)
def load_data():
    connector = get_connector()
    return connector.get_all_candidates()

try:
    df = load_data()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Total", len(df))
    with col2:
        st.metric("🔍 Screening", len(df[df['Status'] == 'Screening']))
    with col3:
        st.metric("📞 L1 Scheduled", len(df[df['Status'] == 'L1_Scheduled']))
    with col4:
        st.metric("🎯 L2 Scheduled", len(df[df['Status'] == 'L2_Scheduled']))
    with col5:
        st.metric("✅ Offers", len(df[df['Status'].isin(['Offer_Sent', 'Offer_Accepted'])]))

except Exception as e:
    st.error(f"Could not load data: {e}")
    # Fallback to placeholder
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Candidates", "—")
    with col2:
        st.metric("In Screening", "—")
    with col3:
        st.metric("L1 Scheduled", "—")
    with col4:
        st.metric("Offers Sent", "—")