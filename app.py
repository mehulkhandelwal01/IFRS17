"""
# Basic dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
from IFRS17.gmm import GMM

st.set_page_config(page_title="Actuartech IFRS 17 Data Management")

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

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
            #st.subheader('Dashboard')
            recon_container = st.container()
            recon_container.write('#### Reconciliation Account')
            recon = recon_container.selectbox('#### ', ('Reconciliation of Best Estimate Liability', 'Reconciliation of Contractual Service Margin', 'Reconciliation of Risk Adjustment', 'Reconciliation of Total Contract Liability'))
            year_col, measure_col, table_col, recon_col = st.columns(4)
            with year_col:
                st.write('#### Year')
                g = GMM(assumptions, parameters)
                if recon == "Reconciliation of Best Estimate Liability":
                    data = g.Reconciliation_of_Best_Estimate_Liability
                elif recon == "Reconciliation of Contractual Service Margin":
                    data = g.Reconciliation_of_Contractual_Service_Margin
                elif recon == "Reconciliation of Risk Adjustment":
                    data = g.Reconciliation_of_Risk_Adjustment
                elif recon == "Reconciliation of Total Contract Liability":
                    data = g.Reconciliation_of_Total_Contract_Liability

            min_year = np.min(data.index)
            max_year = np.max(data.index)
            years = st.slider('#### ', min_year, max_year, (min_year, min_year+1))
            year_range = range(years[0], years[len(years)-1]+1)

            st.write(str('#### ' + str(recon)))
            st.dataframe(data.loc[year_range, :], use_container_width=True) 

            container_measure = st.container()
            container_measure.write('#### Measure')
            measure_values = data.columns
            list_of_measures = tuple(measure_values[2:len(measure_values)])
            measure = container_measure.radio("#### ", list_of_measures)

            graph_measure = st.container()
            graph_measure.write('#### Graph')
            graph_data = data.loc[year_range, str(measure)]
            graph_measure.bar_chart(graph_data)
