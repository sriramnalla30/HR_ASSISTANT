import streamlit as st
import sys
import os 
from datetime import datetime,timedelta
from streamlit_autorefresh import st_autorefresh

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets_connector import get_connector
from utils.email_sender import send_email
from utils.email_checker import check_for_reply
from utils.ai_message_generator import generate_engagement_message

st.set_page_config(
    page_title="Anti-Ghosting Bot",
    page_icon="👻",
    layout="wide"
)
st.title("👻 Anti-Ghosting Bot")
st.markdown("Keep candidates engaged during their notice period")

@st.cache_data(ttl=60)
def load_candidates():
    connector=get_connector()
    return connector.get_all_candidates()

df=load_candidates()

notice_period_candidates=df[df['Status']=='Offer_Accepted']

st.markdown("---")
st.subheader("📋 Candidates in Notice Period")
if len(notice_period_candidates) == 0:
    st.info("👻 No candidates in notice period currently. Change a candidate's status to 'Offer_Accepted' to see them here.")
else:
    st.dataframe(
        notice_period_candidates[['Name', 'Email', 'Role', 'Applied_Date']],
        width="stretch"
    )

# ============================================
# CANDIDATE SELECTION & TIME TRAVEL
# ============================================
if len(notice_period_candidates) > 0:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Controls")
    
    # 1. Select Candidate
    candidate_names = notice_period_candidates['Name'].tolist()
    selected_name = st.sidebar.selectbox("👤 Select Candidate", candidate_names)
    
    # Get selected candidate data
    candidate = notice_period_candidates[
        notice_period_candidates['Name'] == selected_name
    ].iloc[0]
    
    # 2. Time Travel Slider (Demo Feature)
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏳ Time Travel (Demo)")
    
    # Calculate days since offer accepted (mock if not present)
    # In real app, we'd use Offer_Accepted_Date from sheet
    # For now, we simulate day 0-90
    
    days_passed = st.sidebar.slider(
        "Days into Notice Period",
        min_value=0,
        max_value=90,
        value=15,
        format="Day %d"
    )
    
    # Demo Mode Timer
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏱️ Demo Settings")
    demo_mode = st.sidebar.checkbox("🧪 Demo Mode (1 min timer)", value=True)
    check_minutes = 1 if demo_mode else 120
    
    # Auto-Check Toggle
    auto_check = st.sidebar.checkbox("🔄 Auto-Check Responses", value=False)
    
    # Pause Alerts Toggle
    pause_alerts = st.sidebar.checkbox("⏸️ Pause HR Alerts", value=False)
    if pause_alerts:
        st.sidebar.warning("📧 HR emails paused!")
    
    # Reset tracking when Auto-Check is turned OFF
    if not auto_check:
        if 'auto_emails_sent' in st.session_state:
            st.session_state.auto_emails_sent = False
        if 'emailed_candidates' in st.session_state:
            st.session_state.emailed_candidates = set()
        if 'alerted_candidates' in st.session_state:
            st.session_state.alerted_candidates = set()
    
    # HR Email for notifications
    HR_EMAIL = "sriramnalla30@gmail.com"
    
    if auto_check:
        # Refresh every 30 seconds when auto-check is ON
        count = st_autorefresh(interval=30000, limit=100, key="auto_checker")
        st.sidebar.success(f"🔄 Auto-checking... (refresh #{count})")
        
        # Clear cache to get fresh data
        st.cache_data.clear()
        
        # Re-load fresh data
        connector = get_connector()
        fresh_df = connector.get_all_candidates()
        fresh_notice = fresh_df[fresh_df['Status']=='Offer_Accepted']
        
        # Initialize session state for tracking emailed candidates
        if 'emailed_candidates' not in st.session_state:
            st.session_state.emailed_candidates = set()
        
        # AUTO-SEND: When Auto-Check is first enabled, send emails to ALL candidates
        if 'auto_emails_sent' not in st.session_state:
            st.session_state.auto_emails_sent = False
        
        if not st.session_state.auto_emails_sent and len(fresh_notice) > 0:
            st.markdown("### 📨 Sending Initial Engagement Emails...")
            email_progress = st.progress(0)
            
            for i, (_, cand) in enumerate(fresh_notice.iterrows()):
                if cand['Name'] not in st.session_state.emailed_candidates:
                    # Send welcome email
                    try:
                        email_subject = "Welcome aboard! 🎉"
                        email_body = f"Hi {cand['Name'].split()[0]},\n\nWe are thrilled that you accepted our offer! The whole team is excited to have you join as a {cand['Role']}.\n\nLet us know if you have any questions!"
                        
                        send_email(
                            to_email=cand['Email'],
                            subject=email_subject,
                            body=email_body
                        )
                        st.session_state.emailed_candidates.add(cand['Name'])
                        st.success(f"✅ Email sent to {cand['Name']}")
                    except Exception as e:
                        st.error(f"❌ Failed to email {cand['Name']}: {e}")
                
                email_progress.progress((i + 1) / len(fresh_notice))
            
            st.session_state.auto_emails_sent = True
            st.info("📧 All candidates emailed! Now tracking responses...")
        
        # Auto-check ALL candidates for responses
        st.markdown("### 🔔 Auto-Check Results")
        ghosting_candidates = []
        responding_candidates = []
        waiting_candidates = []  # Candidates not yet emailed
        updated_risks = {}  # Track new risk values
        
        for _, cand in fresh_notice.iterrows():
            # ONLY check for reply if we've sent them an email
            if cand['Name'] not in st.session_state.emailed_candidates:
                waiting_candidates.append(cand['Name'])
                # Keep current risk (don't change)
                try:
                    risk_val = cand.get('Ghost_Risk', '')
                    current_risk = int(risk_val) if risk_val and str(risk_val).isdigit() else 10
                except:
                    current_risk = 10
                updated_risks[cand['Name']] = current_risk
                continue  # Skip to next candidate
            
            # Check for reply from emailed candidates
            result = check_for_reply(from_email=cand['Email'], since_minutes=check_minutes)
            if result['found']:
                responding_candidates.append(cand['Name'])
                updated_risks[cand['Name']] = 10
                # Reset ghost risk if responding
                connector.update_candidate_status(
                    email=cand['Email'],
                    new_status="Offer_Accepted",
                    additional_updates={"Ghost_Risk": "10"}
                )
            else:
                # Increase ghost risk
                try:
                    risk_val = cand.get('Ghost_Risk', '')
                    current_risk = int(risk_val) if risk_val and str(risk_val).isdigit() else 10
                except:
                    current_risk = 10
                new_risk = min(current_risk + 20, 100)
                ghosting_candidates.append(cand['Name'])
                updated_risks[cand['Name']] = new_risk
                connector.update_candidate_status(
                    email=cand['Email'],
                    new_status="Offer_Accepted",
                    additional_updates={"Ghost_Risk": str(new_risk)}
                )
        
        # Display results
        if waiting_candidates:
            st.info(f"📨 **Waiting for first email:** {', '.join(waiting_candidates)}")
        
        if responding_candidates:
            st.success(f"✅ **Responding:** {', '.join(responding_candidates)}")
        
        if ghosting_candidates:
            st.warning(f"⚠️ **No reply (potential ghost):** {', '.join(ghosting_candidates)}")
        
        # Only send HR Alert if any candidate has risk > 40%
        high_risk_candidates = []
        for name, risk in updated_risks.items():
            if risk > 40:
                high_risk_candidates.append(f"{name} ({risk}%)")
        
        # Initialize session state for tracking alerted candidates
        if 'alerted_candidates' not in st.session_state:
            st.session_state.alerted_candidates = set()
        
        if high_risk_candidates:
            st.error(f"🚨 **HIGH RISK (>40%):** {', '.join(high_risk_candidates)}")
            
            # Find NEW high-risk candidates (not already alerted)
            new_alerts = []
            for name, risk in updated_risks.items():
                if risk > 40 and name not in st.session_state.alerted_candidates:
                    new_alerts.append(f"{name} ({risk}%)")
                    st.session_state.alerted_candidates.add(name)
            
            # Send HR Alert Email ONLY for NEW high-risk candidates
            if new_alerts and not pause_alerts:
                alert_subject = "🚨 Ghost Alert: Candidates Need Immediate Attention!"
                alert_body = f"""
HR Alert - Anti-Ghosting Bot

⚠️ The following candidates have Ghost Risk ABOVE 40%:

{chr(10).join(['🔴 ' + name for name in new_alerts])}

Please follow up with them IMMEDIATELY to prevent ghosting.

---
This is an automated alert from the Recruiters Assistant.
                """
                
                try:
                    send_email(to_email=HR_EMAIL, subject=alert_subject, body=alert_body)
                    st.info(f"📧 Alert sent to HR ({HR_EMAIL}) for: {', '.join(new_alerts)}")
                except Exception as e:
                    st.error(f"Failed to send HR alert: {e}")
            elif new_alerts and pause_alerts:
                st.warning("⏸️ HR Alert PAUSED (not sent)")
            else:
                st.caption("ℹ️ HR already alerted for these candidates")
    
    # Reload fresh data for accurate display
    fresh_connector = get_connector()
    fresh_data = fresh_connector.get_all_candidates()
    fresh_candidates = fresh_data[fresh_data['Status']=='Offer_Accepted']
    
    # Get fresh candidate data for display
    if len(fresh_candidates[fresh_candidates['Name'] == selected_name]) > 0:
        candidate = fresh_candidates[fresh_candidates['Name'] == selected_name].iloc[0]
    
    # Display selected candidate info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"### 👤 {candidate['Name']}")
        st.caption(candidate['Role'])
        
    with col2:
        st.metric("📧 Email", candidate['Email'])
        
    with col3:
        # Ghost Risk - Read from sheet or calculate
        # Combines stored risk with time-based risk
        try:
            ghost_risk_value = candidate.get('Ghost_Risk', '')
            # Handle empty, None, or non-numeric values
            if ghost_risk_value and str(ghost_risk_value).isdigit():
                stored_risk = int(ghost_risk_value)
            else:
                stored_risk = 10  # Default risk
        except:
            stored_risk = 10
        
        # Add time-based risk bonus
        time_risk = 0
        if days_passed > 30: time_risk += 10
        if days_passed > 60: time_risk += 20
        if days_passed > 85: time_risk += 20
        
        total_risk = min(stored_risk + time_risk, 100)
        
        # Color coding risk
        risk_color = "green"
        if total_risk > 40: risk_color = "orange"
        if total_risk > 70: risk_color = "red"
        
        st.markdown(f'''<div style="text-align: center;"><p style="margin-bottom: 0px;">👻 Ghost Risk</p><h2 style="color: {risk_color}; margin-top: 0px;">{total_risk}%</h2></div>''', unsafe_allow_html=True)
        
    # ============================================
    # ENGAGEMENT TIMELINE
    # ============================================
    st.markdown("### 📅 Engagement Timeline")
    
    # Define touchpoints
    touchpoints = {
        1:  "🎉 Offer Accepted",
        7:  "📋 Onboarding Docs",
        30: "💬 Monthly Check-in",
        60: "🏢 Team Intro",
        85: "🚀 Pre-joining Prep",
        90: "🏁 Day 1 Joined"
    }
    
    # Determine current stage
    current_stage = None
    next_stage = None
    
    stages_html = ""
    
    for day, label in touchpoints.items():
        # Determine status of this stage
        status_color = "#e0e0e0"  # Default gray (future)
        opacity = 0.5
        
        if days_passed >= day:
            status_color = "#4CAF50"  # Green (completed)
            opacity = 1.0
            current_stage = label
        elif next_stage is None:
            status_color = "#2196F3"  # Blue (next up)
            opacity = 1.0
            next_stage = label
            
        stages_html += f'''<div style="flex: 1; text-align: center; opacity: {opacity}"><div style="width: 30px; height: 30px; background: {status_color}; border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{day}</div><div style="font-size: 12px;">{label}</div></div>'''
        
    st.markdown(f'''<div style="display: flex; justify-content: space-between; margin: 20px 0;">{stages_html}</div>''', unsafe_allow_html=True)
    
    # ============================================
    # MESSAGE PREVIEW
    # ============================================
    st.markdown("---")
    st.subheader("💬 Active Engagement")
    
    # Select message templates based on days passed
    message_subject = ""
    message_body = ""
    
    if days_passed <= 2:
        message_subject = "Welcome aboard! 🎉"
        message_body = f"Hi {candidate['Name'].split()[0]},\n\nWe are thrilled that you accepted our offer! The whole team is excited to have you join as a {candidate['Role']}.\n\nLet us know if you have any questions!"
    elif days_passed <= 10:
        message_subject = "Getting started: Documents 📋"
        message_body = f"Hi {candidate['Name'].split()[0]},\n\nTo make your Day 1 smooth, could you please review the attached onboarding documents?\n\nThis will save us a lot of time on your joining date!"
    elif days_passed <= 35:
        message_subject = "Checking in 👋"
        message_body = f"Hi {candidate['Name'].split()[0]},\n\nHope your notice period is going smoothly. How are things at your current workplace? Let us know if you need any support from our side."
    elif days_passed <= 65:
        message_subject = "Meet the team! 🏢"
        message_body = f"Hi {candidate['Name'].split()[0]},\n\nYour future team is having a virtual coffee chat next Friday. Would you like to join and meet everyone before your official start date?"
    else:
        message_subject = "Ready for launch? 🚀"
        message_body = f"Hi {candidate['Name'].split()[0]},\n\nJust a few days left! We have your laptop ready and your desk set up. Can't wait to see you on Monday!"

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"**Template Subject:** {message_subject}")
        
        # AI Generate Button
        if st.button("🤖 Generate AI Message"):
            with st.spinner("AI is writing your message..."):
                ai_message = generate_engagement_message(
                    candidate_name=candidate['Name'],
                    candidate_role=candidate['Role'],
                    day_number=days_passed,
                    company_name="TechCorp"
                )
                st.session_state['ai_subject'] = ai_message['subject']
                st.session_state['ai_body'] = ai_message['body']
        
        # Show AI generated or template message
        if 'ai_subject' in st.session_state:
            final_subject = st.text_input("Subject", value=st.session_state['ai_subject'])
            final_body = st.text_area("Message", value=st.session_state['ai_body'], height=200)
        else:
            final_subject = st.text_input("Subject", value=message_subject)
            final_body = st.text_area("Message", value=message_body, height=200)
        
        # Send Email Button
        if st.button("📨 Send Email"):
            try:
                send_email(
                    to_email=candidate['Email'],
                    subject=final_subject,
                    body=final_body
                )
                # Track that we emailed this candidate
                if 'emailed_candidates' not in st.session_state:
                    st.session_state.emailed_candidates = set()
                st.session_state.emailed_candidates.add(candidate['Name'])
                
                st.success(f"✅ Email sent to {candidate['Email']}!")
                st.info("⏱️ Ghost Risk tracking started for this candidate")
            except Exception as e:
                st.error(f"❌ Failed to send: {e}")
        
        # Check Response Button
        st.markdown("---")
        if st.button("🔍 Check for Reply"):
            with st.spinner(f"Checking inbox (last {check_minutes} min)..."):
                result = check_for_reply(
                    from_email=candidate['Email'],
                    since_minutes=check_minutes
                )
            
            if result['found']:
                st.success(f"✅ {result['message']}")
                st.balloons()
            else:
                st.warning(f"⏳ {result['message']}")
                st.info(f"Ghost Risk may increase if no reply in {check_minutes} minutes")
            
    with col2:
        st.markdown("### 🤖 Bot Status")
        st.write(f"⏱️ Response window: **{check_minutes} min**")
        st.write(f"📅 Day: **{days_passed}/90**")
        
        if demo_mode:
            st.success("🧪 Demo Mode: ON")
        else:
            st.info("🏭 Production Mode")
        
        # Show ghost risk status
        st.markdown("---")
        st.markdown("### 👻 Ghost Risk")
        try:
            risk_val = candidate.get('Ghost_Risk', '')
            current_risk = int(risk_val) if risk_val and str(risk_val).isdigit() else 10
        except:
            current_risk = 10
        
        risk_color = "green" if current_risk <= 40 else ("orange" if current_risk <= 70 else "red")
        st.markdown(f"<h2 style='color: {risk_color};'>{current_risk}%</h2>", unsafe_allow_html=True)
        
        if current_risk > 40:
            st.error("⚠️ HR will be alerted!")
        else:
            st.info(f"Alert threshold: >40%")
