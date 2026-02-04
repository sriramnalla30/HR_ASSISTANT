import streamlit as st
import sys
import os
import pandas as pd
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets_connector import get_connector

st.set_page_config(
    page_title="Interview Scheduler",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Interview Scheduler")
st.markdown("Schedule and manage L1 & L2 interviews")

TIME_SLOTS = [
    "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"
]

@st.cache_data(ttl=30)
def load_candidates():
    connector = get_connector()
    return connector.get_all_candidates()

df = load_candidates()

screening_candidates = df[df['Status'] == 'Screening']
l1_scheduled = df[df['Status'] == 'L1_Scheduled']
l1_done = df[df['Status'] == 'L1_Done']
l2_scheduled = df[df['Status'] == 'L2_Scheduled']

def auto_schedule_candidates(candidates_df, interview_type="L1", start_date=None, start_time_slot=None):
    connector = get_connector()
    scheduled_count = 0
    
    date_col = f"{interview_type}_Date"
    time_col = f"{interview_type}_Time"
    
    unscheduled = candidates_df[
        (candidates_df[date_col].isna()) | (candidates_df[date_col] == '')
    ]
    
    if len(unscheduled) == 0:
        return 0
    
    if start_date is None:
        current_date = datetime.now().date()
    else:
        current_date = start_date
    
    connector_temp = get_connector()
    all_data = connector_temp.get_all_candidates()
    already_scheduled = all_data[
        (all_data['Status'] == f'{interview_type}_Scheduled') &
        (all_data[date_col] != '') &
        (all_data[date_col].notna())
    ]
    
    def get_taken_slots(date_str):
        date_candidates = already_scheduled[already_scheduled[date_col] == date_str]
        return date_candidates[time_col].tolist()
    
    if start_time_slot:
        start_index = TIME_SLOTS.index(start_time_slot)
        filtered_slots = TIME_SLOTS[start_index:]
    else:
        filtered_slots = TIME_SLOTS

    for _, candidate in unscheduled.iterrows():
        date_str = current_date.strftime("%Y-%m-%d")
        
        taken_slots = get_taken_slots(date_str)
        available_slot = None
        
        for slot in filtered_slots:
            if slot not in taken_slots:
                available_slot = slot
                break
        
        while available_slot is None:
            current_date += timedelta(days=1)
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)
            
            date_str = current_date.strftime("%Y-%m-%d")
            taken_slots = get_taken_slots(date_str)
            
            for slot in filtered_slots:
                if slot not in taken_slots:
                    available_slot = slot
                    break
        
        connector.update_candidate_status(
            email=candidate['Email'],
            new_status=f"{interview_type}_Scheduled",
            additional_updates={
                date_col: date_str,
                time_col: available_slot
            }
        )
        
        already_scheduled = pd.concat([
            already_scheduled,
            pd.DataFrame([{date_col: date_str, time_col: available_slot}])
        ], ignore_index=True)
        
        time.sleep(1)
        scheduled_count += 1
    
    return scheduled_count

st.sidebar.header("⚙️ Scheduler Controls")

selected_date = st.sidebar.date_input(
    "📅 View Date",
    value=datetime.now().date()
)
selected_date_str = selected_date.strftime("%Y-%m-%d")

st.sidebar.markdown("---")
st.sidebar.subheader("📅 L1 Schedule Settings")

l1_start_date = st.sidebar.date_input(
    "Start L1 Interviews From",
    value=datetime.now().date(),
    key="l1_start"
)
l1_start_time = st.sidebar.selectbox(
    "Start From Time Slot",
    options=TIME_SLOTS,
    key="l1_start_time"
)

if st.sidebar.button("📋 Schedule L1 Interviews"):
    st.cache_data.clear()
    fresh_connector = get_connector()
    fresh_df = fresh_connector.get_all_candidates()
    fresh_screening = fresh_df[fresh_df['Status'] == 'Screening']
    
    count = auto_schedule_candidates(fresh_screening, "L1", start_date=l1_start_date, start_time_slot=l1_start_time)
    if count > 0:
        st.sidebar.success(f"✅ Scheduled {count} L1 interviews!")
        st.rerun()
    else:
        st.sidebar.info("No candidates to schedule")

st.sidebar.markdown("---")
st.sidebar.subheader("📅 L2 Schedule Settings")

l2_start_date = st.sidebar.date_input(
    "Start L2 Interviews From",
    value=datetime.now().date(),
    key="l2_start"
)
l2_start_time = st.sidebar.selectbox(
    "Start From Time Slot",
    options=TIME_SLOTS,
    key="l2_start_time"
)

if st.sidebar.button("📋 Schedule L2 Interviews"):
    st.cache_data.clear()
    fresh_connector = get_connector()
    fresh_df = fresh_connector.get_all_candidates()
    fresh_l1_done = fresh_df[fresh_df['Status'] == 'L1_Done']
    
    count = auto_schedule_candidates(fresh_l1_done, "L2", start_date=l2_start_date, start_time_slot=l2_start_time)
    if count > 0:
        st.sidebar.success(f"✅ Scheduled {count} L2 interviews!")
        st.rerun()
    else:
        st.sidebar.info("No candidates to schedule")

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Reset (Demo Only)")

