
import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# Setup Streamlit UI
st.set_page_config(page_title="🧠 AI Web Scraper", layout="centered")
st.title("🔍Web Crawler ")

# Initialize chat memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar: File upload or URL input
st.sidebar.header("📂 Input Method")
input_mode = st.sidebar.radio("Choose content source:", ["Scrape from Website", "Upload HTML File"])

if input_mode == "Scrape from Website":
    url = st.text_input("🌐 Website URL", "https://quotes.toscrape.com/page/2/")
else:
    uploaded_file = st.sidebar.file_uploader("📄 Upload an HTML file", type=["html", "htm"])
    file_content = uploaded_file.read().decode("utf-8") if uploaded_file else ""

# User prompt and language
user_prompt = st.text_area("💬 Ask a question about the content:", "What does this say about bravery?")
target_language = st.selectbox("🌍 Translate response to:", ["English", "Hindi", "Spanish", "French", "German"])

submit = st.button("⚙️ Scrape & Ask")

# Logging area
status_placeholder = st.empty()

if submit:
    try:
        # Fetch or use file content
        if input_mode == "Scrape from Website":
            status_placeholder.info("🔄 Scraping website...")
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.get_text()
        else:
            status_placeholder.info("📄 Reading uploaded file...")
            soup = BeautifulSoup(file_content, "html.parser")
            content = soup.get_text()

        # Initialize Gemini model
        status_placeholder.info("🤖 Querying Gemini model...")
        gemini_model = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key="AIzaSyDPoLahoW16TVEAFaeIDjrSh9NcWX2wWwo"
        )

        # Multilingual prompt
        lang_prompt = {
            "English": "",
            "Hindi": "Give your final answer in Hindi.",
            "Spanish": "Give your final answer in Spanish.",
            "French": "Give your final answer in French.",
            "German": "Give your final answer in German."
        }

        mymsg = [
            {"role": "system", "content": f"You are an AI assistant that analyzes the following content: {content}"},
            {"role": "user", "content": user_prompt + ". " + lang_prompt[target_language]}
        ]

        # API call
        response = gemini_model.chat.completions.create(model="gemini-2.5-flash", messages=mymsg)
        result = response.choices[0].message.content

        # Store in chat memory
        st.session_state.chat_history.append(("You", user_prompt))
        st.session_state.chat_history.append(("AI", result))

        # Show response
        status_placeholder.success("✅ Done!")
        st.subheader("📄 AI Response:")
        st.write(result)

    except Exception as e:
        status_placeholder.error(f"❌ Error: {e}")

# Chat History Display
if st.session_state.chat_history:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Chat History")
    for role, message in st.session_state.chat_history[-6:][::-1]:  # Last 3 exchanges
        st.sidebar.markdown(f"**{role}:** {message}")
