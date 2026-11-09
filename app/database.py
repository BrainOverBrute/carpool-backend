from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = "postgresql+psycopg2://vaibhav:Vaibhav10@localhost:5432/postgres"
engine = create_engine(db_url)

session = sessionmaker(autoflush=False, bind=engine)