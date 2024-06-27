import openai
import streamlit as st
from dotenv import load_dotenv
import os
import requests
from io import BytesIO

# Load the .env file
load_dotenv()

# Set your OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

# Streamlit app
st.title("Generate an Image with DALL-E")
st.write("Enter a prompt to generate an image:")

# Input for the prompt
prompt = st.text_input("Prompt")

# Button to submit the prompt
if st.button("Generate Image"):
    if prompt:
        with st.spinner("Generating image..."):
            try:
                # Generate image using OpenAI's API
                response = openai.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                # Get the URL of the generated image
                image_url = response.data[0].url

                # Display the image
                st.image(image_url, caption="Generated Image")

                # Download the image
                image_response = requests.get(image_url)
                image_data = BytesIO(image_response.content)

                # Add a save button to download the image
                st.download_button(
                    label="Save Image",
                    data=image_data,
                    file_name="generated_image.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.error("Please enter a prompt.")
