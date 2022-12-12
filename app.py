"""
# Basic dashboard
"""

import streamlit as st
import pandas as pd
from IFRS17.gmm import GMM

assumptions = st.file_uploader('Choose an Assumptions CSV File')
parameters = st.file_uploader('Choose an Parameters CSV File')

if assumptions is not None and parameters is not None:

    g = GMM(assumptions, parameters)
    st.table(g.Analysis_by_remaining_coverage)
