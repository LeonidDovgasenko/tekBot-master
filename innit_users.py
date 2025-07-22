from datetime import datetime

import pandas as pd
import secrets
import hashlib
from database.models import User, User_info, Admin, CompanyTour, TourRegistration
from database.session import SessionLocal, engine, Base
from database.models import Reminder

# 🔧 Создаем таблицы, если их ещё нет (включая Admin)
Base.metadata.create_all(bind=engine)

def add_default_tours():
    db = SessionLocal()
    if not db.query(CompanyTour).first():
        tours = [
            CompanyTour(
                title="Техническая экскурсия",
                description="Посещение завода и знакомство с производством",
                meeting_time=datetime(2025, 8, 1, 10, 0),
                meeting_place="Главный вход"
            ),
            CompanyTour(
                title="Офисная экскурсия",
                description="Знакомство с офисом и сотрудниками",
                meeting_time=datetime(2025, 8, 5, 15, 0),
                meeting_place="Ресепшн"
            )
        ]
        db.add_all(tours)
        db.commit()
        print("[INFO] Добавлены стандартные экскурсии")
    db.close()
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_unique_code() -> str:
    return secrets.token_urlsafe(8)


def import_employees_from_csv(csv_path: str):
    db = SessionLocal()

    # 🔍 Чтение CSV (разделитель — 2+ пробела, кодировка utf-16)
    df = pd.read_csv(csv_path, encoding='utf-16', sep=r'\s{2,}', engine='python')
    df.columns = df.columns.str.strip()  # удаляем пробелы в названиях колонок
    print("[DEBUG] Колонки:", df.columns.tolist())
    print(df.head())

    user_pwd = []

    for _, row in df.iterrows():
        name = row['name']
        mail = row['mail']
        office = row['office']
        officephone = row['officephone']

        auth_token = generate_unique_code()
        pwd = generate_unique_code()
        hashpass = hash_password(pwd)

        user_pwd.append({
            'auth_token': auth_token,
            'name': name,
            'pwd': pwd
        })

        # Добавляем запись User_info
        user_info = User_info(
            full_name=name,
            mail=mail,
            office=office,
            officephone=officephone,
            auth_token=auth_token
        )

        # Добавляем запись User
        user = User(
            auth_token=auth_token,
            hash_pass=hashpass,
            is_authorized=False
        )

        db.add(user_info)
        db.add(user)

        print(f"[{name}] Token: {auth_token}")

    # ✅ Добавляем админов (по TГ ID)
    admin_tokens = ['783002281', '5400694934', '1723977545', '1393336686']
    for token in admin_tokens:
        exists = db.query(Admin).filter_by(auth_token=token).first()
        if not exists:
            db.add(Admin(auth_token=token))
            print(f"[INFO] Добавлен админ с auth_token={token}")

    db.commit()
    db.close()

    # 💾 Сохраняем пароли пользователей в CSV
    new_df = pd.DataFrame(user_pwd)
    new_df.to_csv('data/user_passwords.csv', index=False, sep='\t', encoding='utf-8')


if __name__ == "__main__":
    csv_file = "data/users.csv"
    import_employees_from_csv(csv_file)
    add_default_tours()
