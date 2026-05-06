from src.classifier import ArticleClassifier
from pdf_processor import process_info, extract_authors_from_filename, get_num_pages
from db import create_connection, create_tables, insert_article
import os


def main():
    classifier = ArticleClassifier()
    print('Взяли классификатор')

    path = "D://ПРОГА/Проектики/Github/Electronic_library/Диплом/Данные/Тестовые/Литература. Философия"
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path, file)
        text = process_info(file_path)
        print('Обработали текст')

        class_name, time_spent = classifier.predict(text)
        print('Получили класс')

        # Извлечение автора и числа страниц
        authors = extract_authors_from_filename(file)
        author_name = authors[0] if authors else None
        num_pages = get_num_pages(file_path)

        conn = create_connection()
        if conn:
            create_tables(conn)
            insert_article(conn, file, class_name, num_pages, author_name)
            conn.close()

        print(f"\n{'=' * 50}\nФайл: {file}\nКласс: {class_name}\nВремя: {time_spent:.2f} сек")


if __name__ == "__main__":
    main()
