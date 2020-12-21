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
import datetime
import plotly.graph_objects as go

URI_SQLITE_DB = "lwinhealthrecords.db"

def main():
    st.title("My Health Tracker")
    st.markdown("Use this web application to update and visualise your health records.")    
    conn = get_connection(URI_SQLITE_DB)
    init_db(conn)
    
    health_record = st.selectbox("Select health record to update:", ["Blood Pressure", "Resting Heart Rate", "Body Mass Index"])
    if health_record == "Blood Pressure":

        input_ex = st.beta_expander("Input")
        a1, a2, a3 = input_ex.beta_columns(3)
        
        date = a1.date_input('Enter date of measurement:', datetime.date.today(), key='1')
        date = date.strftime("%d %b %Y")
        lower = a2.slider("Enter diastolic (lower) blood pressure (mmHg):", 40, 200)
        upper = a3.slider("Enter systolic (upper) blood pressure (mmHg):", 40, 200)
        
        if input_ex.button("Save record", key='1'):
            conn.execute(f"INSERT INTO blood_pressure_table (Date, Lower, Upper) VALUES (?, ?, ?)", (date, lower, upper))
            conn.commit()
        
        output_ex = st.beta_expander("Output")
        
        view_mode = output_ex.radio("Select view mode:", ["Table", "Chart"], key='1')
        df_blood_pressure = get_blood_pressure_data(conn)
        
        if view_mode == "Table":
            output_ex.table(df_blood_pressure)        
        else:
            fig1 = plot_blood_pressure(df_blood_pressure)
            output_ex.plotly_chart(fig1)
            
            fig2 = plot_blood_pressure_line(df_blood_pressure)
            output_ex.plotly_chart(fig2)
            
    
    elif health_record == "Resting Heart Rate":
        input_ex = st.beta_expander("Input")
        b1, b2 = input_ex.beta_columns(2)
        date = b1.date_input('Enter date of measurement:', datetime.date.today(), key='2')
        date = date.strftime("%d %b %Y")   
        heart_rate = b2.slider("Enter resting heart rate (beats per minute):", 40, 150)

        if input_ex.button("Save record", key='2'):
            conn.execute(f"INSERT INTO heart_rate_table (Date, HeartRate) VALUES (?, ?)", (date, heart_rate))
            conn.commit()
        
        output_ex = st.beta_expander("Output")
        view_mode = output_ex.radio("Select view mode:", ["Table", "Chart"], key='2')
        df_heart_rate = get_heart_rate_data(conn)
        
        if view_mode == "Table":
            output_ex.table(df_heart_rate)
            
        else:
            fig = plot_heart_rate(df_heart_rate)
            output_ex.plotly_chart(fig)

    elif health_record == "Body Mass Index":
        input_ex = st.beta_expander("Input")
        c1, c2, c3 = input_ex.beta_columns(3)
        date = c1.date_input('Enter date of measurement:', datetime.date.today(), key='3')
        date = date.strftime("%d %b %Y")   
        weight = c2.slider("Enter weight (kg):", 63.0, 75.0, value=67.3, step=0.1)
        weight = round(weight, 1)
        height = c3.slider("Enter height (m):", 1.6, 1.8, value=1.72, step=0.01)
        height = round(height, 2)
        bmi = round(weight / (height**2), 1)
        bmi1, bmi2, bmi3 = input_ex.beta_columns(3)
        bmi1.write("Your BMI is ")
        bmi2.header(str(bmi))
        
        if input_ex.button("Save record", key='3'):
            conn.execute(f"INSERT INTO bmi_table (Date, Weight, Height, BMI) VALUES (?, ?, ?, ?)", (date, weight, height, bmi))
            conn.commit()
            
        output_ex = st.beta_expander("Output")
        view_mode = output_ex.radio("Select view mode:", ["Table", "Chart"], key='3')
        df_bmi = get_bmi_data(conn)
        
        if view_mode == "Table":
            output_ex.table(df_bmi)
            
        else:
            fig1 = plot_weight(df_bmi) # STOPPED HERE
            fig2 = plot_bmi(df_bmi)
            output_ex.plotly_chart(fig1)
            output_ex.plotly_chart(fig2)

@st.cache
def plot_heart_rate(data):
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Resting Heart Rate']), 
        connectgaps=True
    ))

    fig.update_yaxes(
            title_text = "Resting Heart Rate (beats per minute)")

    fig.update_layout(
        title="Resting Heart Rate")

    return fig

@st.cache
def plot_weight(data):
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Weight']), 
        connectgaps=True 
    ))

    fig.update_yaxes(
            title_text = "Weight (kg)")

    fig.update_layout(
        title="Weight")
    
    return fig

@st.cache
def plot_bmi(data):
    
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

@st.cache
def plot_blood_pressure(data):
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
        connectgaps=False
    ))
    
    fig.update_yaxes(
            title_text = "Blood Pressure (mmHg)")
    
    fig.update_layout(
        title="Blood Pressure")
    
    return fig

@st.cache
def plot_blood_pressure_line(data):
                             
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Diastolic (Lower)']),
        name='Diastolic Blood Pressure',
        connectgaps=True # override default to connect the gaps
    ))
    
    fig.add_trace(go.Scatter(
        x=list(data['Date']),
        y=list(data['Systolic (Upper)']), 
        name='Systolic Blood Pressure',
        connectgaps=True # override default to connect the gaps
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
    return df

def get_heart_rate_data(conn: Connection):
    df = pd.read_sql("SELECT * FROM heart_rate_table", con=conn)
    df.columns = ['Date', 'Resting Heart Rate']
    return df

def get_bmi_data(conn: Connection):
    df = pd.read_sql("SELECT * FROM bmi_table", con=conn)
    return df

@st.cache(hash_funcs={Connection: id})
def get_connection(path: str):
    """Put the connection in cache to reuse if path does not change between Streamlit reruns.
    NB : https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
    """
    return sqlite3.connect(path, check_same_thread=False)

if __name__ == "__main__":
    main()