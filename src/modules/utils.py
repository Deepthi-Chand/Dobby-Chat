import os
from io import StringIO

import pandas as pd
import streamlit as st
import pdfplumber
import requests

from modules.chatbot import Chatbot
from modules.embedder import Embedder

class Utilities:

    @staticmethod
    def load_api_key():
        """
        Loads the OpenAI API key from the .env file or 
        from the user's input and returns it
        """
        if not hasattr(st.session_state, "api_key"):
            st.session_state.api_key = None
        #you can define your API key in .env directly
        if os.path.exists(".env") and os.environ.get("OPENAI_API_KEY") is not None:
            user_api_key = os.environ["OPENAI_API_KEY"]
            st.sidebar.success("API key loaded from .env", icon="🚀")
        else:
            if st.session_state.api_key is not None:
                user_api_key = st.session_state.api_key
                st.sidebar.success("API key loaded from previous input", icon="🚀")
            else:
                user_api_key = st.sidebar.text_input(
                    label="#### Your OpenAI API key 👇", placeholder="sk-...", type="password"
                )
                if user_api_key:
                    st.session_state.api_key = user_api_key

        return user_api_key


    @staticmethod
    def handle_upload(file_types):
        """
        Handles and display uploaded_file
        :param file_types: List of accepted file types, e.g., ["csv", "pdf", "txt"]
        """
        uploaded_file = st.sidebar.file_uploader("upload", type=file_types, label_visibility="collapsed")
        if uploaded_file is not None:

            def show_csv_file(uploaded_file):
                file_container = st.expander("Your CSV file :")
                uploaded_file.seek(0)
                shows = pd.read_csv(uploaded_file)
                file_container.write(shows)

            def show_pdf_file(uploaded_file):
                file_container = st.expander("Your PDF file :")
                with pdfplumber.open(uploaded_file) as pdf:
                    pdf_text = ""
                    for page in pdf.pages:
                        pdf_text += page.extract_text() + "\n\n"
                file_container.write(pdf_text)

            def show_txt_file(uploaded_file):
                file_container = st.expander("Your TXT file:")
                uploaded_file.seek(0)
                content = uploaded_file.read().decode("utf-8")
                file_container.write(content)

            def get_file_extension(uploaded_file):
                return os.path.splitext(uploaded_file)[1].lower()

            file_extension = get_file_extension(uploaded_file.name)

            # Show the contents of the file based on its extension
            #if file_extension == ".csv" :
            #    show_csv_file(uploaded_file)
            if file_extension== ".pdf" :
                show_pdf_file(uploaded_file)
            elif file_extension== ".txt" :
                show_txt_file(uploaded_file)

        else:
            st.session_state["reset_chat"] = True

        #print(uploaded_file)
        return uploaded_file

    @staticmethod
    def setup_chatbot(uploaded_file, model, temperature):
        """
        Sets up the chatbot with the uploaded file, model, and temperature
        """
        embeds = Embedder()

        with st.spinner("Processing..."):
            uploaded_file.seek(0)
            file = uploaded_file.read()
            # Get the document embeddings for the uploaded file
            vectors = embeds.getDocEmbeds(file, uploaded_file.name)

            # Create a Chatbot instance with the specified model and temperature
            chatbot = Chatbot(model, temperature,vectors)
        st.session_state["ready"] = True

        return chatbot

    @staticmethod
    def handle_file_link(file_types):
        """
                Handles url link and display linked file
                :param file_types: List of accepted file types, e.g., ["csv", "pdf", "txt"]
        """
        url_link = st.sidebar.text_input(placeholder="Enter valid CSV URL", label_visibility="hidden", label=" ")
        if is_valid_url(url_link):
            def show_csv_file(url):
                file_container = st.expander("Your CSV file :")
                api_response = requests.get(url)
                csv_data = StringIO(api_response.text)
                df = pd.read_csv(csv_data, sep=",", keep_default_na=False)
                # df = pd.read_csv(url, storage_options={"User-Agent": "Mozilla/5.0"})
                file_container.write(df)
            # def get_file_extension(uploaded_file):
            #     return os.path.splitext(uploaded_file)[1].lower()

            # Show the contents of the url
            print(url_link)
            show_csv_file(url_link)
        else:
            st.session_state["reset_chat"] = True

        # print(url_link)
        return url_link


def is_valid_url(url):
    try:
        response = requests.get(url)
        print(response)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError:
        return False
    except requests.exceptions.RequestException:
        return False
