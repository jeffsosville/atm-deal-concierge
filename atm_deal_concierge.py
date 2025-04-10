import streamlit as st
from openai import OpenAI
from supabase import create_client

# Load secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("ATM Deal Concierge Agent")

listing_id = 1  # Default to Cape Cod listing

# Ask user for a question
user_question = st.text_input("Ask the Concierge Agent")

if user_question:
    # Step 1: Search Supabase for matching Q&A
    query = supabase.table("questions_and_answers").select("*").eq("listing_id", listing_id).execute()
    results = query.data

    # Step 2: Try to match question
    matched = None
    for row in results:
        if user_question.lower() in row["question"].lower():
            matched = row
            break

    if matched:
        st.markdown("**Agent Response:**")
        st.success(matched["answer"])
    else:
        st.markdown("**Agent Response (GPT fallback):**")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful ATM business broker assistant. Answer clearly and concisely."},
                {"role": "user", "content": user_question}
            ]
        )
        st.success(response.choices[0].message.content)
