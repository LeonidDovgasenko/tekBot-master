from your_database_module import Base, engine  # Base — базовый класс моделей, engine — движок БД

Base.metadata.create_all(bind=engine)