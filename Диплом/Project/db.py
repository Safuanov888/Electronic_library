import psycopg2
from psycopg2 import sql, errors

### ТЕСТОВЫЕ ДАННЫЕ ЗАКАНЧИВАЮТСЯ НА 31 ID в БД ###

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
    """Устанавливает соединение с PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Подключение к PostgreSQL успешно")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None


def create_table(conn):
    """Создаёт таблицу с колонками для каждого класса."""

    columns_def = [sql.SQL("{} BOOLEAN DEFAULT FALSE").format(sql.Identifier(cls.lower())) for cls in CLASSES]
    columns_def.append(sql.SQL("filename TEXT NOT NULL UNIQUE"))

    create_query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            {columns}
        );
    """).format(
        columns=sql.SQL(', ').join(columns_def)
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_query)
            conn.commit()
        print("✅ Таблица 'articles' создана или уже существует")
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        conn.rollback()


def insert_article(conn, filename, class_name):
    """
    Добавляет или обновляет запись о статье.
    Для указанного класса ставит TRUE, для остальных оставляет FALSE.
    """
    # Приводим название класса к нижнему регистру для имени колонки
    class_column = class_name.lower()
    if class_column not in [c.lower() for c in CLASSES]:
        print(f"❌ Неизвестный класс: {class_name}")

    # Формируем словарь: все FALSE, кроме указанного класса
    data = {cls.lower(): (True if cls == class_name else False) for cls in CLASSES}
    data['filename'] = filename

    columns = sql.SQL(', ').join(map(sql.Identifier, data.keys()))
    values = sql.SQL(', ').join([sql.Placeholder()] * len(data))

    # ON CONFLICT обновляет только колонки классов (filename не меняется)
    update_set = sql.SQL(', ').join([
        sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(k), sql.Identifier(k))
        for k in data.keys() if k != 'filename'
    ])

    query = sql.SQL("""
        INSERT INTO articles ({columns})
        VALUES ({values})
        ON CONFLICT (filename) DO UPDATE SET {update_set}
    """).format(
        columns=columns,
        values=values,
        update_set=update_set
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, list(data.values()))
            conn.commit()
        print(f"✅ Статья '{filename}' отнесена к классу '{class_name}'")
    except Exception as e:
        print(f"❌ Ошибка вставки: {e}")
        conn.rollback()
