from pypdf import PdfReader
import re
from typing import Optional, List


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

    # Email
    text = re.sub(r'\S+@\S+', '', text)

    # Английские разделы
    text = re.sub(r'Abstract[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)
    text = re.sub(r'Keywords[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)
    text = re.sub(r'For citation[^\n]*[\s\S]*?(?=\n[А-ЯЁ]|$)', '', text)

    # Ссылки
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'DOI:\s*\S+', '', text)

    # Библиография
    text = re.sub(r'Список\s+источников[\s\S]*', '', text)
    text = re.sub(r'References[\s\S]*', '', text)

    # Спец.символы
    text = text.replace('\xa0', ' ').replace('•', '')
    text = re.sub(r'-\s+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'•\s*\n', '', text)

    # Оставшиеся английские фрагменты
    text = re.sub(r'(?:[A-Za-z-]+\s){3,}[A-Za-z-]*', '', text)

    return text


def get_num_pages(file_path):
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        return len(reader.pages)

def get_author_from_metadata(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            # Проверяем, существует ли метаданные и есть ли в них автор
            if reader.metadata and reader.metadata.author:
                # Приводим к обычной строке
                return str(reader.metadata.author)
    except Exception as e:
        print(f"Не удалось прочитать метаданные PDF: {e}")
    return None


def extract_authors_from_filename(filename: str) -> Optional[List[str]]:
    name = re.sub(r'\.(pdf|PDF)$', '', filename)

    # 1. Поиск явного разделителя
    separators = r'\s*[-–—]\s*|\s+[-–—]\s+|_'
    parts = re.split(separators, name, maxsplit=1)
    if len(parts) >= 2:
        author_part = parts[0].strip()
        if author_part and _looks_like_author(author_part):
            return _parse_authors(author_part)

    # 2. Нет разделителя, значит ищем автора в начале строки по шаблону
    ru_pattern = r'^([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.(?:\s*[А-ЯЁ]\.)?)\s+(.*)$'
    en_pattern = r'^([A-Z][a-z]+\s+[A-Z]\.(?:\s*[A-Z]\.)?)\s+(.*)$'

    for pattern in [ru_pattern, en_pattern]:
        match = re.match(pattern, name)
        if match:
            author_part = match.group(1).strip()
            if _looks_like_author(author_part):
                return _parse_authors(author_part)

    return None


def _looks_like_author(text: str) -> bool:
    if not text or text[0].isdigit():
        return False
    if not re.search(r'[А-ЯA-Z]', text):
        return False
    if '.' not in text and ' ' not in text:
        return False
    if len(text) < 3:
        return False

    blacklist = r'библиотек|журнал|код|учебник|пособие|статья|лекция|курс|пример|глава|раздел'
    if re.search(blacklist, text, re.IGNORECASE):
        return False
    return True


def _parse_authors(author_part: str) -> List[str]:
    authors_raw = re.split(r'\s*[,;]\s*|\s+и\s+|\s+&\s+', author_part)
    authors = []
    for raw in authors_raw:
        raw = raw.strip().replace('_', ' ')
        if raw and re.search(r'[А-ЯA-Z][а-яa-z]*\s*[\.]?\s*[А-ЯA-Z]?\.?', raw):
            authors.append(raw)
    return authors

def extract_author(file_path: str, filename: str) -> str | None:
    # 1. Пробуем взять из метаданных PDF
    author = get_author_from_metadata(file_path)
    if author:
        return author

    # 2. Если не сработало, то извлекаем из имени файла
    authors_from_filename = extract_authors_from_filename(filename)
    if authors_from_filename:
        return authors_from_filename[0]

    # 3. Если ничего не найдено, возвращаем None
    return None