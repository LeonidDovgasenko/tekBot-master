# init_content_db.py

"""
Скрипт для инициализации базы данных контента:
- Создание таблиц content и content_files
- Добавление начальных записей (если их нет)
"""

from database.models import Content, ContentFile
from database.content_session import ContentSessionLocal, ContentBase, content_engine
from sqlalchemy.orm import Session

def create_tables():
    """Создаёт все таблицы в БД, если они ещё не созданы"""
    try:
        ContentBase.metadata.create_all(bind=content_engine)
        print("[OK] Таблицы успешно созданы или уже существуют")
    except Exception as e:
        print(f"[ERROR] Не удалось создать таблицы: {e}")
        raise


def add_default_content(db: Session):
    """Добавляет стандартные разделы и опциональные файлы"""
    content_data = [
        {
            "section": "history",
            "title": "История компании",
            "text": "Это информация о истории компании ТЭК",
            "files": ["data/company_info/history.pdf"]
        },
        {
            "section": "values",
            "title": "Наши ценности",
            "text": "Это ценности компании ТЭК",
            "files": ["data/company_info/values.pdf"]
        }
    ]

    for item in content_data:
        existing = db.query(Content).filter(Content.section == item["section"]).first()
        if not existing:
            # Создаём новый раздел
            new_content = Content(
                section=item["section"],
                title=item["title"],
                text=item["text"]
            )
            db.add(new_content)
            db.flush()  # Чтобы получить ID перед добавлением файлов

            # Добавляем файлы, если указаны
            for file_path in item.get("files", []):
                db.add(ContentFile(content=new_content, file_path=file_path))

    try:
        db.commit()
        print("[INFO] Стандартный контент и файлы добавлены")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ошибка при добавлении контента: {e}")
        raise


if __name__ == "__main__":
    create_tables()
    db: Session = ContentSessionLocal()
    try:
        add_default_content(db)
    finally:
        db.close()