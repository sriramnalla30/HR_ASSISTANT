# 🚀 HR Assistant - Recruiters Assistant

An AI-powered recruitment management system built with Streamlit that helps HR teams manage the entire hiring pipeline, from screening to onboarding.

## ✨ Features

### 1. 📊 Pipeline Dashboard
- Visual Kanban board of all candidates
- Status tracking (Screening → L1 → L2 → Offer → Joined)
- Quick status updates with one click

### 2. 📅 Interview Scheduler
- Auto-scheduling of L1 and L2 interviews
- Gantt chart visualization
- Conflict-free time slot allocation
- 8 slots per day (9 AM - 5 PM)

### 3. 👻 Anti-Ghosting Bot
- Tracks candidates during notice period
- Auto-sends engagement emails
- Ghost Risk calculation based on response time
- HR email alerts when risk exceeds 40%
- AI-powered message generation (Groq API)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Database**: Google Sheets API
- **AI**: Groq API (LLaMA 3)
- **Email**: SMTP (Gmail)
- **Charts**: Plotly

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/sriramnalla30/HR_ASSISTANT.git
cd HR_ASSISTANT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
GOOGLE_CREDENTIALS_PATH=config/credentials.json
SHEET_NAME=RecruitmentData
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
GROQ_API_KEY=your-groq-api-key
```

4. Add your Google Sheets credentials:
- Create a service account in Google Cloud Console
- Download the JSON credentials
- Save as `config/credentials.json`

5. Run the application:
```bash
streamlit run app.py
```

## 📊 Google Sheet Structure

Your Google Sheet should have these columns:
| Column | Description |
|--------|-------------|
| Name | Candidate name |
| Email | Candidate email |
| Phone | Phone number |
| Role | Job role |
| Status | Current status |
| Applied_Date | Application date |
| L1_Date | L1 interview date |
| L1_Time | L1 interview time |
| L1_Result | L1 outcome |
| L2_Date | L2 interview date |
| L2_Time | L2 interview time |
| L2_Result | L2 outcome |
| Ghost_Risk | Ghosting risk percentage |
| Notes | Additional notes |

## 🎮 Demo Mode

The Anti-Ghosting Bot has a Demo Mode that:
- Uses 1-minute timer instead of 2 hours
- Auto-refreshes every 30 seconds
- Allows quick testing of the entire flow

## 📧 Email Features

- **Candidate Emails**: Engagement messages during notice period
- **HR Alerts**: Automatic notifications when Ghost Risk > 40%
- **AI Messages**: Groq-powered personalized content



---

Built with ❤️ by [Sriram Nalla](https://github.com/sriramnalla30)
