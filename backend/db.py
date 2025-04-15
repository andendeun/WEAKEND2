from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# DB 연결 (SQLite 파일 생성)
engine = create_engine("sqlite:///conversation.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# 대화 로그 테이블 정의
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    role = Column(String)  # user or assistant
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# 테이블 생성
Base.metadata.create_all(engine)

# 메시지 저장 함수
def save_message(username, role, message):
    new_msg = ChatLog(username=username, role=role, message=message)
    session.add(new_msg)
    session.commit()

# 메시지 조회 함수
def get_all_messages(username=None):
    if username:
        return session.query(ChatLog).filter_by(username=username).all()
    else:
        return session.query(ChatLog).all()
