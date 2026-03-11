import streamlit as st
import tempfile
import os
from pathlib import Path

from src.classifier import ArticleClassifier
from db import create_connection, create_table, insert_article
from pdf_processor import process_info

# Настройка страницы
st.set_page_config(page_title="Классификация книг", layout="centered")
st.title("📚 Классификация книг")
st.markdown("Загрузите PDF-файл статьи, и модель определит её тематику и сохранит результат в базу данных.")


# Кэширование классификатора (загружается один раз)
@st.cache_resource
def load_classifier():
    with st.spinner("Загрузка модели..."):
        clf = ArticleClassifier()
    return clf


classifier = load_classifier()

# Загрузка файла
uploaded_file = st.file_uploader("Выберите PDF-файл", type=["pdf"])

if uploaded_file is not None:
    if st.button("Классифицировать и сохранить в БД"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            status_text.text("Извлечение текста из PDF...")
            progress_bar.progress(20)
            text = process_info(tmp_path)

            status_text.text("Классификация...")
            progress_bar.progress(50)
            class_name, time_spent = classifier.predict(text)

            status_text.text(f"Получен класс: {class_name}. Сохранение в БД...")
            progress_bar.progress(80)

            # Подключение к БД и сохранение
            conn = create_connection()
            if conn:
                create_table(conn)
                filename = uploaded_file.name  # используем имя файла как уникальный идентификатор
                insert_article(conn, filename, class_name)
                conn.close()
                status_text.text("✅ Готово!")
                progress_bar.progress(100)

                st.success(f"Статья отнесена к классу: **{class_name}**")
                st.info(f"Время обработки: {time_spent:.2f} сек")
            else:
                st.error("Ошибка подключения к базе данных.")
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
        finally:
            # Удаляем временный файл
            os.unlink(tmp_path)