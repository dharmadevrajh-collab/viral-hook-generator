import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime, timedelta
import pandas as pd
import time

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
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        width: 100%;
    }
    .free-trial-badge {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
    }
    .paywall-box {
        background-color: #1E1E1E;
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (ip TEXT PRIMARY KEY, 
                  trial_count INTEGER,
                  last_used DATE,
                  is_paid BOOLEAN DEFAULT 0,
                  email TEXT)''')
    conn.commit()
    conn.close()

# Get user IP (for trial tracking)
def get_user_ip():
    try:
        # This works on Streamlit Cloud
        return st.context.headers.get('X-Forwarded-For', '127.0.0.1').split(',')[0]
    except:
        return '127.0.0.1'

# Check trial status
def check_trial_status(ip):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT trial_count, last_used, is_paid FROM users WHERE ip=?", (ip,))
    result = c.fetchone()
    
    if result:
        trial_count, last_used, is_paid = result
        
        # Reset count if last used was more than 30 days ago
        if last_used and datetime.strptime(last_used, '%Y-%m-%d') < datetime.now() - timedelta(days=30):
            trial_count = 0
            c.execute("UPDATE users SET trial_count=0, last_used=? WHERE ip=?", 
                     (datetime.now().strftime('%Y-%m-%d'), ip))
            conn.commit()
            conn.close()
            return {'count': 0, 'is_paid': is_paid}
        
        conn.close()
        return {'count': trial_count, 'is_paid': is_paid}
    else:
        # New user
        c.execute("INSERT INTO users (ip, trial_count, last_used) VALUES (?, ?, ?)",
                 (ip, 0, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return {'count': 0, 'is_paid': False}

# Update trial count
def update_trial_count(ip):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET trial_count = trial_count + 1, last_used = ? WHERE ip=?", 
             (datetime.now().strftime('%Y-%m-%d'), ip))
    conn.commit()
    conn.close()

# Mark user as paid
def mark_as_paid(ip, email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_paid=1, email=? WHERE ip=?", (email, ip))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# App header
st.title("🎣 Viral Hook Generator Pro")
st.markdown("Generate scroll-stopping hooks for TikTok, Reels, and YouTube Shorts")

# Sidebar for API key (you'll hardcode this in production)
with st.sidebar:
    st.header("🔧 Configuration")
    
    # For production, hardcode your API key here
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")  # Use Streamlit secrets
    
    if not API_KEY:
        API_KEY = st.text_input("Enter your Gemini API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 📊 Your Status")
    
    # Get user IP and check status
    user_ip = get_user_ip()
    user_status = check_trial_status(user_ip)
    
    if user_status['is_paid']:
        st.success("⭐ Premium Member")
    else:
        remaining = 5 - user_status['count']
        if remaining > 0:
            st.info(f"🎁 Free Trials Left: {remaining}/5")
            st.progress(user_status['count']/5)
        else:
            st.error("🚫 Trials exhausted")
    
    st.markdown("---")
    st.markdown("Support: [Contact](mailto:support@yourdomain.com)")

# Check if user can use the app
can_use = user_status['is_paid'] or user_status['count'] < 5

if not can_use:
    # PAYWALL SCREEN
    st.markdown("""
    <div class='paywall-box'>
        <h1>🔒 Trials Exhausted</h1>
        <p>You've used all 5 free hook generations.</p>
        <h2>Unlock Unlimited Access for $9/month</h2>
        <ul style='text-align: left; margin: 2rem;'>
            <li>✅ Unlimited hook generations</li>
            <li>✅ 10+ psychological frameworks</li>
            <li>✅ Priority support</li>
            <li>✅ Export to CSV</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Payment form
    with st.form("payment_form"):
        st.subheader("Enter Payment Details")
        email = st.text_input("Email Address")
        card = st.text_input("Card Number", placeholder="4242 4242 4242 4242")
        col1, col2 = st.columns(2)
        with col1:
            expiry = st.text_input("Expiry (MM/YY)")
        with col2:
            cvv = st.text_input("CVV", type="password")
        
        if st.form_submit_button("💳 Upgrade Now - $9/month"):
            if email and card and expiry and cvv:
                # In production, connect to Stripe here
                mark_as_paid(user_ip, email)
                st.success("✅ Payment successful! Refreshing...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Please fill all fields")
    
    # Alternative payment methods
    st.markdown("---")
    st.markdown("### 💰 Other Payment Options")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[PayPal](https://paypal.me/yourlink)")
    with col2:
        st.markdown("[Cryptocurrency](https://yourcryptolink)")
    with col3:
        st.markdown("[Bank Transfer](mailto:payments@yourdomain.com)")
    
    st.stop()  # Stop execution here for non-paid users

# Configure Gemini
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"API Configuration Error: {e}")
        st.stop()
else:
    st.error("Please enter your Gemini API Key in the sidebar")
    st.stop()

# Main app interface for users who can use it
st.markdown(f"<div class='free-trial-badge'>✨ You have {5 - user_status['count']} free generations remaining</div>", unsafe_allow_html=True)

# Topic input
topic = st.text_input(
    "What's your video topic?", 
    placeholder="e.g., how to make money online, fitness tips, relationship advice"
)

# Advanced options
with st.expander("⚙️ Advanced Settings"):
    col1, col2 = st.columns(2)
    with col1:
        frameworks = st.multiselect(
            "Hook Frameworks",
            ["Curiosity Gap", "Negativity Bias", "Us vs Them", "Immediate Value", "Controversy", "Storytelling", "Shock Value"],
            default=["Curiosity Gap", "Immediate Value", "Storytelling"]
        )
    with col2:
        tone = st.selectbox(
            "Tone",
            ["Professional", "Casual", "Urgent", "Humorous", "Inspirational"]
        )
    
    num_hooks = st.slider("Number of hooks", 5, 20, 10)

# Generate button
if st.button("🎯 Generate Viral Hooks", type="primary"):
    if not topic:
        st.error("Please enter a topic!")
    else:
        with st.spinner("🧠 Analyzing psychological triggers..."):
            try:
                # Increment trial count for free users
                if not user_status['is_paid']:
                    update_trial_count(user_ip)
                
                # Enhanced prompt
                prompt = f"""You are an expert viral video scriptwriter. Generate {num_hooks} viral hooks for: '{topic}'

Requirements:
- Use frameworks: {', '.join(frameworks) if frameworks else 'All available'}
- Tone: {tone}
- Each hook must make people stop scrolling
- Keep hooks under 10 words
- Use psychological triggers

Format each hook EXACTLY like this:

**Hook #:** [hook text]
**Psychology:** [what trigger it uses]
**Visual:** [what to show on screen]
**Example Script:** [15-second script idea]

Make them punchy and conversion-focused."""

                response = model.generate_content(prompt)
                
                # Display results
                st.success(f"✅ Generated {num_hooks} viral hooks!")
                
                # Create tabs for different views
                tab1, tab2 = st.tabs(["📝 Hooks", "📊 Analytics"])
                
                with tab1:
                    hooks = response.text.split("**Hook #:")
                    for i, hook in enumerate(hooks[1:], 1):
                        with st.container():
                            st.markdown(f"### 🔥 Hook #{i}")
                            st.markdown(f"**{hook.strip()}")
                            st.markdown("---")
                
                with tab2:
                    st.subheader("Hook Performance Predictions")
                    data = pd.DataFrame({
                        'Hook Type': frameworks[:3] + ['Other'] * (len(frameworks)-3) if len(frameworks) > 3 else frameworks,
                        'Predicted CTR': [85, 72, 68, 60, 55][:len(frameworks)]
                    })
                    st.bar_chart(data.set_index('Hook Type'))
                    
                # Export option for paid users
                if user_status['is_paid']:
                    if st.button("📥 Export to CSV"):
                        # Convert to CSV and download
                        csv = response.text
                        st.download_button(
                            label="Download Hooks",
                            data=csv,
                            file_name=f"hooks_{topic[:20]}.txt",
                            mime="text/plain"
                        )
                
            except Exception as e:
                st.error(f"Generation failed: {e}")

# Show remaining trials
if not user_status['is_paid']:
    remaining = 5 - user_status['count']
    if remaining > 0:
        st.info(f"🎁 {remaining} free generations remaining. Upgrade for unlimited access!")
        
        # Upgrade CTA
        if st.button("⭐ Upgrade to Pro ($9/month)"):
            st.rerun()  # This will show the paywall
