import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config.database import engine
from src.models.chat import Base as ChatBase
from src.models.session import Base as SessionBase

def init_database():
    try:
        # Drop existing tables
        ChatBase.metadata.drop_all(bind=engine)
        SessionBase.metadata.drop_all(bind=engine)
        
        # Create tables with new schema
        SessionBase.metadata.create_all(bind=engine)
        ChatBase.metadata.create_all(bind=engine)
        
        print("Database tables recreated successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    init_database() 