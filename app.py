"""
Smart Entertainment Recommendation System - Streamlit Entrypoint.
Starts background Flask API server and renders the redesigned high-performance UI.
"""

import os
import sys
import time
import socket
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from api_server import start_server_in_thread

# Configure Streamlit Page
st.set_page_config(
    page_title="Smart Entertainment Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS to hide default Streamlit padding and headers for full-screen UI
st.markdown("""
<style>
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  header {visibility: hidden;}
  [data-testid="stHeader"] {display: none;}
  .block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
  }
  iframe {
    width: 100% !important;
    height: 100vh !important;
    border: none !important;
  }
</style>
""", unsafe_allow_html=True)


def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


API_PORT = 8502

if not is_port_in_use(API_PORT):
    start_server_in_thread(port=API_PORT)
    time.sleep(1.0)

components.iframe(f"http://127.0.0.1:{API_PORT}", height=1000, scrolling=True)
