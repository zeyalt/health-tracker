# -*- coding: utf-8 -*-
"""
Created on Sun Dec 20 07:28:29 2020

@author: Zeya
"""

import pandas as pd
from pathlib import Path
import sqlite3
from sqlite3 import Connection
import streamlit as st
from datetime import timedelta
import datetime as dt
import plotly.graph_objects as go
import base64
from io import BytesIO

# DATABASE_NAME = "myint_lwin_health_records"
# URI_SQLITE_DB = DATABASE_NAME + ".db"

def main():
    st.title("Health Tracker")
    st.markdown("Use this web application to store, update and monitor your health records.")
    selected_user = st.selectbox("Select user", ["U Myint Lwin", "Daw Le Le Oo"])
    DATABASE_NAME = '_'.join(selected_user.lower().split()) + '_health_records'
    URI_SQLITE_DB = DATABASE_NAME + ".db"
    conn = get_connection(URI_SQLITE_DB)
    init_db(conn)
    health_record = st.selectbox("Select health record to update", ["Blood Pressure", "Resting Heart Rate", "Body Mass Index"])

    if health_record == "Blood Pressure":
        a1, a2, a3 = st.beta_columns([1, 2, 2])
        date = a1.date_input('Date of measurement', dt.date.today(), key='1')
        lower = a2.number_input("Diastolic (lower) blood pressure (mmHg)", min_value=40, value=60)
        upper = a3.number_input("Systolic (upper) blood pressure (mmHg)", min_value=60, value=90)
        
        if st.button("Save record", key='1'):
            conn.execute(f"INSERT INTO blood_pressure_table (Date, Lower, Upper) VALUES (?, ?, ?)", (date, lower, upper))
            conn.commit()

        output_ex = st.beta_expander("View Output")
        view_mode = output_ex.radio("Select view mode", ["Table", "Chart"], key='1')
        df_blood_pressure = get_blood_pressure_data(conn)

        if view_mode == "Table":
            output_ex.table(df_blood_pressure)
            
            # if output_ex.button("Edit record", key='4'):
            #     index = output_ex.number_input("Enter row number", min_value=0, value=0, step=1)
            #     if output_ex.button("Retrieve record", key='5'):
            #         date_to_edit = df_blood_pressure["Date"][index]
            #         lower_to_edit = df_blood_pressure["Diastolic (Lower)"][index]
            #         upper_to_edit = df_blood_pressure["Systolic (Upper)"][index]
            #         # st.text(date_to_edit)
            #         e1, e2, e3 = output_ex.beta_columns([1, 2, 2])
            #         date_editted = e1.date_input('Date of measurement', date_to_edit, key='2')
            #         # date_editted = date_editted.strftime("%Y-%m-%d") 
            #         lower_editted = e2.number_input("Diastolic (lower) blood pressure (mmHg)", min_value=40, value=lower_to_edit, key='2')
            #         upper_editted = e3.number_input("Systolic (upper) blood pressure (mmHg)", min_value=60, value=upper_to_edit, key='2')
        
        else:
            fig1 = plot_blood_pressure(df_blood_pressure)
            output_ex.plotly_chart(fig1)
            fig2 = plot_blood_pressure_line(df_blood_pressure)
            output_ex.plotly_chart(fig2)
        
        # st.markdown(get_table_download_link(df_blood_pressure), unsafe_allow_html=True)


    elif health_record == "Resting Heart Rate":
        b1, b2 = st.beta_columns(2)
        date = b1.date_input('Date of measurement', dt.date.today(), key='2')
        date = date.strftime("%Y-%m-%d")  
        heart_rate = b2.number_input("Resting heart rate (beats per minute)", min_value=40, value=75)

        if st.button("Save record", key='2'):
            conn.execute(f"INSERT INTO heart_rate_table (Date, HeartRate) VALUES (?, ?)", (date, heart_rate))
            conn.commit()
        
        output_ex = st.beta_expander("View Output")
        view_mode = output_ex.radio("Select view mode", ["Table", "Chart"], key='2')
        df_heart_rate = get_heart_rate_data(conn)
        
        if view_mode == "Table":
            output_ex.table(df_heart_rate)
        else:
            fig = plot_heart_rate(df_heart_rate)
            output_ex.plotly_chart(fig)

    elif health_record == "Body Mass Index":
        c1, c2, c3 = st.beta_columns(3)
        date = c1.date_input('Date of measurement', dt.date.today(), key='3')
        date = date.strftime("%Y-%m-%d")    
        weight = c2.number_input("Weight (kg)", min_value=63.0, value=67.3, step=0.1)
        weight = round(weight, 1)
        height = c3.number_input("Height (m)", min_value=1.2, value=1.72, step=0.01)
        height = round(height, 2)
        bmi = round(weight / (height**2), 1)
        bmi1, bmi2, bmi3 = st.beta_columns(3)
        bmi1.write("Your BMI is ")
        bmi2.header(str(bmi))

        if st.button("Save record", key='3'):
            conn.execute(f"INSERT INTO bmi_table (Date, Weight, Height, BMI) VALUES (?, ?, ?, ?)", (date, weight, height, bmi))
            conn.commit()

        output_ex = st.beta_expander("View Output")
        view_mode = output_ex.radio("Select view mode", ["Table", "Chart"], key='3')
        df_bmi = get_bmi_data(conn)
        
        if view_mode == "Table":
            output_ex.table(df_bmi)
        else:
            fig1 = plot_weight(df_bmi)
            fig2 = plot_bmi(df_bmi)
            output_ex.plotly_chart(fig1)
            output_ex.plotly_chart(fig2)

