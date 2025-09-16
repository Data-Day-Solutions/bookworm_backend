import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Sign in user
email = "davidshaw1985@gmail.com"
password = "password123"

auth_response = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

# Check login success
if not auth_response.user:
    raise Exception("Authentication failed")

print("Logged in as:", auth_response.user.email)

# 2. Use authenticated session to insert a row
user_id = auth_response.user.id

# Your RLS-enabled table expects this structure
data = {"test_value": "The Gruffalo"}

# Insert the row
insert_response = supabase.table("test_table").insert(data).execute()

# Show response
print("Insert result:", insert_response)
