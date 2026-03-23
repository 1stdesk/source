import streamlit as st
from transformers import pipeline

# Title of the app
st.title("Simple Sentiment AI 🤖")

# Load the AI model (this might take a minute the first time)
@st.cache_resource
def load_model():
    return pipeline("sentiment-analysis")

classifier = load_model()

# User input
user_input = st.text_input("How are you feeling today?")

if user_input:
    # Run the model
    result = classifier(user_input)
    label = result[0]['label']
    score = result[0]['score']

    # Display results
    st.write(f"The AI thinks this is: **{label}**")
    st.write(f"Confidence: {score:.2%}")
