"""
# Basic dashboard
"""

import streamlit as st
import pandas as pd
from IFRS17.gmm import GMM

st.set_page_config(page_title="Actuartech IFRS 17 Data Management")

st.title("Actuartech IFRS 17 Data Management Software")
st.subheader("Upload your data")
assumptions = st.file_uploader('Choose an Assumptions CSV File')
parameters = st.file_uploader('Choose a Parameters CSV File')

@st.cache
def load_data(file):
    data = pd.read_csv(file)
    return data

if assumptions is not None and parameters is not None:
    assumptions = load_data(assumptions)
    parameters = load_data(parameters)
    if st.checkbox('Show raw data'):
        st.subheader('Assumptions file')
        st.write(assumptions)
        st.subheader('Parameters file')
        st.write(parameters)
