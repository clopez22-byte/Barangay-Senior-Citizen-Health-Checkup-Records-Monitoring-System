# Barangay Senior Citizen Health Checkup Records Monitoring System

**BSIS Capstone 1 Project**

A web-based health record management system designed for Barangay Health Centers to organize senior citizen profiles, log routine health checkups, monitor upcoming or overdue follow-up visits, and generate health service reports.

## Key Features
- **Role-Based Access Control:** Separate access for Administrators, Barangay Health Workers (BHW), and Barangay Health Nurses.
- **Senior Citizen Registration & Profiles:** Full CRUD (Create, Read, Update, Delete) operations for senior citizen records and emergency contacts.
- **Health Checkup Records:** Logs checkup dates, vital signs (BP, heart rate, temperature, weight), services rendered, and observations.
- **Follow-Up Monitoring:** Automatically flags upcoming and overdue follow-up visits.
- **Health Service Reports:** Filterable daily, monthly, and yearly reports with CSV/Excel export.

## Technology Stack
- **Language:** Python
- **Framework:** Streamlit
- **Database:** SQLite
- **Data & Visualization:** Pandas, Plotly

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
