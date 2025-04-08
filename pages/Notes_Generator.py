import streamlit as st
import PyPDF2
import re
import os
import requests
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import textwrap
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import google.auth
from together import Together

# === API Key (keep this safe in production!) ===
client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")

# === Google Drive Authentication ===
CLIENT_SECRET_FILE = '/Users/ayeshabuland/Downloads/client_secret.json'  # Path to your credentials.json file
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds, _ = google.auth.load_credentials_from_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service

def upload_to_google_drive(file_path):
    drive_service = authenticate_google_drive()
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return f"✅ PDF uploaded to Google Drive with file ID: {file.get('id')}"

# === Notion API Setup ===
NOTION_TOKEN = "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"  # Replace with your Notion integration token
NOTION_DATABASE_ID = "your_notion_database_id"  # Replace with your Notion database ID

def upload_to_notion(title, content):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2021-05-13"
    }
    data = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Name": { "title": [{ "text": { "content": title } }] },
            "Content": { "rich_text": [{ "text": { "content": content } }] }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return "✅ Note uploaded to Notion successfully!"
    else:
        return f"⚠️ Error uploading to Notion: {response.text}"

# === Helper Functions ===

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def slugify(text):
    return re.sub(r'\W+', '_', text.lower()).strip('_')

def extract_title(notes_text):
    lines = notes_text.strip().split('\n')
    for line in lines:
        if line.strip():
            return re.sub(r'#*', '', line).strip()
    return "untitled_notes"

def wrap_text(text, width=90):
    wrapped_lines = []
    for line in text.split('\n'):
        wrapped_lines.extend(textwrap.wrap(line, width=width) or [""])
    return wrapped_lines

def save_notes_to_pdf(notes_text):
    title = extract_title(notes_text)
    filename = slugify(title) + ".pdf"
    output_path = Path("~/Downloads").expanduser() / filename

    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    y = height - 72  # top margin

    # Wrap the text
    wrapped_lines = wrap_text(notes_text)

    for line in wrapped_lines:
        # Check if line contains '##' to interpret as bold
        if line.strip().startswith('##'):
            c.setFont("Helvetica-Bold", 14)
            line = line.strip().replace('##', '').strip()  # Remove the '##' symbols
        else:
            c.setFont("Helvetica", 11)

        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = height - 72

    c.save()
    return output_path

def generate_notes(text):
    system_prompt = {
        "role": "system",
        "content": (
            "Make clean, neat, and intuitive notes using bullet lists and different headers."
        )
    }

    user_prompt = {"role": "user", "content": text}

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[system_prompt, user_prompt],
        temperature=0.3,
        max_tokens=2048,
    )

    return response.choices[0].message.content.strip()

# === Streamlit App ===

st.title("📘 AI Notes Generator")
st.write("Upload a PDF to generate smart notes using AI, then edit and save it as a PDF to your Downloads folder.")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    with st.spinner("📖 Extracting text..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    if raw_text:
        with st.spinner("Summarizing notes using Meta LLaMA..."):
            notes = generate_notes(raw_text)

        st.subheader("📝 Edit Your Notes")
        edited_notes = st.text_area("Make edits below before saving:", value=notes, height=400, key="editable_notes")

        if st.button("📄 Generate PDF"):
            path = save_notes_to_pdf(edited_notes)
            st.success(f"✅ PDF saved to your Downloads folder: {path}")

        # Upload to Notion button
        if st.button("📤 Upload to Notion"):
            title = extract_title(edited_notes)  # Get title from notes
            upload_message = upload_to_notion(title, edited_notes)
            st.success(upload_message)

        # Upload to Google Drive button
        if st.button("☁️ Upload to Google Drive"):
            pdf_path = save_notes_to_pdf(edited_notes)  # Generate PDF
            upload_message = upload_to_google_drive(pdf_path)  # Upload to Google Drive
            st.success(upload_message)
    else:
        st.warning("⚠️ No text found in the PDF. It might be a scanned image.")

# === Chatbot Section ===
st.subheader("💬 Ask a Follow-up Question")

# Initialize a session state for chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []  # Store the chat history (messages from both user and assistant)


# Function to handle sending messages and getting responses from the model
def chat_response(user_message):
    # System prompt to set up the behavior of the assistant
    system_prompt = {
        "role": "system",
        "content": "You are a helpful and friendly assistant who answers questions about study notes and related content."
    }

    # User prompt based on the input message
    user_prompt = {"role": "user", "content": user_message}

    # Make a request to the LLaMA model with the entire chat history
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",  # Using LLaMA model
        messages=[system_prompt, *st.session_state['messages'], user_prompt],  # Include previous conversation context
        temperature=0.7,  # Adjust response creativity
        max_tokens=2048,  # Limit the length of the response
    )

    # Extract and clean the response
    answer = response.choices[0].message.content.strip()

    # Update the chat history with the user message and assistant's response
    st.session_state['messages'].append(user_prompt)
    st.session_state['messages'].append({"role": "assistant", "content": answer})

    return answer


# Create an input box for the user to ask questions
user_input = st.text_input("Ask a question about your notes:")

# Trigger the chat response when the user types a message
if user_input:
    with st.spinner("Generating response..."):
        answer = chat_response(user_input)  # Get the chatbot's response
        st.write(answer)  # Display the response
