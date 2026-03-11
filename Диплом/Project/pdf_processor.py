from PyPDF2 import PdfReader
import re


def process_info(file):
    with open(file, "rb") as f:
        reader = PdfReader(f)
        text = ''.join([page.extract_text() for page in reader.pages])
    # Служебная информация
    text = re.sub(r'ISSN\s+\d{4}-\d{3,4}[^\n]*', '', text)
    text = re.sub(r'\d{4};\d{2}\(\d+\):\d+–\d+', '', text)

    # Авторы
    text = re.sub(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][\.\s]+\s*[А-ЯЁ][\.\s]*', '', text)
    text = re.sub(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][\.\s]+\s*[А-ЯЁ][\.\s]*', '', text)
    text = re.sub(r'\d+[\s\w\.,–-]+(университет|институт|академия|центр)[^\n]*', '', text)

    # Сноски в квадратных скобках
    text = re.sub(r'\[\d+\]', '', text)  # [1], [2]
    text = re.sub(r'\[\d+[,-]\d+\]', '', text)  # [1-3], [4,5]
    text = re.sub(r'\[[A-Za-z]+\d*\]', '', text)  # [A1], [B]

    # email
    text = re.sub(r'\S+@\S+', '', text)

    # английские разделы
    text = re.sub(r'Abstract[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)
    text = re.sub(r'Keywords[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)
    text = re.sub(r'For citation[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)

    # ссылки
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'DOI:\s*\S+', '', text)

    # библиография
    text = re.sub(r'Список\s+источников[\s\S]*', '', text)
    text = re.sub(r'References[\s\S]*', '', text)

    # спец.символы
    text = text.replace('\xa0', ' ').replace('•', '')
    text = re.sub(r'-\s+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'•\s*\n', '', text)

    # оставшиеся английские фрагменты
    text = re.sub(r'(?:[A-Za-z-]+\s){3,}[A-Za-z-]*', '', text)

    return text
