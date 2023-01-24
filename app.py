"""
# Actuartech IFRS 17 Dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from IFRS17.gmm import GMM
import mysql.connector
st.set_page_config(page_title="Actuartech IFRS 17 Data Management", layout="wide")
st.image("assets/actuartech-logo.png")

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title("Actuartech IFRS 17 Data Management Software")

#@st.cache
#def load_data(file):
#    data = pd.read_csv(file)
#    return data

@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

dashboard_tab, about_tab = st.tabs(["Dashboard", "About Us"])


# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
#@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

BEL = run_query("SELECT * from BEL;")
RA = run_query("SELECT * from RA;")
CSM = run_query("SELECT * from BEL;")
TCL = run_query("SELECT * from RA;")
headers = ["Product", "Sub-Product", "Opening Balance",
                    "Changes Related to Future Service: New Business",
                    "Changes Related to Future Service: Assumptions",
                    "Insurance Service Expense",
                    "Changes Related to Current Service: Experience",
                    "Changes Related to Current Service: Release",
                    "Changes Related to Past Service", "Closing Balance"]
BEL = pd.DataFrame(BEL,columns=headers)
RA = pd.DataFrame(RA,columns=headers)
CSM = pd.DataFrame(CSM,columns=headers)
TCL = pd.DataFrame(TCL,columns=headers)



with about_tab:
    st.write("Placeholder for About Us text")

with dashboard_tab:
    recon_col, sub_col, year_col = st.columns(3)
    with recon_col:
        recon_container = st.container()
        recon_container.write('#### Reconciliation Account')
        recon = recon_container.selectbox('#### ', ('Reconciliation of Best Estimate Liability', 'Reconciliation of Contractual Service Margin', 'Reconciliation of Risk Adjustment', 'Reconciliation of Total Contract Liability'))
        
        if recon == "Reconciliation of Best Estimate Liability":
            data = BEL
        elif recon == "Reconciliation of Contractual Service Margin":
            data = CSM
        elif recon == "Reconciliation of Risk Adjustment":
            data = RA
        elif recon == "Reconciliation of Total Contract Liability":
            data = TCL
            
        with sub_col:
            st.write('#### Subproduct')
            subproduct = st.radio('#### ', tuple(np.unique(data['Sub-Product'])))

        with year_col:
            st.write('#### Reporting Period')
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
                
        download_col, waterfall_col = st.columns(2)
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
                
        with waterfall_col:
            graph_waterfall = st.container()
            graph_waterfall.write('#### ' + str(recon) + '\n' + '##### Waterfall Chart - ' + str(year_range[0]) + " Reporting Period")
            waterfall_data = pd.DataFrame(table_data.transpose()[year_range[0]])
            waterfall_data = waterfall_data.iloc[2:len(waterfall_data)]
            waterfall_data.index.name = "Account"
            waterfall_data.reset_index(inplace=True)
            waterfall_data.columns = ['  ', ' ']
            waterfall_plot = alt.Chart(waterfall_data).mark_bar().encode(
                        x=alt.X('  ', sort=None),
                        y=' '
            )
            st.altair_chart(waterfall_plot, use_container_width=True)
            

                
