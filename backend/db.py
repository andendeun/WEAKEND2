import sqlite3
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


# DB 초기화, 테이블 생성
def init_db():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            message TEXT,
            emotion TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


# DB에 대화 내용 저장
def save_message(user_id, role, message, emotion=""):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversations (user_id, role, message, emotion, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, role, message, emotion, datetime.now().isoformat()))
    conn.commit()
    conn.close()


# User 테이블 초기화, 생성
def init_user_table():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


# 지역 정보 등록
def get_region_list():
    try:
        response = supabase.table("region").select("region_name").execute()
        region_data = response.data
        return [r["region_name"] for r in region_data]
    except Exception as e:
        return []
