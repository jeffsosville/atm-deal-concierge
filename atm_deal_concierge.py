# atm_deal_concierge.py

import streamlit as st
from openai import OpenAI
import os
import requests
from datetime import datetime
from supabase import create_client, Client

# ---- Config ----
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# ---- Page Config ----
st.set_page_config(page_title="ATM Deal Concierge", layout="wide")

st.title("Cape Cod ATM Route – Deal Concierge Agent")

# ---- Load Listing Info ----
listing_id = 1  # Cape Cod hardcoded for now
listing_data = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data

if listing_data:
    st.subheader(f"{listing_data['title']} – {listing_data['location']}")
    st.markdown(f"**Asking Price:** ${listing_data['asking_price']:,.0f}")
    st.markdown(f"**Revenue:** ${listing_data['revenue']:,.0f}")
    st.markdown(f"**Net Profit:** ${listing_data['net_profit']:,.0f}")
    st.markdown(f"**Number of ATMs:** {listing_data['atm_count']}")

# ---- NDA Check ----
st.markdown("### Data Room Access")
user_email = st.text_input("Enter your email to check NDA status:")
nda_signed = False

if user_email:
    result = supabase.table("nda_signatures").select("*").eq("email", user_email).eq("listing_id", listing_id).execute().data
    if result:
        nda_signed = True
        st.success("NDA is on file. You may access the data room below.")
        st.markdown(f"[Access Google Drive Data Room]({listing_data['google_drive_link']})")
    else:
        st.warning("No NDA found for this listing. Please sign the NDA form to gain access.")

# ---- Chat with GPT ----
st.markdown("### Ask the Concierge Agent")

user_question = st.text_input("What's your question about this listing?")
if user_question:
    # Load Q&A pairs
    qa_data = supabase.table("questions_and_answers").select("*").eq("listing_id", listing_id).execute().data
    context = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_data])

    prompt = f"""
You are a helpful ATM Deal Concierge Agent. Answer the user's question using the listing info below and any preloaded Q&A.

Listing:
Title: {listing_data['title']}
Location: {listing_data['location']}
Asking Price: ${listing_data['asking_price']}
Revenue: ${listing_data['revenue']}
Net Profit: ${listing_data['net_profit']}
ATMs: {listing_data['atm_count']}

Preloaded Q&A:
{context}

User question: {user_question}
    """

    chat_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )

    answer = chat_response.choices[0].message.content.strip()
    st.markdown("**Agent Response:**")
    st.write(answer)

    # Optional: log chat
    supabase.table("chat_logs").insert({
        "listing_id": listing_id,
        "user_input": user_question,
        "agent_response": answer,
        "timestamp": datetime.now().isoformat()
    }).execute()
