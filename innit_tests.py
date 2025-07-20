"""
Скрипт для инициализации таблиц тестов
"""

import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Используем ту же базу данных, что и для пользователей
# (укажите вашу реальную строку подключения)
DATABASE_URL = "sqlite:///database/users.db"  
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Определение моделей тестов
class Test(Base):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    section = Column(String)
    title = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class UserTestProgress(Base):
    __tablename__ = 'user_test_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    test_id = Column(Integer, ForeignKey('tests.id'))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

# 3. Функции инициализации
def create_tables():
    """Создает таблицы для тестовой системы"""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Таблицы тестов успешно созданы")
    except Exception as e:
        print(f"[ERROR] Ошибка создания таблиц тестов: {e}")
        raise

def add_sample_tests():
    """Добавляет примеры тестов"""
    db = SessionLocal()
    try:
        sample_tests = [
            {
                "section": "training_tests",
                "title": "Тест по технике безопасности",
                "url": "https://example.com/safety_test"
            },
            {
                "section": "training_tests",
                "title": "Тест по продуктам компании",
                "url": "https://example.com/products_test"
            }
        ]

        for test_data in sample_tests:
            if not db.query(Test).filter_by(title=test_data["title"]).first():
                db.add(Test(**test_data))
        
        db.commit()
        print("[OK] Тестовые данные добавлены")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ошибка добавления тестов: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    add_sample_tests()
    print("Инициализация тестов завершена успешно!")