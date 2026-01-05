# MRR & Commercial Dashboard - Streamlit

This project consists of an interactive and automated dashboard for monitoring MRR (Monthly Recurring Revenue) metrics and Commercial performance, integrated directly with Google Sheets data.

## Key Features

Auto-Rotation: The system alternates between 5 critical visualizations every 30 seconds, ideal for fixed monitor displays (monitoring TVs).

Real-Time Integration: Robust API connection with Google Sheets using gspread.

Dynamic Visualizations:

MRR: Budgeted, Actual, and Difference KPIs with month-over-month comparisons.

Commercial: Client distribution by plans (Essential, Control, Advanced, and Total) and Churn metrics.

Revenue Graph: Annual evolution of the MRR Target.

Client Goal: Annual evolution of client count.

Churn Graph: Client loss evolution in units.

## Technical Stack

Language: Python 3.x

Web Framework: Streamlit

Data Manipulation: Pandas

Graphics: Plotly (Graph Objects)

Automation: Streamlit Autorefresh

Data Source: Google Sheets API

## Interface Adjustments (UI/UX)

The dashboard was optimized for high information density:

Custom CSS: Removal of default paddings and margins to utilize 100% of the screen width.

Inter Font: Modern typography applied globally.

Space Optimization: Surgical reduction of fonts in the Commercial section (metrics and deltas) to ensure the 4 plan cards are horizontally aligned without layout breaks.

## Configuration

#### 1. Dependencies

Ensure the necessary libraries are installed:

pip install streamlit pandas gspread gspread-dataframe plotly streamlit-autorefresh


####  2. Secrets

Google Cloud credentials must be configured in the .streamlit/secrets.toml file or in the Streamlit Cloud dashboard, following this structure:

[connections.gsheets_mrr]
type = "service_account"
project_id = "..."
private_key = "..."
client_email = "..."
spreadsheet = "SHEET_URL"


## ETL and Data

The system uses a centralized data_loader that:

Cleans Brazilian strings (R$, %, points, and commas).

Converts formatted values into usable decimal numbers.

Executes complex formulas (VLOOKUP) directly from the Sheets engine before importing the data.

Work developed for strategic subscription monitoring and annual targets.