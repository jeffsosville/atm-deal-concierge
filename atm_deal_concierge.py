# atm_deal_concierge.py

import streamlit as st
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import os

# Load env vars locally (optional for local dev)
load_dotenv()

# Streamlit secrets (used for deployment)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Connect to OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Load listing data for Cape Cod (listing_id = 1)
listing_id = 1
listing_resp = supabase.table("listings").select("*").eq("id", listing_id).execute()
listing = listing_resp.data[0] if listing_resp.data else {}

# Load Q&A
qna_resp = supabase.table("questions_and_answers").select("*").eq("listing_id", listing_id).execute()
qna_data = qna_resp.data if qna_resp.data else []

# -------------------- UI --------------------
st.title("ATM Deal Concierge Agent")

st.subheader(f"{listing.get('title', 'ATM Listing')} – {listing.get('location', '')}")
st.markdown(f"**Asking Price:** ${listing.get('asking_price', 'N/A'):,}")
st.markdown(f"**Revenue:** ${listing.get('revenue', 'N/A'):,}")
st.markdown(f"**Net Profit:** ${listing.get('net_profit', 'N/A'):,}")
st.markdown(f"**Number of ATMs:** {listing.get('atm_count', 'N/A')}")

st.markdown("---")
st.subheader("Data Room Access")
st.text_input("Enter your email to check NDA status:")

st.markdown("---")
st.subheader("Ask the Concierge Agent")
user_q = st.text_input("What's your question about this listing?")

if user_q:
    # Try to answer from Supabase first
    best_match = None
    for row in qna_data:
        if user_q.lower() in row['question'].lower():
            best_match = row
            break

    if best_match:
        st.markdown("**Agent Response:**")
        st.success(best_match['answer'])
    else:
        # Use OpenAI fallback
        prompt = f"Answer this buyer question about ATMs or ATM routes: {user_q}"
        try:
            chat_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("**Agent Response (GPT fallback):**")
            st.success(chat_response.choices[0].message.content)
        except Exception as e:
            st.error("Agent failed to respond. Please try again.")
            st.exception(e)

# Uncomment this to show debug Q&A:
# if st.checkbox("Show sample Q&A"):
#     for row in qna_data[:5]:
#         st.markdown(f"**Q:** {row['question']}\n\n**A:** {row['answer']}")
