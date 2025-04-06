import streamlit as st
from together import Together
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
import PyPDF2
from pathlib import Path
import os

# Initialize Together API
client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")


# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text


# Function to summarize text with LLaMA via Together
def summarize_text(text):
    if len(text) > 6000:
        text = text[:6000]

    prompt = (
        "Please summarize the following document content into clear, structured study notes. "
        "Use bullet points, numbered lists, and headings where helpful. Focus on clarity and conciseness:\n\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents into notes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=2048,
    )

    return response.choices[0].message.content.strip()


# Save summary as PDF with ReportLab
def save_notes_to_pdf(notes, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []

    # Create custom styles
    styles = getSampleStyleSheet()

    # Create a style for headings (big, bold)
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12
    )

    # Create a style for normal text
    normal_style = styles['Normal']

    # Process the summary and add headings & normal text
    paragraphs = notes.split("\n")

    for paragraph in paragraphs:
        # If the paragraph starts with '##', treat it as a heading
        if paragraph.startswith("##"):
            # Remove '##' and treat the rest as a heading
            paragraph = paragraph[2:].strip()
            header = Paragraph(f"<b>{paragraph}</b>", heading_style)
            story.append(header)
        else:
            # Regular paragraph (normal text)
            normal_paragraph = Paragraph(paragraph, normal_style)
            story.append(normal_paragraph)

    # Build the PDF
    doc.build(story)


# UI with Streamlit
st.set_page_config(page_title="Notes Generator", layout="centered")
st.title("📓 Notes Generator")
st.write("Upload a PDF and get clean, structured summary notes.")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting and summarizing..."):
        raw_text = extract_text_from_pdf(uploaded_file)
        summary = summarize_text(raw_text)

        # Save to Downloads
        downloads_dir = Path.home() / "Downloads"
        output_path = downloads_dir / "summary_notes.pdf"
        save_notes_to_pdf(summary, str(output_path))

        st.success(f"✅ Summary saved to your Downloads folder as 'summary_notes.pdf'")

        # Also show download button in browser
        with open(output_path, "rb") as f:
            st.download_button(
                label="📥 Download Notes",
                data=f,
                file_name="summary_notes.pdf",
                mime="application/pdf"
            )

        # Optional preview
        st.subheader("📘 Preview:")
        st.text_area("Summary", summary, height=300)
