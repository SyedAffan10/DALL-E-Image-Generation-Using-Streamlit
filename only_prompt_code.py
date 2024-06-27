import openai
import streamlit as st
from dotenv import load_dotenv
import os
import requests
from io import BytesIO
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

    # Admin view: Show request log and search functionality
    if username == "admin":
        st.write("Admin Panel: Request Log")

        # Load the request log
        if os.path.exists("request_log.csv"):
            request_log = pd.read_csv("request_log.csv")
            
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
        else:
            st.write("No logs available.")
    
    # Regular user view: Generate image
    else:
        st.write("Enter a prompt to generate an image:")

        # Input for the prompt
        prompt = st.text_input("Prompt")

        # Load the request log
        if os.path.exists("request_log.csv"):
            request_log = pd.read_csv("request_log.csv")
        else:
            request_log = pd.DataFrame(columns=["username", "email", "prompt", "timestamp"])

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

                        # Log the request
                        new_entry = pd.DataFrame([{
                            "username": username,
                            "email": credentials["usernames"][username]["email"],
                            "prompt": prompt,
                            "timestamp": pd.Timestamp.now()
                        }])
                        request_log = pd.concat([request_log, new_entry], ignore_index=True)
                        request_log.to_csv("request_log.csv", index=False)

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.error("Please enter a prompt.")

elif authentication_status == False:
    st.error("Username/password is incorrect")

elif authentication_status == None:
    st.warning("Please enter your username and password")

authenticator.logout("Logout", "sidebar")
