from src.classifier import ArticleClassifier
from pdf_processor import process_info
from src.db import create_connection, create_table, insert_article
import os

def main():
    # Создаём классификатор
    classifier = ArticleClassifier()
    print('Взяли классификатор')

    # Текст
    path = "D://ПРОГА/Проектики/Github/Electronic_library/Диплом/Данные/Тестовые/Литература. Философия"
    files = os.listdir(path)
    for file in files:
        text = process_info(path + '/' + file)
        print('Обработали текст')

        # Получаем результат
        class_name, time_spent = classifier.predict(text)
        print('Получили класс')

        # Добавляем результат в БД
        conn = create_connection()
        if conn:
            create_table(conn)
            insert_article(conn, file, class_name)
            conn.close()

        # Выводим
        print("\n" + "=" * 50)
        print(f"Время: {time_spent:.2f} сек")


if __name__ == "__main__":
    main()
