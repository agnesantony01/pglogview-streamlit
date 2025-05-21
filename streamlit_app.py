# pgBadger-style PostgreSQL Log Analyzer in Streamlit

import streamlit as st
import pandas as pd
import re
from io import BytesIO
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

# -------------------------
# Utility Functions
# -------------------------

@st.cache_data
def parse_log(file_content):
    log_entries = []
    log_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)(?: [A-Z]+)? \[(?P<pid>\d+)\]: (?:\[.*?\])?\s*u=\[(?P<user>.*?)\] db=\[(?P<db>.*?)\] app=\[(?P<app>.*?)\].*?(?P<level>LOG|ERROR|FATAL|STATEMENT): (?P<message>.*)'
    )
    for line in file_content.splitlines():
        match = log_pattern.search(line)
        if match:
            entry = match.groupdict()
            entry['full_line'] = line
            log_entries.append(entry)

    df = pd.DataFrame(log_entries)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    return df


def filter_logs(df, filters):
    df_filtered = df.copy()
    for key, value in filters.items():
        if value:
            if key == 'date_range':
                start, end = value
                df_filtered = df_filtered[(df_filtered['timestamp'] >= start) & (df_filtered['timestamp'] <= end)]
            elif key == 'keyword':
                df_filtered = df_filtered[df_filtered['message'].str.contains(value, case=False, na=False)]
            else:
                df_filtered = df_filtered[df_filtered[key].isin(value)]
    return df_filtered


def style_log_level(val):
    return f"color: {'red' if val == 'ERROR' else 'orange' if val == 'FATAL' else 'black'}"


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Logs')
    return output.getvalue()

# -------------------------
# UI Starts Here
# -------------------------

st.set_page_config("📊PgLogView", layout="wide")
st.markdown("""
    <style>
        .css-18e3th9 { background-color: #2f2f2f; color: white; }
        .css-1d391kg { background-color: #2f2f2f; color: white; }
        .stApp { background-color: #f4f4f4; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 PgLogView")

uploaded_file = st.file_uploader("Upload your PostgreSQL log file", type=["log", "txt"])

if uploaded_file:
    content = uploaded_file.read().decode('utf-8')
    df_logs = parse_log(content)

    if df_logs.empty:
        st.error("No valid log entries found.")
    else:
        st.sidebar.header("🔍 Filters")

        filters = {
            'level': st.sidebar.multiselect("Log Level", df_logs['level'].unique().tolist(), default=df_logs['level'].unique().tolist()),
            'user': st.sidebar.multiselect("User", df_logs['user'].dropna().unique().tolist()),
            'db': st.sidebar.multiselect("Database", df_logs['db'].dropna().unique().tolist()),
            'app': st.sidebar.multiselect("Application", df_logs['app'].dropna().unique().tolist()),
            'date_range': st.sidebar.date_input("Date Range", [df_logs['timestamp'].min(), df_logs['timestamp'].max()]),
            'keyword': st.sidebar.text_input("Keyword Search")
        }

        if len(filters['date_range']) == 2:
            filters['date_range'] = tuple(pd.to_datetime(filters['date_range']))

        filtered = filter_logs(df_logs, filters)

        tabs = st.tabs(["Overview", "Connections", "Sessions", "Checkpoints", "Temp Files", "Vacuums", "Locks", "Queries", "Top", "Events", "Download"])

        with tabs[0]:
            st.metric("Total Logs", len(filtered))
            st.metric("Error Logs", len(filtered[filtered['level'] == 'ERROR']))
            st.dataframe(filtered.style.applymap(style_log_level, subset=['level']), use_container_width=True)

        with tabs[1]:
            st.subheader("Connections Over Time")
            conn_series = filtered.set_index('timestamp').resample("5min").size()
            st.line_chart(conn_series)

        with tabs[2]:
            st.subheader("Sessions by App")
            st.bar_chart(filtered['app'].value_counts())

        with tabs[3]:
            st.info("Checkpoints not explicitly parsed but can be inferred via keywords if present in logs.")

        with tabs[4]:
            st.info("Temp file data not explicitly available unless logged.")

        with tabs[5]:
            st.info("Vacuum info to be extracted from 'VACUUM' keyword logs.")
            vacuum_logs = filtered[filtered['message'].str.contains('vacuum', case=False)]
            st.dataframe(vacuum_logs)

        with tabs[6]:
            st.info("Locks info can be parsed via 'lock' keyword in messages.")
            lock_logs = filtered[filtered['message'].str.contains('lock', case=False)]
            st.dataframe(lock_logs)

        with tabs[7]:
            st.subheader("Top Query Statements")
            stmt_logs = filtered[filtered['level'] == 'STATEMENT']
            top_queries = stmt_logs['message'].value_counts().head(10)
            st.table(top_queries)

        with tabs[8]:
            st.subheader("Top Error Types")
            top_errors = filtered[filtered['level'] == 'ERROR']['message'].value_counts().head(10)
            st.table(top_errors)

        with tabs[9]:
            st.subheader("Event Heatmap")
            heatmap_df = filtered.copy()
            heatmap_df['hour'] = heatmap_df['timestamp'].dt.hour
            heatmap_df['day'] = heatmap_df['timestamp'].dt.day_name()
            pivot = heatmap_df.pivot_table(index='day', columns='hour', values='message', aggfunc='count').fillna(0)
            fig, ax = plt.subplots()
            sns.heatmap(pivot, cmap="YlGnBu", ax=ax)
            st.pyplot(fig)

        with tabs[10]:
            st.subheader("Download Logs")
            csv = filtered.to_csv(index=False).encode('utf-8')
            xlsx = to_excel(filtered)
            st.download_button("Download CSV", csv, file_name="filtered_logs.csv")
            st.download_button("Download Excel", xlsx, file_name="filtered_logs.xlsx")

else:
    st.info("Please upload a PostgreSQL log file to begin analysis.")  
