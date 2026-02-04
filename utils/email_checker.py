import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime,timedelta
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PASSWORD=os.getenv("SMTP_PASSWORD")

def check_for_reply(from_email,since_minutes=60):
    """
    Checks Gmail inbox for emails From a specifi candidate
     
    Args:
        from_email: Candidate's email address to look for
        since_minutes: Only check emails from last X minutes (default: 60)
                      For demo, set to 1-2 minutes
    
    Returns:
        dict with 'found' (bool) and 'latest_reply_time' (datetime or None)
    """
    
    try:
        mail=imaplib.IMAP4_SSL("imap.gmail.com",993)
        mail.login(SMTP_EMAIL,SMTP_PASSWORD)
        mail.select("inbox")
        since_date = datetime.now() - timedelta(minutes=since_minutes)
        date_str = since_date.strftime("%d-%b-%Y") 
        search_criteria = f'(FROM "{from_email}" SINCE "{date_str}")'
        
        status, messages = mail.search(None, search_criteria)
        
        email_ids = messages[0].split()
        
        if len(email_ids) == 0:
            # No emails found from this candidate
            mail.logout()
            return {
                "found": False,
                "latest_reply_time": None,
                "message": f"No reply from {from_email} in last {since_minutes} minutes"
            }
        
        # Get the latest email (last in list)
        latest_id = email_ids[-1]
        
        # Fetch the email data
        status, msg_data = mail.fetch(latest_id, "(RFC822)")
        
        # Parse the email
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Get the date of the email
                date_str = msg["Date"]
                
                mail.logout()
                return {
                    "found": True,
                    "latest_reply_time": date_str,
                    "message": f"✅ Reply found from {from_email}!"
                }
        
        mail.logout()
        return {"found": False, "latest_reply_time": None}
        
    except Exception as e:
        return {
            "found": False,
            "latest_reply_time": None,
            "message": f"Error checking emails: {str(e)}"
        }

if __name__ == "__main__":
    print("Testing Email Checker...")
    print("=" * 50)
    
    test_email = "sriramnalla3009@gmail.com"  
    
    result = check_for_reply(
        from_email=test_email,
        since_minutes=60  
    )
    
    print(f"Found reply: {result['found']}")
    print(f"Message: {result.get('message', 'N/A')}")
