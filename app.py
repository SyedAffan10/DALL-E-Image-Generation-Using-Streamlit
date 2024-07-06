import openai
import streamlit as st
from dotenv import load_dotenv
import os
import requests
from io import BytesIO
from PIL import Image
import base64
import streamlit_authenticator as stauth
import pandas as pd
import secrets

# Load the .env file
load_dotenv()

# Set your OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define user credentials
credentials = {
    "usernames": {
        "affan": {"name": "Affan", "email": "affan@gmail.com", "password": "affan"},
        "sohail": {"name": "Sohail", "email": "sohail@gmail.com", "password": "sohail"},
        "admin": {"name": "Admin", "email": "admin@gmail.com", "password": "admin"},
        # Add more users as needed
    }
}

# Generate a random cookie key
cookie_key = secrets.token_hex(16)

# Create an authenticator object
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="dalle_app",
    cookie_key=cookie_key,
    cookie_expiry_days=30
)

# Authentication
name, authentication_status, username = authenticator.login()

if authentication_status:
    st.title(f"Welcome {name}")

    authenticator.logout("Logout", "sidebar")

    # Load the request log
    if os.path.exists("request_log.csv"):
        request_log = pd.read_csv("request_log.csv")
    else:
        request_log = pd.DataFrame(columns=["username", "email", "prompt", "timestamp", "image_base64"])

    # Display user history in the sidebar
    user_history = request_log[request_log["username"] == username]

    st.sidebar.title("Your History")
    for index, row in user_history.iterrows():
        st.sidebar.write(f"Prompt: {row['prompt']}")
        image_data = base64.b64decode(row["image_base64"])
        st.sidebar.image(Image.open(BytesIO(image_data)), use_column_width=True)

    # Admin view: Show request log and search functionality
    if username == "admin":
        st.write("Admin Panel: Request Log")

        # Inputs for search
        search_username = st.text_input("Search by Username")
        search_date = st.date_input("Search by Date")
        
        # Filter the log based on inputs
        if search_username or search_date:
            if search_username:
                request_log = request_log[request_log["username"].str.contains(search_username, case=False, na=False)]
            if search_date:
                request_log = request_log[pd.to_datetime(request_log["timestamp"]).dt.date == search_date]
        
        # Display the filtered log
        st.dataframe(request_log)
        
        # Display the count of requests
        st.write(f"Total requests: {request_log.shape[0]}")
    
    # Regular user view: Generate image
    else:
        st.write("Enter a prompt to generate an image:")

        # Input for the prompt
        prompt = st.text_input("Prompt")

        # Input for the image
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

        # Function to encode image as base64
        def encode_image(image_file):
            buffered = BytesIO()
            image_file.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Function to get image description using OpenAI's model
        def get_image_description(image):
            base64_image = encode_image(image)

            # Make API call to OpenAI
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in describing an image."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Give me the description of this image."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]}
                ],
                temperature=0.0,
            )

            description = response.choices[0].message.content
            return description

        # Button to submit the prompt
        if st.button("Generate Image"):
            if prompt:
                with st.spinner("Generating image..."):
                    try:
                        combined_prompt = prompt
                        if uploaded_image:
                            input_image = Image.open(uploaded_image)
                            st.image(input_image, caption="Uploaded Image", use_column_width=True)
                            image_description = get_image_description(input_image)
                            combined_prompt = f"{image_description}. {prompt}"

                        # Generate image using OpenAI's DALL-E model
                        response = openai.images.generate(
                            model="dall-e-3",
                            prompt=combined_prompt,
                            size="1024x1024",
                            n=1
                        )
                        # Get the URL of the generated image
                        image_url = response.data[0].url

                        # Display the generated image
                        st.image(image_url, caption="Generated Image", use_column_width=True)

                        # Fetch the image from URL for logging
                        image_response = requests.get(image_url)
                        image_data = BytesIO(image_response.content)
                        image_base64 = base64.b64encode(image_data.getvalue()).decode("utf-8")

                        # Log the request
                        new_entry = pd.DataFrame([{
                            "username": username,
                            "email": credentials["usernames"][username]["email"],
                            "prompt": prompt,
                            "timestamp": pd.Timestamp.now(),
                            "image_base64": image_base64
                        }])
                        request_log = pd.concat([request_log, new_entry], ignore_index=True)
                        request_log.to_csv("request_log.csv", index=False)

                        # Update the history in the sidebar
                        user_history = request_log[request_log["username"] == username]
                        
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.error("Please enter a prompt.")


elif authentication_status == False:
    st.error("Username/password is incorrect")

elif authentication_status == None:
    st.warning("Please enter your username and password")

