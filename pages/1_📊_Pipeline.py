import streamlit as st
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets_connector import get_connector

st.set_page_config(
    page_title="Pipeline Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pipeline Dashboard")
st.markdown("Manage your recruitment pipeline")

@st.cache_data(ttl=60)
def load_candidates():
    connector = get_connector()
    return connector.get_all_candidates()

df = load_candidates()

st.sidebar.header("🔍 Filters")

all_statuses = df['Status'].unique().tolist()
all_roles = df['Role'].unique().tolist()

selected_status = st.sidebar.selectbox(
    "Filter by Status",
    options=["All"] + all_statuses
)

selected_role = st.sidebar.selectbox(
    "Filter by Role",
    options=["All"] + all_roles
)

filtered_df = df.copy()
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
if selected_role != "All":
    filtered_df = filtered_df[filtered_df['Role'] == selected_role]

st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📋 Total", len(df))
with col2:
    st.metric("🔍 Screening", len(df[df['Status'] == 'Screening']))
with col3:
    st.metric("📞 L1 Scheduled", len(df[df['Status'] == 'L1_Scheduled']))
with col4:
    st.metric("✅ Offer Accepted", len(df[df['Status'] == 'Offer_Accepted']))
with col5:
    st.metric("👻 Ghosted", len(df[df['Status'] == 'Ghosted']))

st.markdown("---")
st.subheader(f"👥 Candidates ({len(filtered_df)})")

edited_df = st.data_editor(
    filtered_df,
    num_rows="fixed",
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=[
                "Screening",
                "L1_Scheduled", 
                "L1_Done",
                "L2_Scheduled",
                "Offer_Sent",
                "Offer_Accepted",
                "Joined",
                "Rejected",
                "Ghosted"
            ],
            required=True
        ),
        "Ghost_Risk": st.column_config.TextColumn("Ghost Risk")
    }
)

st.markdown("---")

if not df.equals(edited_df):
    st.warning("⚠️ You have unsaved changes!")
    
    if st.button("💾 Save Changes to Google Sheets"):
        connector = get_connector()
        changes_made = 0
        
        for index, row in edited_df.iterrows():
            original_row = df.loc[index]
            
            if row['Status'] != original_row['Status']:
                connector.update_candidate_status(
                    email=row['Email'],
                    new_status=row['Status']
                )
                changes_made += 1
        
        if changes_made > 0:
            st.success(f"✅ Saved {changes_made} change(s) to Google Sheets!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.info("No status changes detected.")

st.markdown("---")
st.subheader("📨 Pending Offers")

pending_offers = df[df['Status'] == 'Offer_Sent']

if len(pending_offers) == 0:
    st.info("📭 No pending offers. When candidates pass L2, they'll appear here.")
else:
    st.write("Candidates waiting for offer response:")
    
    for _, candidate in pending_offers.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{candidate['Name']}** - {candidate['Role']}")
            st.caption(f"📧 {candidate['Email']}")
        
        with col2:
            if st.button("✅ Accepted", key=f"accept_{candidate['Email']}"):
                connector = get_connector()
                connector.update_candidate_status(
                    email=candidate['Email'],
                    new_status="Offer_Accepted"
                )
                st.cache_data.clear()
                st.rerun()
        
        with col3:
            if st.button("❌ Declined", key=f"decline_{candidate['Email']}"):
                connector = get_connector()
                connector.update_candidate_status(
                    email=candidate['Email'],
                    new_status="Offer_Declined"
                )
                st.cache_data.clear()
                st.rerun()
        
        st.markdown("---")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
