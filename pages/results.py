"""
# Results page
"""

import streamlit as st
import pandas as pd
from IFRS17.gmm import GMM

st.set_page_config(page_title="Actuartech IFRS 17 Data Management")

st.title("Results")
st.subheader("Tables")

assumptions = st.session_state.assumptions
parameters = st.session_state.parameters

if assumptions is not None and parameters is not None:
    g = GMM(assumptions, parameters)
    st.subheader('Analysis by Remaining Coverage')
    arc = g.Analysis_by_remaining_coverage
    st.table(arc)
    st.subheader('Analysis by Measurement Component')
    mc = g.Analysis_by_measurement_component
    st.table(mc)
else:
    st.write('### Please ensure your data is uploaded')
