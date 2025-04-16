import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def register(username, password):
    # 유저 중복 확인
    result = supabase.table("users").select("username").eq("username", username).execute()
    if len(result.data) > 0:
        return False  # 이미 존재

    supabase.table("users").insert({"username": username, "password": password}).execute()
    return True

def login(username, password):
    result = supabase.table("users").select("password").eq("username", username).execute()
    if len(result.data) == 0:
        return False
    return result.data[0]["password"] == password
