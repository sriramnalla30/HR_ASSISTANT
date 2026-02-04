from groq import  Groq
import os 
from dotenv import load_dotenv

load_dotenv()

client=Groq()
def generate_engagement_message(candidate_name,candidate_role,day_number,company_name="TechCorp"):
    """
    Generates a personalized engagement message using Groq LLM.
    Args:
        candidate_name:Name of the candidate (e.g.,"Arjun Sharma")
        Candidate_role: Their job role (e.g.,"Backend Engineer")
        day_number: which day of hte 90-day notice period(1,7,30, etc..)
        company_name: Your Company Name
    
    Returns:
        dict with 'Subject' and 'Body' keys
    """

    prompt = f"""
    You are a friendly HR buddy writing engaging emails to candidates during their 90-day notice period.

    **Candidate Info:**
    - Name: {candidate_name} (use first name only)
    - Role: {candidate_role}
    - Company: {company_name}
    - Day: {day_number}/90

    **Tone Guide by Day:**
    - Day 1-7: 🎉 Celebratory! Welcome them warmly
    - Day 8-30: 📋 Helpful - share docs, blog, team culture
    - Day 31-60: 💻 Exciting - tech stack, projects, perks
    - Day 61-85: 📦 Practical - logistics, equipment, documents
    - Day 86-90: 🚀 Final countdown - Day 1 prep, excitement

    **Rules:**
    1. Start with "Subject: " on first line
    2. Keep body under 100 words
    3. Be warm and personal, not corporate
    4. Use 1-2 relevant emojis
    5. End with "{company_name} Team"
    6. Ask ONE engaging question to encourage reply
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile",  
        temperature=0.7,  # Some creativity but not too random
        max_tokens=300    # Keep response short
    )
    
    response_text = chat_completion.choices[0].message.content
    
    lines = response_text.strip().split('\n')
    
    subject = lines[0].replace("Subject:", "").strip()
    
    body_lines = [line for line in lines[1:] if line.strip()]
    body = '\n'.join(body_lines)
    
    return {
        "subject": subject,
        "body": body
    }
# =================================================
# TEST FUNCTION - Run this file directly to test
# =================================================
if __name__ == "__main__":
    # Test with sample data
    print("Testing AI Message Generator...")
    print("=" * 50)
    
    result = generate_engagement_message(
        candidate_name="Arjun Sharma",
        candidate_role="Backend Engineer",
        day_number=7
    )
    
    print(f"Subject: {result['subject']}")
    print("-" * 50)
    print(f"Body:\n{result['body']}")
