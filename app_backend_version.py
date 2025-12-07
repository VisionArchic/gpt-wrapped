import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from collections import Counter, defaultdict
import datetime
import tiktoken
import numpy as np
import random
import requests

# --- BACKEND CONFIG ---
# For local development
BACKEND_URL = "http://localhost:8000"

# For production (update after deploying backend)
# BACKEND_URL = "https://your-backend-url.com"

# Override with Streamlit secrets if available
if 'backend' in st.secrets:
    BACKEND_URL = st.secrets.backend.url

# --- CONSTANTS FOR ESTIMATES ---
COST_PER_1M_TOKENS = 2.5      # USD per 1M tokens (OpenAI GPT-4 avg)
KWH_PER_1M_TOKENS = 0.3       # kWh per 1M tokens (rough estimate)
LITERS_PER_1M_TOKENS = 3.5    # Water in liters per 1M tokens (datacenter cooling)

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="GPT Wrapped",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.io as pio
pio.templates.default = "plotly_dark"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #050505;}
    h1, h2, h3 {color: #FF0055; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 2px;}
    
    .persona-banner {
        text-align: center; padding: 60px;
        background: black;
        border-bottom: 4px solid #FF0055;
        margin-bottom: 40px;
        color: white; font-size: 4em; font-weight: bold;
        text-transform: uppercase; letter-spacing: 8px;
        text-shadow: 4px 4px 0px #FF0055;
    }
    
    .section-header {
        margin-top: 60px; margin-bottom: 20px; 
        border-bottom: 2px solid #333; padding-bottom: 10px;
        font-size: 2em; color: #fff;
    }
    
    .explanation {
        color: #888; font-size: 0.9em; font-style: italic; margin-bottom: 20px;
    }
    
    .chat-bubble {
        padding: 15px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #222;
        font-family: 'Verdana', sans-serif; font-size: 0.95em;
    }
    .user-bubble {background-color: #0a0a0a; color: #ccc; text-align: right; border-right: 2px solid #00CCFF;}
    .ai-bubble {background-color: #110011; color: #ffccff; border-left: 2px solid #FF0055;}
</style>
""", unsafe_allow_html=True)

# --- 2. HELPERS ---

@st.cache_resource
def setup_tools():
    import nltk
    required = ['punkt', 'punkt_tab', 'stopwords', 'averaged_perceptron_tagger']
    for r in required:
        try: nltk.data.find(f'tokenizers/{r}')
        except: 
             try: nltk.data.find(f'taggers/{r}')
             except:
                 try: nltk.data.find(f'corpora/{r}')
                 except: nltk.download(r, quiet=True)

setup_tools()
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

@st.cache_resource
def get_encoding():
    return tiktoken.get_encoding("cl100k_base")
enc = get_encoding()

# --- 3. BACKEND INTEGRATION ---

def upload_to_backend(file_content):
    """Upload file to backend for processing"""
    try:
        files = {'file': ('conversations.json', file_content, 'application/json')}
        response = requests.post(f"{BACKEND_URL}/api/upload", files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")
        st.info("💡 Processing locally instead...")
        return None

# [REST OF THE CODE REMAINS THE SAME - just using data from backend response]
# The parse_conversations and other functions stay the same

def main():
    # --- PRIVACY NOTICE ---
    st.sidebar.markdown("---")
    st.sidebar.info("🔒 Files are sent to backend for processing and admin verification")
    
    st.sidebar.title("📥 Upload")
    f = st.sidebar.file_uploader("conversations.json", type="json")
    
    if not f:
        st.title("GPT Wrapped")
        st.markdown("""
        ### 🎁 Unwrap Your ChatGPT Journey
        
        Upload your ChatGPT `conversations.json` to see beautiful analytics.
        
        **How to get your data:**
        1. Go to [ChatGPT Settings](https://chat.openai.com/settings)
        2. Click "Data Controls" → "Export Data"  
        3. Wait for email with download link
        4. Upload `conversations.json` here!
        
        ---
        
        **📧 Note:** Uploaded files are sent to our backend for verification and stored securely.
        """)
        return

    with st.spinner("Uploading and processing..."):
        # Read file
        file_content = f.read()
        
        # Send to backend
        backend_response = upload_to_backend(file_content)
        
        if backend_response and backend_response.get('status') == 'success':
            st.success("✅ File received and sent to admin!")
            
            # Get processed data from backend
            data = backend_response.get('data', [])
            
            # Continue with normal processing using the data...
            # [Rest of your existing visualization code]
            
        else:
            st.error("Backend unavailable. Please try again later.")
            return

if __name__ == "__main__":
    main()
