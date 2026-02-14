import streamlit as st
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(page_title="Viral Hook Generator", page_icon="🎣")

# 2. App Title and Branding
st.title("🎣 Viral Hook Generator")
st.write("Stop the scroll. Enter your topic to get 10 psychological hooks.")

# 3. Sidebar for API Key (Keeps it free/safe)
# Users input their own key OR you paste yours here for the hosted version.
# For a paid app, you would hardcode your key securely.
api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

if not api_key:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed. (Get one free from Google AI Studio)")
    st.stop()

# 4. Configure the AI
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 5. The Logic
topic = st.text_input("What is your video topic?", placeholder="e.g., How to lose weight without the gym")

if st.button("Generate Hooks"):
    if not topic:
        st.error("Please enter a topic!")
    else:
        with st.spinner("Generating viral hooks..."):
            try:
                # THE PROMPT FROM PHASE 1
                prompt = f"""
                You are an expert viral video scriptwriter. 
                Generate 10 distinct, high-converting hooks for the topic: '{topic}'.
                Use psychological frameworks like Negativity Bias, Curiosity Gap, and Immediate Value Promise.
                Format each hook as:
                - **Hook:** [Text]
                - **Why it works:** [Reason]
                - **Visual Cue:** [Instruction]
                """
                
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")