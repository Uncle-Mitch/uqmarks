import os
from sqlalchemy import create_engine, text
from sqlalchemy import Column, Integer, Text, TIMESTAMP, text, String
from sqlalchemy.ext.declarative import declarative_base


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
Base = declarative_base()

db = SQLAlchemy()

class Course(db.Model):
    __tablename__ = 'courses'
    code = db.Column(db.String(8), primary_key=True)
    semester = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    asmts = db.Column(db.Text)  # Changed to Text for consistency with SQLAlchemy

class SearchLogs(db.Model):
    __tablename__ = 'search_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ts = db.Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    code = db.Column(db.Text, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.Index('ix_search_logs_code_sem_year', 'code'),
    )
    __table_args__ = (
        db.Index('idx_search_logs_ts', 'ts'),
    )
    
def create_database(app):
    """
    Create all tables in the database if they don't already exist.
    """
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating database tables: {e}")

def get_sqlalchemy_engine():
    """Create and return an SQLAlchemy engine for PostgreSQL."""
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", 5432)

    # Create the database connection string
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)
