from app.database.connection import Base, engine


Base.metadata.create_all(bind=engine)


print("Database initialized")
