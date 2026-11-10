"""Ski Trip Planner: Streamlit entry point.

Run with:
    streamlit run app.py

Streamlit automatically adds every file in the ``pages/`` folder to the
sidebar navigation. This file is the landing page.
"""

import streamlit as st

st.set_page_config(
    page_title="Ski Trip Planner",
    page_icon="⛷️",
    layout="wide",
)

st.title("⛷️ Ski Trip Planner")
st.write(
    "Explore 23 major ski resorts in Colorado and Utah using about ten years "
    "of historical snowfall and temperature data, plus live snow forecasts."
)

st.info("The app is under construction. Pages will appear in the sidebar as they are built.")
