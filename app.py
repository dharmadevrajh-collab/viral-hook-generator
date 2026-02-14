import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime, timedelta
import time
import hashlib

# Page config
st.set_page_config(
    page_title="Viral Hook Generator", 
    page_icon="🎣",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stButton button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF8C42 100%);
        color: white;
        font-weight: bold;
        width: 100%;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
    }
    .free-trial-badge {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    .paywall-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .hook-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ip TEXT UNIQUE,
                  trial_count INTEGER DEFAULT 0,
                  last_used DATE,
                  is_paid BOOLEAN DEFAULT 0,
                  email TEXT,
                  subscribed_date DATE)''')
    conn.commit()
    conn.close()

# Get user IP
def get_user_ip():
    try:
        return st.context.headers.get('X-Forwarded-For', '127.0.0.1').split(',')[0]
    except:
        return '127.0.0.1'

# Check trial status
def check_trial_status(ip):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT trial_count, last_used, is_paid FROM users WHERE ip=?", (ip,))
    result = c.fetchone()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if result:
        trial_count, last_used, is_paid = result
        # Reset if 30 days passed
        if last_used and datetime.strptime(last_used, '%Y-%m-%d') < datetime.now() - timedelta(days=30):
            trial_count = 0
            c.execute("UPDATE users SET trial_count=0, last_used=? WHERE ip=?", (today, ip))
            conn.commit()
            conn.close()
            return {'count': 0, 'is_paid': is_paid}
        conn.close()
        return {'count': trial_count, 'is_paid': is_paid}
    else:
        c.execute("INSERT INTO users (ip, trial_count, last_used) VALUES (?, ?, ?)",
                 (ip, 0, today))
        conn.commit()
        conn.close()
        return {'count': 0, 'is_paid': False}

# Update trial count
def update_trial_count(ip):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("UPDATE users SET trial_count = trial_count + 1, last_used = ? WHERE ip=?", (today, ip))
    conn.commit()
    conn.close()

# Mark as paid
def mark_as_paid(ip, email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("UPDATE users SET is_paid=1, email=?, subscribed_date=? WHERE ip=?", (email, today, ip))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# App header
st.title("🎣 Viral Hook Generator Pro")
st.markdown("Generate scroll-stopping hooks for TikTok, Reels, and YouTube Shorts")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/FF4B4B/ffffff?text=VIRAL+HOOKS", use_column_width=True)
    st.header("🔧 Settings")
    
    # API Key
    API_KEY = st.text_input("Enter your Gemini API Key", type="password", help="Get it from Google AI Studio")
    
    st.markdown("---")
    st.markdown("### 📊 Your Status")
    
    user_ip = get_user_ip()
    user_status = check_trial_status(user_ip)
    
    if user_status['is_paid']:
        st.success("⭐ Premium Member")
        st.balloons()
    else:
        remaining = 5 - user_status['count']
        if remaining > 0:
            st.info(f"🎁 Free Trials Left: {remaining}/5")
            st.progress(user_status['count']/5)
        else:
            st.error("🚫 Trials Exhausted - Upgrade to continue")

# PAYWALL SECTION
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/bJecN49sB0UPfno2QRafS00"  # YOUR STRIPE LINK HERE

can_use = user_status['is_paid'] or user_status['count'] < 5

if not can_use:
    st.markdown("""
    <div class='paywall-box'>
        <h1>🔒 Trials Exhausted</h1>
        <p style='font-size: 1.2rem;'>You've used all 5 free hook generations.</p>
        <h2 style='font-size: 2.5rem;'>$9/month</h2>
        <p style='margin: 2rem 0;'>Unlock unlimited access & premium features:</p>
        <div style='text-align: left; max-width: 300px; margin: 0 auto;'>
            ✓ Unlimited hook generations<br>
            ✓ 10+ psychological frameworks<br>
            ✓ Export to CSV<br>
            ✓ Priority support<br>
            ✓ Advanced analytics<br>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("💳 Upgrade Now - $9/month", type="primary", use_container_width=True):
            js = f"window.open('{STRIPE_PAYMENT_LINK}')"
            st.markdown(f'<script>{js}</script>', unsafe_allow_html=True)
            st.success("Opening payment page...")
    
    with st.expander("Already paid? Click here"):
        email = st.text_input("Email used for payment")
        if st.button("Verify Payment"):
            st.info("We'll verify and upgrade you within 24 hours. Email support@yourdomain.com if urgent.")
    
    st.stop()

# Main app (only runs if user has trials or paid)
if not API_KEY:
    st.warning("👆 Please enter your Gemini API Key in the sidebar")
    st.stop()

# Configure Gemini
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# App interface
st.markdown(f"<div class='free-trial-badge'>✨ You have {5 - user_status['count']} free generations remaining</div>", unsafe_allow_html=True)

# Topic input
topic = st.text_input(
    "What's your video topic?",
    placeholder="e.g., how to make money online, fitness tips, relationship advice",
    help="Be specific for better hooks"
)

# Options
col1, col2 = st.columns(2)
with col1:
    framework = st.selectbox(
        "Hook Style",
        ["Curiosity Gap", "Negativity Bias", "Us vs Them", "Immediate Value", "Storytelling", "Controversy"]
    )
with col2:
    tone = st.selectbox(
        "Tone",
        ["Professional", "Casual", "Urgent", "Humorous", "Inspirational"]
    )

# Generate button
if st.button("🎯 Generate Viral Hooks", type="primary", use_container_width=True):
    if not topic:
        st.error("Please enter a topic!")
    else:
        with st.spinner("🧠 Analyzing psychological triggers..."):
            try:
                # Update trial count for free users
                if not user_status['is_paid']:
                    update_trial_count(user_ip)
                
                # Enhanced prompt
                prompt = f"""You are an expert viral video scriptwriter. Generate 5 viral hooks for topic: '{topic}'

Style: {framework}
Tone: {tone}

For each hook:
1. Make it STOP THE SCROLL in first 3 seconds
2. Use psychological triggers
3. Keep under 10 words

Format EXACTLY:

🔴 Hook 1:
[hook text]

💡 Why it works:
[psychological reason]

📹 Visual:
[what to show on screen]

---
"""
                
                response = model.generate_content(prompt)
                
                # Display results
                st.success("✅ Generated 5 viral hooks!")
                
                # Split and display nicely
                hooks = response.text.split("---")
                for hook in hooks:
                    if hook.strip():
                        with st.container():
                            st.markdown(f"<div class='hook-card'>{hook}</div>", unsafe_allow_html=True)
                
                # Show countdown for free users
                if not user_status['is_paid']:
                    remaining = 5 - user_status['count'] - 1
                    if remaining > 0:
                        st.info(f"🎁 {remaining} free generations left. Upgrade for unlimited!")
                    else:
                        st.warning("⚠️ This was your last free generation! Upgrade to continue.")
                
            except Exception as e:
                st.error(f"Generation failed: {e}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for creators | [Terms](/) | [Privacy](/)")