if st.sidebar.button("⚠️ Reset All to Screening"):
    st.cache_data.clear()
    connector = get_connector()
    fresh_df = connector.get_all_candidates()
    
    all_to_reset = fresh_df[fresh_df['Status'].isin([
        'L1_Scheduled', 'L1_Done', 'L2_Scheduled', 
        'Rejected', 'Offer_Sent', 'Offer_Accepted', 'Offer_Declined'
    ])]
    
    if len(all_to_reset) == 0:
        st.sidebar.info("Nothing to reset!")
    else:
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        
        total = len(all_to_reset)
        
        for i, (_, candidate) in enumerate(all_to_reset.iterrows()):
            status_text.text(f"Resetting {candidate['Name']}...")
            
            connector.update_candidate_status(
                email=candidate['Email'],
                new_status="Screening",
                additional_updates={
                    "L1_Date": "",
                    "L1_Time": "",
                    "L1_Result": "",
                    "L2_Date": "",
                    "L2_Time": "",
                    "L2_Result": "",
                    "Ghost_Risk": "10"
                }
            )
            
            progress_bar.progress((i + 1) / total)
            time.sleep(1)
        
        status_text.text("Done!")
        st.sidebar.success(f"✅ Reset {total} candidates!")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

st.markdown("---")

tab1, tab2 = st.tabs(["📞 L1 Interviews", "🎯 L2 Interviews"])

with tab1:
    st.subheader(f"L1 Interviews - {selected_date.strftime('%A, %B %d, %Y')}")
    
    todays_l1 = df[
        (df['Status'] == 'L1_Scheduled') & 
        (df['L1_Date'] == selected_date_str)
    ]
    
    if len(todays_l1) == 0:
        st.info("📭 No L1 interviews scheduled for this date")
    else:
        st.markdown("### 📊 Timeline View")
        
        for time_slot in TIME_SLOTS:
            candidate_in_slot = todays_l1[todays_l1['L1_Time'] == time_slot]
            
            if len(candidate_in_slot) > 0:
                candidate = candidate_in_slot.iloc[0]
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**⏰ {time_slot}**")
                    
                    with col2:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 15px;
                            border-radius: 10px;
                            color: white;
                            margin: 5px 0;
                        ">
                            <strong>👤 {candidate['Name']}</strong><br>
                            <small>📧 {candidate['Email']}</small><br>
                            <small>💼 {candidate['Role']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("✅ Pass", key=f"pass_l1_{candidate['Email']}"):
                            connector = get_connector()
                            connector.update_candidate_status(
                                email=candidate['Email'],
                                new_status="L1_Done",
                                additional_updates={"L1_Result": "Pass"}
                            )
                            st.cache_data.clear()
                            st.rerun()
                    
                    with col4:
                        if st.button("❌ Fail", key=f"fail_l1_{candidate['Email']}"):
                            connector = get_connector()
                            connector.update_candidate_status(
                                email=candidate['Email'],
                                new_status="Rejected",
                                additional_updates={"L1_Result": "Fail"}
                            )
                            st.cache_data.clear()
                            st.rerun()
                    
                    st.markdown("---")
            else:
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.markdown(f"**⏰ {time_slot}**")
                    with col2:
                        st.markdown("""
                        <div style="
                            background: #2d2d2d;
                            padding: 15px;
                            border-radius: 10px;
                            color: #666;
                            margin: 5px 0;
                            border: 2px dashed #444;
                        ">
                            <em>📭 No interview scheduled</em>
                        </div>
                        """, unsafe_allow_html=True)

with tab2:
    st.subheader(f"L2 Interviews - {selected_date.strftime('%A, %B %d, %Y')}")
    
    todays_l2 = df[
        (df['Status'] == 'L2_Scheduled') & 
        (df['L2_Date'] == selected_date_str)
    ]
    
    if len(todays_l2) == 0:
        st.info("📭 No L2 interviews scheduled for this date")
    else:
        for time_slot in TIME_SLOTS:
            candidate_in_slot = todays_l2[todays_l2['L2_Time'] == time_slot]
            
            if len(candidate_in_slot) > 0:
                candidate = candidate_in_slot.iloc[0]
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**⏰ {time_slot}**")
                    
                    with col2:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                            padding: 15px;
                            border-radius: 10px;
                            color: white;
                            margin: 5px 0;
                        ">
                            <strong>👤 {candidate['Name']}</strong><br>
                            <small>📧 {candidate['Email']}</small><br>
                            <small>💼 {candidate['Role']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("✅ Pass", key=f"pass_l2_{candidate['Email']}"):
                            connector = get_connector()
                            connector.update_candidate_status(
                                email=candidate['Email'],
                                new_status="Offer_Sent",
                                additional_updates={"L2_Result": "Pass"}
                            )
                            st.cache_data.clear()
                            st.rerun()
                    
                    with col4:
                        if st.button("❌ Fail", key=f"fail_l2_{candidate['Email']}"):
                            connector = get_connector()
                            connector.update_candidate_status(
                                email=candidate['Email'],
                                new_status="Rejected",
                                additional_updates={"L2_Result": "Fail"}
                            )
                            st.cache_data.clear()
                            st.rerun()
                    
                    st.markdown("---")

st.markdown("---")
st.subheader("🎯 Passed L1 - Ready for L2 Scheduling")

passed_l1 = df[df['Status'] == 'L1_Done']

if len(passed_l1) > 0:
    st.dataframe(
        passed_l1[['Name', 'Email', 'Role', 'L1_Date', 'L1_Time', 'L1_Result']],
        use_container_width=True
    )
    st.info("👆 Click 'Schedule L2 Interviews' in sidebar to assign L2 slots")
else:
    st.info("📭 No candidates have passed L1 yet")