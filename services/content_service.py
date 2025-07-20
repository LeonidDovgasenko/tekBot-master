from database.content_session import ContentSessionLocal
from database.models import Content, ContentFile
import os

def update_content(section: str, title: str = None, text: str = None):
    db = ContentSessionLocal()
    try:
        content = db.query(Content).filter(Content.section == section).first()
        if not content:
            content = Content(section=section, title=title, text=text)
            db.add(content)
        else:
            if title:
                content.title = title
            if text:
                content.text = text
        db.commit()
        db.refresh(content)
        return content
    finally:
        db.close()


def add_file_to_content(section: str, file_path: str):
    db = ContentSessionLocal()
    try:
        content = db.query(Content).filter(Content.section == section).first()
        if not content:
            content = Content(section=section)
            db.add(content)
            db.commit()

        new_file = ContentFile(file_path=file_path, content=content)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        return new_file
    finally:
        db.close()

def get_content_files(section: str):
    db = ContentSessionLocal()
    try:
        content = db.query(Content).filter(Content.section == section).first()
        if content:
            return content.files
        return []
    finally:
        db.close()

def delete_content_file(file_id: int):
    db = ContentSessionLocal()
    try:
        file_record = db.query(ContentFile).get(file_id)
        if file_record:
            file_path = file_record.file_path
            db.delete(file_record)
            db.commit()

            # Опционально: удалить физически файл с диска
            if os.path.exists(file_path):
                os.remove(file_path)

            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Не удалось удалить файл: {e}")
        return False
    finally:
        db.close()