import os
import re
import dramatiq
from io import BytesIO
import threading
import pyttsx3
from pypdf import PdfReader
from app import summarizer


def remove_pdf_content(pdf_content):
    if pdf_content:
        pdf_content = None


def remove_audio_file(audio_file_path):
    if audio_file_path and os.path.exists(audio_file_path):
        os.remove(audio_file_path)
        audio_file_path = None


def filter_text(text):
    # Remove chapter headings
    text = re.sub(r'Chapter \d+: [^\n]+\n?', '', text)
    # Remove dates in MM/DD/YY format
    text = re.sub(r'\d{2}/\d{2}/\d{2}', '', text)
    # Remove times in HH:MM AM/PM format
    text = re.sub(r'\d{1,2}:\d{2} [AP]M', '', text)
    # Remove page numbers in "Page x" format
    text = re.sub(r'Page \d+', '', text)

    return text


@dramatiq.actor
def convert_pdf_to_audio(pdf):
    bytes_file = BytesIO(pdf.read())
    reader = PdfReader(bytes_file)
    pdf_content = ""

    for page in reader.pages:
        pdf_content += page.extract_text()

    filtered_text = filter_text(pdf_content)

    # Convert text to audio
    tts_engine = pyttsx3.init()
    audio_file_path = os.path.join(os.getcwd(), "tts.mp3")
    tts_engine.save_to_file(filtered_text, audio_file_path)
    tts_engine.runAndWait()

    # Set timers to remove PDF content and audio file after 2 minutes
    pdf_timer = threading.Timer(
        120, remove_pdf_content, args=[pdf_content])
    audio_timer = threading.Timer(
        120, remove_audio_file, args=[audio_file_path])
    pdf_timer.start()
    audio_timer.start()

    return audio_file_path


@dramatiq.actor
def summarize_text(pdf):
    bytes_file = BytesIO(pdf.read())
    reader = PdfReader(bytes_file)
    text = ""

    for page_num, page in enumerate(reader.pages):
        try:
            pdf_content = page.extract_text()
            if pdf_content:
                text += pdf_content
            else:
                raise ValueError(f"No text extracted from page {page_num}")
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue  # skip to the next page if there's an issue

    print(len(text))
    summary = summarizer(text,  max_length=min(
        10000, len(text)), min_length=len(text), do_sample=False)
    summary_text = summary[0]["summary_text"]

    summary_text_file_path = os.path.join(os.getcwd(), "summary.txt")
    with open(summary_text_file_path, "w") as f:
        f.write(summary_text)

    return summary_text
