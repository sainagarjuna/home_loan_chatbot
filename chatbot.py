import streamlit as st
import pandas as pd
import numpy as np
import requests
from collections import deque
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API details
GROQ_API_KEY = os.getenv("groq_api_key")
GROQ_MODEL = "llama3-70b-8192"

def get_llm_response(prompt, chat_history):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": chat_history + [{"role": "user", "content": prompt}],
        "max_tokens": 150,
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response from AI.")

def calculate_emi_breakdown(principal, rate, tenure):
    rate = rate / (12 * 100)  # Monthly interest rate
    emi = (principal * rate * (1 + rate) ** tenure) / ((1 + rate) ** tenure - 1)
    
    breakdown = []
    remaining_balance = principal
    for month in range(1, tenure + 1):
        interest_paid = remaining_balance * rate
        principal_paid = emi - interest_paid
        remaining_balance -= principal_paid
        breakdown.append([month, emi, principal_paid, interest_paid, remaining_balance])
    
    df = pd.DataFrame(breakdown, columns=["Month", "EMI", "Principal Paid", "Interest Paid", "Remaining Balance"])
    return df

st.title("🏡 Home Loan AI Chatbot")
st.write("Chat with the bot to calculate your home loan EMI and repayment schedule!")

suggestions = [
    "What is an EMI?",
    "What are the factors affecting my loan eligibility?",
    "How is home loan interest calculated?",
    "What is the difference between fixed and floating interest rates?",
    "Can I prepay my home loan?"
]

st.write("### Suggested Questions:")
cols=st.columns(2)
for i, question in enumerate(suggestions):
    with cols[i%2]:
        if st.button(question):
            st.session_state.messages.append({"role": "user", "content": question})
            response = get_llm_response(question, list(st.session_state.messages))
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):           #chat message
                st.markdown(response)

if "messages" not in st.session_state:
    st.session_state.messages = deque(maxlen=5)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about home loans or enter loan details...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if any(keyword in user_input.lower() for keyword in ["loan", "emi", "interest", "tenure", "down payment"]):
        response = get_llm_response(user_input, list(st.session_state.messages))
    else:
        response = "I'm here to assist only with home loans! Please ask a relevant question."

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

st.write("### Loan EMI Breakdown")
principal = st.number_input("Enter Loan Amount:", min_value=10000, value=500000)
rate = st.number_input("Enter Annual Interest Rate (%):", min_value=1.0, max_value=20.0, value=8.5)
tenure = st.number_input("Enter Tenure (Months):", min_value=12, max_value=360, value=240)

if st.button("Calculate EMI Schedule"):
    emi_df = calculate_emi_breakdown(principal, rate, tenure)
    st.dataframe(emi_df)
