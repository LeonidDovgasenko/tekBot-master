from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Interval
from sqlalchemy.orm import relationship
from database.session import Base
from database.content_session import ContentBase
from datetime import datetime

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)  # Текст напоминания
    is_recurring = Column(Boolean, default=False)  # Повторяющееся ли напоминание
    interval = Column(String)  # Интервал для повторяющихся напоминаний (daily, weekly и т.д.)
    next_send = Column(DateTime)  # Следующее время отправки
    start_time = Column(DateTime, default=datetime.now)  # Время создания напоминания
    is_active = Column(Boolean, default=True)  # Активно ли напоминание
    
class Feedback(Base):
    __tablename__ = 'feedbacks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # ID пользователя в Telegram
    full_name = Column(String)  # Имя пользователя
    feedback_text = Column(Text)  # Текст отзыва
    created_at = Column(DateTime, default=datetime.now)  # Время создания
    
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

class User_info(Base):
    __tablename__ = "about_users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(50))
    mail = Column(String(127), nullable=True)
    office = Column(String(64), nullable=True)
    officephone = Column(String(20), nullable=True)

    username = Column(String(50), nullable=True)
    auth_token = Column(String(64), ForeignKey('users.auth_token'), unique=True)
    
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    auth_token = Column(String(64), ForeignKey('about_users.auth_token'), unique=True)
    hash_pass = Column(String(128))
    is_authorized = Column(Boolean)
    last_activity = Column(DateTime)
    user_info = relationship("User_info", foreign_keys=[auth_token], uselist=False)


    
class Authorized_users(Base):
    __tablename__ = "Authorized_users"
    
    id = Column(Integer, primary_key=True)
    auth_token = Column(String(64), ForeignKey('users.auth_token'), unique=True)
    
    user = relationship("User", foreign_keys=[auth_token], uselist=False)

class Admin(Base):
    __tablename__ = 'Admin'
    
    id = Column(Integer, primary_key=True)
    auth_token = Column(String(64), unique=True)


class Content(ContentBase):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    section = Column(String(50), unique=True)  # Например: history, values
    title = Column(String(100))
    text = Column(Text)

    files = relationship("ContentFile", back_populates="content")


class ContentFile(ContentBase):
    __tablename__ = "content_files"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey("content.id"))
    file_path = Column(String(255))

    content = relationship("Content", back_populates="files")
    
class FAQQuestion(ContentBase):
    __tablename__ = 'faq_questions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # ID пользователя, задавшего вопрос
    question = Column(Text, nullable=False)    # Текст вопроса
    answer = Column(Text)                      # Текст ответа (если есть)
    created_at = Column(DateTime, default=datetime.now)
    answered_at = Column(DateTime)             # Дата ответа
    
    # Отношение к файлам (если понадобится)
    # files = relationship("FAQFile", back_populates="question")

class CompanyTour(Base):
    __tablename__ = "company_tours"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    meeting_time = Column(DateTime)
    meeting_place = Column(String(255))
    max_participants = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)

    registrations = relationship("TourRegistration", back_populates="tour")

class TourRegistration(Base):
    __tablename__ = "tour_registrations"

    id = Column(Integer, primary_key=True)
    tour_id = Column(Integer, ForeignKey("company_tours.id"))
    user_auth_token = Column(String(64), ForeignKey("about_users.auth_token"))
    registered_at = Column(DateTime, default=datetime.now)

    tour = relationship("CompanyTour", back_populates="registrations")
    user = relationship("User_info", foreign_keys=[user_auth_token])
