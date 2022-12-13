"""
# Basic dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
from IFRS17.gmm import GMM

st.set_page_config(page_title="Actuartech IFRS 17 Data Management")

st.title("Actuartech IFRS 17 Data Management Software")

@st.cache
def load_data(file):
    data = pd.read_csv(file)
    return data

load_tab, dashboard_tab = st.tabs(["Load Data", "Dashboard"])

with load_tab:
    st.subheader("Upload your data")
    assumptions = st.file_uploader('Choose an Assumptions CSV File')
    parameters = st.file_uploader('Choose a Parameters CSV File')
    if assumptions is not None and parameters is not None:
        assumptions = load_data(assumptions)
        parameters = load_data(parameters)
        container_data = st.container()
        if container_data.checkbox('Show raw data'):
            container_data.subheader('Assumptions file')
            container_data.write(assumptions)
            container_data.subheader('Parameters file')
            container_data.write(parameters)
        with dashboard_tab:
            st.subheader('Dashboard')
            year_col, measure_col, table_col, recon_col = st.columns(4)
            recon_container = st.container()
            recon = recon_container.selectbox('Select a Reconciliation Account', ('Reconciliation of Best Estimate Liability', 'Reconciliation of Contractual Service Margin', 'Reconciliation of Risk Adjustment', 'Reconciliation of Total Contract Liability'))
            with year_col:
                st.write('#### Year')
                g = GMM(assumptions, parameters)
                min_year = np.min(g.Reconciliation_of_Best_Estimate_Liability.index)
                max_year = np.max(g.Reconciliation_of_Best_Estimate_Liability.index)
                years = st.slider('Year:', min_year, max_year, (min_year, min_year+1))
                #years = st.slider('Year:', 2019, 2022, (2019, 2019+1))
            with table_col:
                st.write('#### Reconciliation of Best Estimate Liability')
                st.dataframe(g.Reconciliation_of_Best_Estimate_Liability) 

            container_measure = st.container()
            container_measure.write('#### Measure')
            measure_values = g.Reconciliation_of_Best_Estimate_Liability.columns
            list_of_measures = tuple(measure_values[2:len(measure_values)])
            measure = container_measure.radio("Measure", list_of_measures)

            graph_measure = st.container()
            graph_measure.write('#### Graph')
            year_range = range(years[0], years[len(years)-1]+1)
            graph_data = g.Reconciliation_of_Best_Estimate_Liability.loc[year_range, str(measure)]
            graph_measure.bar_chart(graph_data)
