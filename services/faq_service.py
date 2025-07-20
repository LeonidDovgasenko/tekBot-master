from database.content_session import ContentSessionLocal
from database.models import FAQQuestion
from datetime import datetime

def add_question(user_id: int, question: str):
    db = ContentSessionLocal()
    try:
        new_question = FAQQuestion(
            user_id=user_id,
            question=question
        )
        db.add(new_question)
        db.commit()
        return new_question
    finally:
        db.close()

def get_answered_questions():
    db = ContentSessionLocal()
    try:
        return db.query(FAQQuestion).filter(FAQQuestion.answer != None).all()
    finally:
        db.close()

def get_unanswered_questions():
    db = ContentSessionLocal()
    try:
        return db.query(FAQQuestion).filter(FAQQuestion.answer == None).all()
    finally:
        db.close()

def answer_question(question_id: int, answer: str):
    db = ContentSessionLocal()
    try:
        question = db.query(FAQQuestion).get(question_id)
        if question:
            question.answer = answer
            question.answered_at = datetime.now()
            db.commit()
            return True
        return False
    finally:
        db.close()

def delete_question(question_id: int):
    db = ContentSessionLocal()
    try:
        question = db.query(FAQQuestion).get(question_id)
        if question:
            db.delete(question)
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_question_by_id(question_id: int):
    db = ContentSessionLocal()
    try:
        return db.query(FAQQuestion).get(question_id)
    finally:
        db.close()