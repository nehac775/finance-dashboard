"""
Financial Dashboard (my version)

Why I built it:
---------------
I wanted to practice working with financial datasets and visualizations.
The goal was to track balances, incomes, and expenses across time.
This gave me practice with pandas, Plotly, and Streamlit layouts.

Notes & Struggles:
------------------
- My first version had charts overlapping → fixed by using st.columns().
- CSV import/export was buggy until I forced float conversions.
- At first I hardcoded sample data, then switched to uploadable CSV.
- TODO: Add authentication (so multiple users can save dashboards).
- TODO: Add comparison chart vs last month.
- TODO: Add ability to connect live to an API (e.g., stock or bank data).

"""

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Streamlit page setup ---
st.set_page_config(page_title="Financial Dashboard", page_icon="📊", layout="wide")
st.title("📊 Financial Dashboard")
st.write("Track and visualize your financial data interactively.")

# --- Data loading ---
# NOTE: I started with a hardcoded CSV, then switched to file uploader so it's more flexible.
uploaded = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded:
    try:
        df = pd.read_csv(uploaded)
        # Standardize columns → I got weird errors before when Amount wasn't float.
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        df = pd.DataFrame()
else:
    # Example placeholder data in case no file is uploaded.
    st.info("No file uploaded. Using sample data.")
    df = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=6, freq="M"),
        "Category": ["Salary", "Rent", "Groceries", "Transport", "Investment", "Other"],
        "Amount": [5000, -1500, -600, -200, 800, -300]
    })

# --- Main display ---
if df.empty:
    st.warning("No data available yet. Please upload a CSV.")
else:
    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)

    # --- Summary by category ---
    st.subheader("Summary by Category")
    try:
        category_summary = df.groupby("Category")["Amount"].sum().reset_index()
        st.dataframe(category_summary, use_container_width=True)

        fig_pie = px.pie(category_summary, names="Category", values="Amount",
                         title="Spending by Category")
        st.plotly_chart(fig_pie, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating category summary: {e}")

    # --- Trends over time ---
    st.subheader("Trends Over Time")
    try:
        if "Date" in df.columns:
            fig_line = px.line(df, x="Date", y="Amount", color="Category",
                               title="Financial Trends Over Time")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("No 'Date' column available in dataset.")
    except Exception as e:
        st.error(f"Error creating time series: {e}")

    # --- Export ---
    st.subheader("Export Processed Data")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Processed CSV", csv, "financial_data.csv", "text/csv")
