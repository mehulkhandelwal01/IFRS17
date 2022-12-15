"""
# Actuartech IFRS 17 Dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
from IFRS17.gmm import GMM

st.set_page_config(page_title="Actuartech IFRS 17 Data Management", layout="wide")
st.image("assets/actuartech-logo.png")

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

@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

load_tab, dashboard_tab, about_tab = st.tabs(["Load Data", "Dashboard", "About Us"])

with about_tab:
    st.write("Placeholder for About Us text")

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
            recon_col, sub_col, year_col = st.columns(3)
            with recon_col:
                recon_container = st.container()
                recon_container.write('#### Reconciliation Account')
                recon = recon_container.selectbox('#### ', ('Reconciliation of Best Estimate Liability', 'Reconciliation of Contractual Service Margin', 'Reconciliation of Risk Adjustment', 'Reconciliation of Total Contract Liability'))
                g = GMM(assumptions, parameters)
                if recon == "Reconciliation of Best Estimate Liability":
                    data = g.BEL
                elif recon == "Reconciliation of Contractual Service Margin":
                    data = g.CSM
                elif recon == "Reconciliation of Risk Adjustment":
                    data = g.RA
                elif recon == "Reconciliation of Total Contract Liability":
                    data = g.TCL
            
            with sub_col:
                st.write('#### Subproduct')
                subproduct = st.radio('#### ', tuple(np.unique(data['Sub-Product'])))

            with year_col:
                st.write('#### Year')
                min_year = int(min(np.array(data.index)))
                max_year = int(max(np.array(data.index)))
                years = st.slider('#### ', min_year, max_year, (min_year, min_year+1))
                year_range = range(years[0], years[len(years)-1]+1)

            st.write(str('#### ' + str(recon)))
            table_data = data.loc[data["Sub-Product"] == str(subproduct)].loc[year_range, :] 
            st.dataframe(table_data)
            
            measure_col, graph_col = st.columns(2)
            with measure_col:
                container_measure = st.container()
                container_measure.write('#### Measure')
                measure_values = data.columns
                list_of_measures = tuple(measure_values[2:len(measure_values)])
                measure = container_measure.radio("#### ", list_of_measures)
            
            with graph_col:
                graph_measure = st.container()
                graph_measure.write('#### ' + str(recon) + '\n' + '##### ' + str(measure))
                graph_data = data.loc[data["Sub-Product"] == str(subproduct)].loc[year_range, str(measure)]
                graph_measure.bar_chart(graph_data)
            
            download_col, empty_col = st.columns(2)
            with download_col:
                file_name = str("ifrs17" + "-" + str(subproduct) + "-" + str(measure) + "-" + str(years[0]) + "-" + str(years[1]) + ".csv")
                csv = convert_df(table_data)
                st.download_button(
                        "📥 Download Current Filter as CSV",
                        csv,
                        file_name,
                        "text/csv",
                        key="download-csv"
                        )
            #with open("ifrs17output.zip", "rb") as fp:
            #    btn = st.download_button(
            #            label="Download IFRS 17 Output",
            #            data=fp,
            #            file_name="ifrs17output.zip",
            #            mime="application/zip"
            #            )
