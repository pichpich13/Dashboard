import streamlit as st
import subprocess

# Download requirements
subprocess.call(["pip", "install", "-r", "requirements.txt"])

# Start the dashboard
subprocess.call(["streamlit", "run", "dashboard.py"])