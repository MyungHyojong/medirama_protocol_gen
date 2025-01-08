import streamlit as st
import openai
import os
import pandas as pd
import requests
import io
import zipfile
import base64
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.dml.color import RGBColor
import pyperclip
from openai import OpenAI

# Configure OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=openai.api_key)

# Streamlit app title
st.title("Clinical Trial Protocol Generator")

# Sidebar for input parameters
st.sidebar.header("Specify Parameters")
phase = st.sidebar.text_input("Phase")
moa_category = st.sidebar.text_input("MOA Category")
specific_moa = st.sidebar.text_input("Specific MOA")
cancer_type = st.sidebar.text_input("Cancer Type")
subtype = st.sidebar.text_input("Subtype")
word_limit = st.sidebar.number_input("Letter Limit", min_value=700, max_value=9000, step=1000)
temperature = st.sidebar.slider("Temperature", min_value=0.5, max_value=1.5, value=0.7, step=0.1)

# Input for section request
section_request = st.text_area(
    "Enter the clinical trial protocol section details you want to generate:",
    "Use in Pregnancy",
    height=80,
)

# Initialize session state for generated text
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

# Button to generate protocol section
if st.button("Generate Protocol Section"):
    if not phase or not moa_category or not specific_moa or not cancer_type or not subtype:
        st.error("Please fill in all the fields in the sidebar.")
    else:
        with st.spinner("Generating protocol section..."):
            try:
                # Format the prompt
                formatted_prompt = (
                    f"Write a clinical trial protocol section for \n'{section_request}'\n"
                    f"for the study titled: \n'(MOA) of {specific_moa}, a {moa_category}, "
                    f"in combination with immunotherapy, in patients with {cancer_type}, phase {phase}'\n\n"
                    "Write as the following rules:\n"
                    "- Write only the passage with full sentence and exclude other items with a single word\n"
                    "- Additional letters that doesn't belong to the main text such as 'Date, page, Title of the page' should never be included. Only the FULL sentence is available\n"
                    "- Do not indicate other section or page number. The section you wrote should be understandable in itself\n"
                    f"- Write within {word_limit} letters\n"
                )

                # Generate text using GPT (first model)
                completion = client.chat.completions.create(
                    model="ft:gpt-4o-mini-2024-07-18:medirama::AmzAIoxv",
                    messages=[
                        {"role": "system", "content": "You are a clinical scientist with expertise in writing clinical trial protocols.."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    temperature=temperature
                )
                generated_text = completion.choices[0].message.content

                # Refine text using GPT (second model)
                refine_prompt = (
                    f"Refine the following text to match the given rules:\n\n"
                    f"{generated_text}\n\n"
                    "Write as the following rules:\n"
                    "- Write only the passage with full sentence and exclude other items with a single word\n"
                    "- Additional letters that doesn't belong to the main text such as 'Date, page, Title of the page' should never be included. Only the FULL sentence is available\n"
                    "- Do not indicate other section or page number. The section you wrote should be understandable in itself\n"
                    "- If there's too specific contents, make it broader\n"
                    f"- Write within {word_limit} letters\n"
                )

                response2 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes clinical trial descriptions."},
                        {"role": "user", "content": refine_prompt}
                    ],
                    temperature=temperature
                )
                refined_text = response2.choices[0].message.content

                # Store the refined text in session state
                st.session_state.generated_text = refined_text

            except Exception as e:
                st.error(f"Error: {e}")

# Display the refined protocol section in an editable area
st.text_area(
    "Generated Protocol Section (Editable)",
    value=st.session_state.generated_text,
    height=300
)

# Button to copy the final text to clipboard
if st.button("Copy to Clipboard"):
    pyperclip.copy(st.session_state.generated_text)
    st.success("Text copied to clipboard!")

# Footer
st.write("\nCreated with Streamlit and OpenAI GPT.")