# def to_excel(df):
#     output = BytesIO()
#     writer = pd.ExcelWriter(output, engine='xlsxwriter')
#     df.to_excel(writer, index=False, sheet_name='Sheet1')
#     writer.save()
#     processed_data = output.getvalue()
#     return processed_data

# def get_table_download_link(df):
#     """Generates a link allowing the data in a given panda dataframe to be downloaded
#     in:  dataframe
#     out: href string
#     """
#     # csv = df.to_csv(index=False)
#     csv = to_excel(df)
#     b64 = base64.b64encode(val)
    
#     return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download csv file</a>' # decode b'abc' => abc
#     # b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
#     # href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
#     # href = f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'
    
#     # return href

@st.cache(allow_output_mutation=True)
def plot_heart_rate(data):
    data = data.sort_values('Date')
    fig = go.Figure()    
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Resting Heart Rate']), 
        connectgaps=True,
        marker=dict(
                color='purple',
                size=11)
    ))
    fig.update_yaxes(
            title_text = "Resting Heart Rate (beats per minute)")
    fig.update_layout(
        title="Resting Heart Rate")

    return fig

@st.cache(allow_output_mutation=True)
def plot_weight(data):
    data = data.sort_values('Date')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Weight']), 
        connectgaps=True,
        marker=dict(
                color='orange',
                size=11)
    ))
    fig.update_yaxes(
            title_text = "Weight (kg)")
    fig.update_layout(
        title="Weight")
    
    return fig

@st.cache(allow_output_mutation=True)
def plot_bmi(data):
    data = data.sort_values('Date')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['BMI']), 
        connectgaps=True 
    ))
    fig.update_yaxes(
            title_text = "BMI")
    fig.update_layout(
        title="Body Mass Index")

    return fig

@st.cache(allow_output_mutation=True)
def plot_blood_pressure(data):
    data = data.sort_values('Date')
    x = [i for i in list(data["Date"]) for j in range(3)]
    y = []
    for i, j in data.iterrows():
        y.append(j["Diastolic (Lower)"])
        y.append(j["Systolic (Upper)"])
        y.append(None)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        name='Gaps',
        connectgaps=False,
        marker=dict(
                color='green',
                size=11)
        ))
    fig.update_layout(xaxis_range=[(min(x) - timedelta(days=5)).to_pydatetime(),
                                   (max(x) + timedelta(days=5)).to_pydatetime()])
    fig.update_yaxes(
            title_text = "Blood Pressure (mmHg)")
    fig.update_layout(
        title="Blood Pressure")

    return fig

@st.cache(allow_output_mutation=True)
def plot_blood_pressure_line(data):
    data = data.sort_values('Date')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Diastolic (Lower)'],
        name='Diastolic Blood Pressure',
        connectgaps=True,
        marker=dict(
                color='blue',
                size=11)
    ))
    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Systolic (Upper)'], 
        name='Systolic Blood Pressure',
        connectgaps=True,
        marker=dict(
                color='red',
                size=11)
    ))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    fig.update_yaxes(
            title_text = "Blood Pressure (mmHg)")
    fig.update_layout(
        title="Blood Pressure (Line Chart)")

    return fig

def init_db(conn: Connection):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS blood_pressure_table
            (
                Date text, 
                Lower INT,
                Upper INT
            );"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS heart_rate_table
           (
               Date text,
               HeartRate INT
               )
        """
        )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS bmi_table
           (
               Date text,
               Weight DOUBLE,
               Height FLOAT,
               BMI REAL
               )
        """
        )

    conn.commit() 

def get_blood_pressure_data(conn: Connection):
    df = pd.read_sql("SELECT * FROM blood_pressure_table", con=conn)
    df.columns = ['Date', 'Diastolic (Lower)', 'Systolic (Upper)']
    df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
    # df['Date'] = df['Date'].dt.strftime("%d-%m-%Y")
    # df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

    return df

def get_heart_rate_data(conn: Connection):
    df = pd.read_sql("SELECT * FROM heart_rate_table", con=conn)
    df.columns = ['Date', 'Resting Heart Rate']
    df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
    # df['Date'] = df['Date'].dt.strftime("%d-%m-%Y")
    # df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

    return df

def get_bmi_data(conn: Connection):
    df = pd.read_sql("SELECT * FROM bmi_table", con=conn)
    df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
    # df['Date'] = df['Date'].dt.strftime("%d-%m-%Y")
    # df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

    return df

@st.cache(hash_funcs={Connection: id})
def get_connection(path: str):
    """Put the connection in cache to reuse if path does not change between Streamlit reruns.
    NB : https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
    """
    return sqlite3.connect(path, check_same_thread=False)

if __name__ == "__main__":
    main()