import streamlit as st
from google import genai

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title="Viral Hook Generator", page_icon="🎣")

st.title("🎣 Viral Hook Generator")
st.write("Stop the scroll. Enter your topic to get 10 psychological hooks.")

# ----------------------------
# API Key Input
# ----------------------------
api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

if not api_key:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

# Initialize Client
client = genai.Client(api_key=api_key)

# ----------------------------
# User Input
# ----------------------------
topic = st.text_input(
    "What is your video topic?",
    placeholder="e.g., How to lose weight without the gym"
)

# ----------------------------
# Generate Button Logic
# ----------------------------
if st.button("Generate Hooks"):
    if not topic:
        st.error("Please enter a topic!")
    else:
        with st.spinner("Generating viral hooks..."):
            try:
                prompt = f"""
You are an expert viral video scriptwriter specializing in TikTok and Instagram Reels. 
Your goal is to stop the scroll.

Generate 10 distinct, high-converting hooks for the topic: "{topic}"

For each hook, use one of these psychological frameworks:
1. The Negativity Bias
2. The Curiosity Gap
3. The 'Us vs Them' Narrative
4. The Immediate Value Promise

Format each hook as:
- **Hook:** [Text]
- **Why it works:** [Brief 5-word explanation]
- **Visual Cue:** [Instruction for screen action]
"""

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )

                st.markdown(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
