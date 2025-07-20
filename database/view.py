import sqlite3

# Подключаемся к БД
conn = sqlite3.connect('content.db')
cursor = conn.cursor()

# Получаем список таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Таблицы в БД:")
for table in tables:
    print(f"\n--- Таблица: {table[0]} ---")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print("Колонки:")
    for col in columns:
        print(f" - {col[1]} ({col[2]})")

    cursor.execute(f"SELECT * FROM {table[0]}")
    rows = cursor.fetchall()
    print("\nДанные:")
    for row in rows[:5]:
        print(row)

conn.close()