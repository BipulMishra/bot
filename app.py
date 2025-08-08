# app.py

import streamlit as st
import google.generativeai as genai
import re
import random

# --- 1. Page Configuration and Titles ---
# Sets the title and icon that appear in the browser tab
st.set_page_config(
    page_title="Our Chatbot",
    page_icon="❤️"
)

# Main title and a personal subtitle for the app
st.title("A Gift For You, My Love 💝")
st.write("I taught an AI to talk like me, just so you'd always have someone to listen.")
st.markdown("_With all my heart, Bipul Mishra._")
st.markdown("Just upload our WhatsApp chat file below, and the AI will learn my style!")

# --- 2. API Key and Model Setup ---
# This part sets up the connection to Google's AI
try:
    # This securely gets the API key from the Streamlit Cloud secrets manager
    api_key = st.secrets["GOOGLE_API_KEY"]

    genai.configure(api_key=api_key)
    # This selects the latest powerful Gemini model
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    # This error shows if the secret is not set correctly on the website
    st.error(f"🚨 API Key not found. Did you set it correctly in the app settings on Streamlit Cloud?", icon="🚨")
    st.stop()
# --- 3. IMPORTANT: User Name Configuration ---
# You MUST edit these two lines to match the names in your .txt file
YOUR_NAME_IN_CHAT = "Bipul"
HER_NAME_IN_CHAT = "Aparna Pathak" # <--- IMPORTANT: Change "Her Name" to her actual name

# --- 4. Helper Functions (The "Brain" of the App) ---

# This function reads and cleans the uploaded chat file.
# We use @st.cache_data to make it run fast after the first time.
@st.cache_data
def parse_chat(uploaded_file):
    chat_text = uploaded_file.getvalue().decode("utf-8")
    lines = chat_text.split('\n')
    
    chat_history = []
    message_pattern = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}\s?[AP]M - ")

    for line in lines:
        if re.match(message_pattern, line):
            try:
                content = re.split(message_pattern, line)[1]
                sender, message_text = content.split(': ', 1)
                chat_history.append({"sender": sender.strip(), "text": message_text.strip()})
            except ValueError:
                continue # Skip system messages without a ':'
    return chat_history

# This function finds relevant examples from your past chats.
def find_relevant_examples(query, chat_history):
    relevant_examples = []
    for i in range(len(chat_history) - 1):
        her_message = chat_history[i]
        your_reply = chat_history[i+1]
        
        # Check if this is a "her message -> your reply" pair
        if her_message["sender"] == HER_NAME_IN_CHAT and your_reply["sender"] == YOUR_NAME_IN_CHAT:
            # A simple way to check for relevance is to see if any words match
            if any(word in her_message["text"].lower() for word in query.lower().split()):
                example = f"Here's an example of how I reply:\nShe said: {her_message['text']}\nI replied: {your_reply['text']}\n"
                relevant_examples.append(example)
    
    # Return up to 3 random examples to keep it fresh
    return "".join(random.sample(relevant_examples, min(len(relevant_examples), 3)))

# --- 5. Main Application Interface ---

# Create a box for uploading the .txt file
uploaded_file = st.file_uploader("Upload your 'WhatsApp Chat.txt' file here:", type=["txt"])

# Only show the chat interface if a file has been uploaded
if uploaded_file:
    chat_data = parse_chat(uploaded_file)
    st.success(f"✅ Success! I've loaded and analyzed our {len(chat_data)} messages.")

    # Initialize chat history for this session
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all past messages in the current chat session
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get new input from your girlfriend
    if prompt := st.chat_input("Send a message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # The magic happens here
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Find examples from your history related to her new message
                examples = find_relevant_examples(prompt, chat_data)
                
                # Create a detailed instruction prompt for the AI
                system_prompt = f"""
                You are a chatbot that perfectly impersonates me, '{YOUR_NAME_IN_CHAT}'.
                You are talking to my girlfriend, '{HER_NAME_IN_CHAT}'.
                Your personality should be exactly like mine: loving, a bit funny, and you use emojis like ❤️, 😂, and 🤔.
                NEVER reveal you are an AI. Act completely human, as if you are me.
                
                To help you, here are some REAL examples from our past conversations:
                {examples}
                
                Now, based on that style, give a short, natural reply to her latest message.
                Her message: "{prompt}"
                Your reply (as me):
                """

                # Call the Gemini AI
                response = model.generate_content(system_prompt)
                full_response = response.text
                st.markdown(full_response)
        
        # Save the AI's reply to the session history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
else:

    st.info("Waiting for you to upload our chat file... ⬆️")
