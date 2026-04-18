import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "dbname": "Electronic_library_diplom",
    "user": "postgres",
    "password": "Turbo",
    "host": "localhost",
    "port": "5432"
}

CLASSES = ['Algo', 'Analysis', 'NN', 'Optim', 'SQL', 'Software_engineering',
           'CIS_design', 'Software_testing', 'Project_management', 'Philosophy', 'Python']


def create_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Подключение к PostgreSQL успешно")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None


def create_tables(conn):
    """Создаёт все таблицы."""
    with conn.cursor() as cur:
        # Таблица классов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Classes (
                class_id SERIAL PRIMARY KEY,
                class_name TEXT UNIQUE NOT NULL
            );
        """)

        # Таблица книг
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Books (
                book_id SERIAL PRIMARY KEY,
                title TEXT NOT NULL UNIQUE,
                num_pages INTEGER,
                class_id INTEGER REFERENCES Classes(class_id) ON DELETE SET NULL,
                author_name TEXT
            );
        """)

        # Таблица авторов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Authors (
                author_id SERIAL PRIMARY KEY,
                author_name TEXT NOT NULL UNIQUE
            );
        """)

        # Таблица связи книга-автор
        cur.execute("""
            CREATE TABLE IF NOT EXISTS BookAuthors (
                book_author_id SERIAL PRIMARY KEY,
                author_id INTEGER REFERENCES Authors(author_id) ON DELETE CASCADE,
                book_id INTEGER REFERENCES Books(book_id) ON DELETE CASCADE,
                UNIQUE(author_id, book_id)
            );
        """)

        for cls in CLASSES:
            cur.execute("""
                INSERT INTO Classes (class_name) VALUES (%s)
                ON CONFLICT (class_name) DO NOTHING;
            """, (cls,))

        conn.commit()
    print("✅ Все таблицы созданы / уже существуют, классы добавлены.")


def get_class_id(conn, class_name):
    """Возвращает class_id по имени класса."""
    with conn.cursor() as cur:
        cur.execute("SELECT class_id FROM Classes WHERE class_name = %s;", (class_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            raise ValueError(f"Класс '{class_name}' не найден в таблице Classes.")


def insert_article(conn, filename, class_name, num_pages=None, author_name=None):
    class_id = get_class_id(conn, class_name)
    with conn.cursor() as cur:
        cur.execute("""
                    INSERT INTO Books (title, num_pages, class_id, author_name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (title) DO UPDATE
                    SET num_pages = EXCLUDED.num_pages,
                        class_id = EXCLUDED.class_id,
                        author_name = EXCLUDED.author_name
                    RETURNING book_id;
                """, (filename, num_pages, class_id, author_name))
        book_id = cur.fetchone()[0]

        if author_name:
            try:
                cur.execute("""
                    INSERT INTO Authors (author_name) VALUES (%s)
                    ON CONFLICT (author_name) DO NOTHING;
                """, (author_name,))
                cur.execute("SELECT author_id FROM Authors WHERE author_name = %s;", (author_name,))
                author_row = cur.fetchone()
                if author_row:
                    author_id = author_row[0]
                    cur.execute("""
                        INSERT INTO BookAuthors (author_id, book_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (author_id, book_id))
            except Exception as e:
                conn.rollback()
                raise
        conn.commit()
