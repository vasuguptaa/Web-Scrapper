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
        def extract_metadata(soup):
            metadata = {}
            for tag in soup.find_all("meta"):
                if tag.get("name"):
                    metadata[tag.get("name")] = tag.get("content", "")
                elif tag.get("property"):  # for og: and twitter: tags
                    metadata[tag.get("property")] = tag.get("content", "")
            return metadata

        def find_internal_links(base_url, soup):
            from urllib.parse import urljoin, urlparse
            parsed_base = urlparse(base_url)
            base_netloc = parsed_base.netloc
            links = set()
            for a in soup.find_all("a", href=True):
                full_url = urljoin(base_url, a['href'])
                if urlparse(full_url).netloc == base_netloc:
                    links.add(full_url)
            return list(links)

        def recursively_scrape_links(start_url, max_depth=1):
            visited = set()
            to_visit = [(start_url, 0)]
            all_text = []

            while to_visit:
                current_url, depth = to_visit.pop()
                if current_url in visited or depth > max_depth:
                    continue
                visited.add(current_url)
                try:
                    sub_resp = requests.get(current_url, timeout=5)
                    sub_soup = BeautifulSoup(sub_resp.text, "html.parser")
                    all_text.append(sub_soup.get_text())
                    if depth < max_depth:
                        new_links = find_internal_links(current_url, sub_soup)
                        to_visit.extend([(link, depth + 1) for link in new_links])
                except:
                    continue
            return "\n\n".join(all_text)

        if input_mode == "Scrape from Website":
            status_placeholder.info("🔄 Scraping website...")
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            metadata = extract_metadata(soup)
            content = recursively_scrape_links(url, max_depth=1)
        else:
            status_placeholder.info("📄 Reading uploaded file...")
            soup = BeautifulSoup(file_content, "html.parser")
            metadata = extract_metadata(soup)
            content = soup.get_text()

        # Initialize Gemini model
        status_placeholder.info("🤖 Querying Gemini model...")
        gemini_model = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key="Use your api key here"
# use your api key here
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
            {"role": "system", "content": f"You are an AI assistant that analyzes the following content: {content}\n\nHere is the page metadata: {metadata}"},
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
