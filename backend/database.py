"""
nagarAI - backend/database.py
=============================
Sets up the Supabase client connection for use across pipelines.
"""

import os
from supabase import create_client, Client

# Load Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase URL/Key not set in environment variables")

# Create a global Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
