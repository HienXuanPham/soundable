import os
import re
import dramatiq
from io import BytesIO
import threading
import pyttsx3
from PyPDF2 import PdfReader


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
