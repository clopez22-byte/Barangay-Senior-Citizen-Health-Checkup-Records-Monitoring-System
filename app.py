import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib
from datetime import datetime, date, timedelta

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Barangay Senior Citizen Health Monitoring",
    page_icon="🏥",
    layout="wide"
)

DB_NAME = "barangay_health.db"

# ==========================================
# HOSPITAL RED & CLINICAL WHITE THEME (CSS)
# ==========================================
st.markdown("""
<style>
    /* Main App Background & Headers */
    .stApp {
        background-color: #FFF8F8;
    }
    h1, h2, h3 {
        color: #990011 !important;
    }

    /* Sidebar Styling - Deep Hospital Crimson */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #990011 0%, #7A000E 100%);
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.25);
    }

    /* Primary Buttons - Hospital Red */
    .stButton > button, .stFormSubmitButton > button {
        background-color: #C8102E !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: 0.2s ease-in-out;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #990011 !important;
        box-shadow: 0 4px 12px rgba(200, 16, 46, 0.3);
    }

    /* Form Containers - Crisp White Card with Red Top Accent */
    [data-testid="stForm"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border-top: 4px solid #C8102E;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    /* Custom Colored Hospital KPI Metric Cards */
    .kpi-card {
        padding: 18px 20px;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 0.88rem;
        font-weight: 700;
        opacity: 0.92;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-crimson { background: linear-gradient(135deg, #C8102E, #E63946); }
    .kpi-navy    { background: linear-gradient(135deg, #1D3557, #457B9D); }
    .kpi-emerald { background: linear-gradient(135deg, #1B7F5C, #2A9D8F); }
    .kpi-amber   { background: linear-gradient(135deg, #D97706, #F59E0B); }

    /* Login Banner Card */
    .login-banner {
        background: linear-gradient(135deg, #990011, #C8102E);
        padding: 28px 32px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 6px 18px rgba(153, 0, 17, 0.25);
        border-left: 8px solid #FFFFFF;
    }
    .login-banner h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.85rem;
    }
    .login-banner p {
        color: #FFE5E8;
        margin-top: 6px;
        margin-bottom: 0;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE & AUTHENTICATION FUNCTIONS
# ==========================================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 2. Senior Citizens Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS senior_citizens (
            senior_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            address TEXT NOT NULL,
            contact_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_number TEXT,
            date_registered TEXT NOT NULL
        )
    ''')

    # 3. Health Services Reference Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS health_services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')

    # 4. Health Checkups Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS health_checkups (
            checkup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            senior_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            checkup_date TEXT NOT NULL,
            blood_pressure TEXT,
            heart_rate INTEGER,
            temperature REAL,
            weight_kg REAL,
            observations TEXT,
            recorded_by TEXT NOT NULL,
            FOREIGN KEY (senior_id) REFERENCES senior_citizens(senior_id)
        )
    ''')

    # 5. Follow-up Schedules Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS follow_up_schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            senior_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (senior_id) REFERENCES senior_citizens(senior_id)
        )
    ''')

    # Seed Default Users
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_users = [
            ("admin", hash_password("admin123"), "System Administrator", "Administrator"),
            ("bhw1", hash_password("bhw123"), "Maria Santos", "Barangay Health Worker"),
            ("nurse1", hash_password("nurse123"), "Elena Reyes, RN", "Barangay Health Nurse")
        ]
        c.executemany("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)", default_users)

    # Seed Health Services
    c.execute("SELECT COUNT(*) FROM health_services")
    if c.fetchone()[0] == 0:
        services = [
            ("General Checkup", "Routine vital signs and physical assessment"),
            ("Blood Pressure Monitoring", "Hypertension screening and tracking"),
            ("Blood Sugar Screening", "Fasting/Random glucose check"),
            ("Follow-up Visit", "Scheduled post-consultation monitoring"),
            ("Immunization / Vaccination", "Flu or pneumonia vaccine administration")
        ]
        c.executemany("INSERT INTO health_services (service_name, description) VALUES (?, ?)", services)

    # Seed Sample Senior Citizens & Records (for Capstone Demo)
    c.execute("SELECT COUNT(*) FROM senior_citizens")
    if c.fetchone()[0] == 0:
        today = datetime.now().date()
        seniors = [
            ("SC-001", "Juan Dela Cruz", "1955-04-12", "Male", "Purok 1, Brgy. San Jose", "09171234567", "Pedro Dela Cruz", "09181234567", str(today - timedelta(days=60))),
            ("SC-002", "Remedios Bautista", "1958-09-23", "Female", "Purok 3, Brgy. San Jose", "09192345678", "Ana Bautista", "09202345678", str(today - timedelta(days=45))),
            ("SC-003", "Ricardo Mendoza", "1950-11-05", "Male", "Purok 2, Brgy. San Jose", "09213456789", "Rosa Mendoza", "09223456789", str(today - timedelta(days=30)))
        ]
        c.executemany("INSERT INTO senior_citizens VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", seniors)

        checkups = [
            ("SC-001", "General Checkup", str(today - timedelta(days=10)), "120/80", 72, 36.5, 65.0, "Normal vital signs. Advised regular walking.", "Maria Santos"),
            ("SC-002", "Blood Pressure Monitoring", str(today - timedelta(days=15)), "140/90", 78, 36.7, 58.5, "Slightly elevated BP. Scheduled for follow-up.", "Elena Reyes, RN")
        ]
        c.executemany("INSERT INTO health_checkups (senior_id, service_name, checkup_date, blood_pressure, heart_rate, temperature, weight_kg, observations, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", checkups)

        schedules = [
            ("SC-001", "Follow-up Visit", str(today + timedelta(days=5)), "Scheduled", "Routine monthly check"),
            ("SC-002", "Blood Pressure Monitoring", str(today - timedelta(days=2)), "Scheduled", "Recheck blood pressure"),
            ("SC-003", "General Checkup", str(today + timedelta(days=2)), "Scheduled", "Initial health assessment")
        ]
        c.executemany("INSERT INTO follow_up_schedules (senior_id, service_name, scheduled_date, status, notes) VALUES (?, ?, ?, ?, ?)", schedules)

    conn.commit()
    conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT user_id, username, full_name, role FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    return user

def calculate_age(birth_date_str):
    bdate = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    today = date.today()
    return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))

# Initialize Database on App Load
init_db()

# ==========================================
# SESSION STATE & LOGIN SCREEN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    st.markdown("""
        <div class="login-banner">
            <h1>✚ Barangay Senior Citizen Health Checkup Records Monitoring System</h1>
            <p>Barangay Health Center Medical Records & Follow-Up Monitoring Portal</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.4])
    with col1:
        with st.form("login_form"):
            st.subheader("Authorized Personnel Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = {
                        "id": user[0],
                        "username": user[1],
                        "full_name": user[2],
                        "role": user[3]
                    }
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        with st.expander("Demo Login Credentials (Capstone Testing)"):
            st.markdown("""
            - **Administrator:** `admin` / `admin123`
            - **Health Worker:** `bhw1` / `bhw123`
            - **Health Nurse:** `nurse1` / `nurse123`
            """)
    st.stop()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
user = st.session_state.user
st.sidebar.title("✚ Health Center Portal")
st.sidebar.markdown(f"**Staff:** {user['full_name']}")
st.sidebar.markdown(f"**Role:** {user['role']}")
st.sidebar.divider()

menu_options = [
    "📊 Dashboard",
    "👴 Senior Citizen Profiles",
    "🩺 Health Checkup Records",
    "📅 Follow-Up Monitoring",
    "📑 Health Service Reports"
]
if user["role"] == "Administrator":
    menu_options.append("⚙️ User Management")

choice = st.sidebar.radio("Navigation", menu_options)

st.sidebar.divider()
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

conn = get_connection()

# ==========================================
# 1. DASHBOARD
# ==========================================
if choice == "📊 Dashboard":
    st.title("📊 Senior Citizen Health Monitoring Dashboard")
    
    seniors_df = pd.read_sql("SELECT * FROM senior_citizens", conn)
    checkups_df = pd.read_sql("SELECT * FROM health_checkups", conn)
    schedules_df = pd.read_sql("SELECT * FROM follow_up_schedules", conn)
    
    today_str = str(date.today())
    upcoming_count = len(schedules_df[(schedules_df["status"] == "Scheduled") & (schedules_df["scheduled_date"] >= today_str)])
    overdue_count = len(schedules_df[(schedules_df["status"] == "Scheduled") & (schedules_df["scheduled_date"] < today_str)])
    
    # Hospital Color-Coded KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="kpi-card kpi-navy">
                <div class="kpi-title">Registered Seniors</div>
                <div class="kpi-value">{len(seniors_df)}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="kpi-card kpi-emerald">
                <div class="kpi-title">Completed Checkups</div>
                <div class="kpi-value">{len(checkups_df)}</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">Upcoming Checkups</div>
                <div class="kpi-value">{upcoming_count}</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="kpi-card kpi-crimson">
                <div class="kpi-title">Overdue Follow-Ups</div>
                <div class="kpi-value">{overdue_count}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader("Recent Checkup Records")
        recent_query = """
            SELECT c.senior_id AS 'Senior ID', s.full_name AS 'Full Name', 
                   c.service_name AS 'Service', c.checkup_date AS 'Date', c.blood_pressure AS 'BP'
            FROM health_checkups c
            JOIN senior_citizens s ON c.senior_id = s.senior_id
            ORDER BY c.checkup_date DESC LIMIT 10
        """
        recent_df = pd.read_sql(recent_query, conn)
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
        
    with col_right:
        st.subheader("Services Availed Distribution")
        if not checkups_df.empty:
            service_counts = checkups_df["service_name"].value_counts().reset_index()
            service_counts.columns = ["Service", "Count"]
            fig = px.pie(
                service_counts,
                values="Count",
                names="Service",
                hole=0.45,
                color_discrete_sequence=["#C8102E", "#1D3557", "#2A9D8F", "#F59E0B", "#E63946"]
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No checkup data available yet.")

# ==========================================
# 2. SENIOR CITIZEN PROFILES
# ==========================================
elif choice == "👴 Senior Citizen Profiles":
    st.title("👴 Senior Citizen Registration & Profiles")
    
    tab1, tab2, tab3 = st.tabs(["📋 Directory", "➕ Register New Senior", "✏️ Update / Delete Profile"])
    
    with tab1:
        search = st.text_input("Search by Senior ID or Name")
        df_seniors = pd.read_sql("SELECT * FROM senior_citizens", conn)
        if not df_seniors.empty:
            df_seniors["Age"] = df_seniors["birth_date"].apply(calculate_age)
            if search:
                df_seniors = df_seniors[
                    df_seniors["senior_id"].str.contains(search, case=False) |
                    df_seniors["full_name"].str.contains(search, case=False)
                ]
            st.dataframe(df_seniors, use_container_width=True, hide_index=True)
        else:
            st.info("No senior citizens registered.")
            
    with tab2:
        with st.form("register_senior_form", clear_on_submit=True):
            st.subheader("New Senior Citizen Registration")
            col1, col2 = st.columns(2)
            with col1:
                senior_id = st.text_input("Senior Citizen ID (e.g., SC-004)*")
                full_name = st.text_input("Full Name*")
                birth_date = st.date_input("Birth Date*", min_value=date(1910, 1, 1), max_value=date(1966, 12, 31))
                gender = st.selectbox("Gender*", ["Male", "Female"])
            with col2:
                address = st.text_input("Complete Barangay Address*")
                contact_num = st.text_input("Contact Number")
                emerg_name = st.text_input("Emergency Contact Person*")
                emerg_num = st.text_input("Emergency Contact Number*")
                
            if st.form_submit_button("Register Senior Citizen"):
                if senior_id and full_name and address:
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO senior_citizens VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (senior_id.strip(), full_name.strip(), str(birth_date), gender, address, contact_num, emerg_name, emerg_num, str(date.today())))
                        conn.commit()
                        st.success(f"Successfully registered {full_name} ({senior_id})!")
                    except Exception as e:
                        st.error(f"Error: Senior ID may already exist. ({e})")
                else:
                    st.warning("Please fill in all required (*) fields.")

    with tab3:
        df_seniors = pd.read_sql("SELECT * FROM senior_citizens", conn)
        if not df_seniors.empty:
            selected_id = st.selectbox("Select Senior ID to Edit/Delete", df_seniors["senior_id"])
            record = df_seniors[df_seniors["senior_id"] == selected_id].iloc[0]
            
            with st.form("edit_senior_form"):
                e_name = st.text_input("Full Name", value=record["full_name"])
                e_address = st.text_input("Address", value=record["address"])
                e_contact = st.text_input("Contact Number", value=record["contact_number"])
                e_emerg_name = st.text_input("Emergency Contact", value=record["emergency_contact_name"])
                e_emerg_num = st.text_input("Emergency Number", value=record["emergency_contact_number"])
                
                col_u, col_d = st.columns(2)
                update_btn = col_u.form_submit_button("Update Profile", use_container_width=True)
                delete_btn = col_d.form_submit_button("Delete Record", use_container_width=True)
                
                if update_btn:
                    c = conn.cursor()
                    c.execute("""
                        UPDATE senior_citizens 
                        SET full_name=?, address=?, contact_number=?, emergency_contact_name=?, emergency_contact_number=?
                        WHERE senior_id=?
                    """, (e_name, e_address, e_contact, e_emerg_name, e_emerg_num, selected_id))
                    conn.commit()
                    st.success("Profile updated!")
                    st.rerun()
                    
                if delete_btn:
                    c = conn.cursor()
                    c.execute("DELETE FROM senior_citizens WHERE senior_id=?", (selected_id,))
                    conn.commit()
                    st.warning("Record deleted.")
                    st.rerun()

# ==========================================
# 3. HEALTH CHECKUP RECORDS
# ==========================================
elif choice == "🩺 Health Checkup Records":
    st.title("🩺 Health Checkup Records")
    st.info("ℹ️ Note: This system records vital signs and observations entered by authorized personnel. It does not diagnose diseases or prescribe medication.")
    
    tab1, tab2 = st.tabs(["➕ Record New Checkup", "📜 Checkup History"])
    
    with tab1:
        seniors_df = pd.read_sql("SELECT senior_id, full_name FROM senior_citizens", conn)
        services_df = pd.read_sql("SELECT service_name FROM health_services", conn)
        
        if seniors_df.empty:
            st.warning("Please register a senior citizen first.")
        else:
            senior_map = {f"{row['senior_id']} - {row['full_name']}": row['senior_id'] for _, row in seniors_df.iterrows()}
            
            with st.form("checkup_form", clear_on_submit=True):
                selected_senior = st.selectbox("Select Senior Citizen*", list(senior_map.keys()))
                col1, col2 = st.columns(2)
                with col1:
                    service = st.selectbox("Health Service Provided*", services_df["service_name"].tolist())
                    checkup_date = st.date_input("Checkup Date*", value=date.today())
                    bp = st.text_input("Blood Pressure (mmHg)", placeholder="e.g., 120/80")
                with col2:
                    hr = st.number_input("Heart Rate (bpm)", min_value=30, max_value=220, value=75)
                    temp = st.number_input("Temperature (°C)", min_value=34.0, max_value=42.0, value=36.5, step=0.1)
                    weight = st.number_input("Weight (kg)", min_value=20.0, max_value=200.0, value=60.0, step=0.5)
                
                observations = st.text_area("Health Observations / Remarks")
                
                st.markdown("---")
                schedule_followup = st.checkbox("Schedule a Follow-Up Visit?")
                followup_date = st.date_input("Next Follow-Up Date", value=date.today())
                followup_notes = st.text_input("Follow-Up Purpose / Notes")
                
                if st.form_submit_button("Save Checkup Record"):
                    s_id = senior_map[selected_senior]
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO health_checkups (senior_id, service_name, checkup_date, blood_pressure, heart_rate, temperature, weight_kg, observations, recorded_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (s_id, service, str(checkup_date), bp, hr, temp, weight, observations, user["full_name"]))
                    
                    if schedule_followup:
                        c.execute("""
                            INSERT INTO follow_up_schedules (senior_id, service_name, scheduled_date, status, notes)
                            VALUES (?, ?, ?, 'Scheduled', ?)
                        """, (s_id, "Follow-up Visit", str(followup_date), followup_notes))
                        
                    conn.commit()
                    st.success("Checkup record saved successfully!")

    with tab2:
        query = """
            SELECT c.checkup_id AS 'ID', c.senior_id AS 'Senior ID', s.full_name AS 'Full Name',
                   c.service_name AS 'Service', c.checkup_date AS 'Date', c.blood_pressure AS 'BP',
                   c.heart_rate AS 'HR', c.temperature AS 'Temp (°C)', c.weight_kg AS 'Weight (kg)',
                   c.observations AS 'Observations', c.recorded_by AS 'Recorded By'
            FROM health_checkups c
            JOIN senior_citizens s ON c.senior_id = s.senior_id
            ORDER BY c.checkup_date DESC
        """
        df_history = pd.read_sql(query, conn)
        st.dataframe(df_history, use_container_width=True, hide_index=True)

# ==========================================
# 4. FOLLOW-UP MONITORING
# ==========================================
elif choice == "📅 Follow-Up Monitoring":
    st.title("📅 Follow-Up Visit Monitoring & Scheduling")
    
    today_str = str(date.today())
    query = """
        SELECT f.schedule_id, f.senior_id, s.full_name, s.contact_number, 
               f.service_name, f.scheduled_date, f.status, f.notes
        FROM follow_up_schedules f
        JOIN senior_citizens s ON f.senior_id = s.senior_id
        ORDER BY f.scheduled_date ASC
    """
    df_sched = pd.read_sql(query, conn)
    
    def get_display_status(row):
        if row["status"] == "Scheduled" and row["scheduled_date"] < today_str:
            return "🚨 Overdue"
        elif row["status"] == "Scheduled":
            return "🗓️ Upcoming"
        elif row["status"] == "Completed":
            return "✅ Completed"
        return "❌ Missed"

    def color_status_row(val):
        if "Overdue" in str(val):
            return "background-color: #FADBD8; color: #990011; font-weight: bold;"
        elif "Upcoming" in str(val):
            return "background-color: #FEF5E7; color: #B9770E; font-weight: bold;"
        elif "Completed" in str(val):
            return "background-color: #D4EFDF; color: #1B7F5C; font-weight: bold;"
        elif "Missed" in str(val):
            return "background-color: #EBEDEF; color: #566573; font-weight: bold;"
        return ""

    if not df_sched.empty:
        df_sched["Monitoring Status"] = df_sched.apply(get_display_status, axis=1)
        
        filter_status = st.selectbox("Filter Visits", ["All", "🚨 Overdue", "🗓️ Upcoming", "✅ Completed", "❌ Missed"])
        if filter_status != "All":
            filtered_df = df_sched[df_sched["Monitoring Status"] == filter_status]
        else:
            filtered_df = df_sched
            
        display_cols = filtered_df[["schedule_id", "Monitoring Status", "senior_id", "full_name", "contact_number", "service_name", "scheduled_date", "notes"]]
        styled_df = display_cols.style.map(color_status_row, subset=["Monitoring Status"])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.subheader("Update Visit Status")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sched_id = st.selectbox("Select Schedule ID", df_sched["schedule_id"])
        with col2:
            new_status = st.selectbox("Mark Status As", ["Completed", "Missed", "Scheduled"])
        with col3:
            st.write("")
            st.write("")
            if st.button("Update Status", use_container_width=True):
                c = conn.cursor()
                c.execute("UPDATE follow_up_schedules SET status=? WHERE schedule_id=?", (new_status, sched_id))
                conn.commit()
                st.success("Visit status updated!")
                st.rerun()
    else:
        st.info("No follow-up schedules recorded.")

# ==========================================
# 5. HEALTH SERVICE REPORTS
# ==========================================
elif choice == "📑 Health Service Reports":
    st.title("📑 Health Service & Checkup Reports")
    
    report_type = st.radio("Select Report Period", ["Daily", "Monthly", "Yearly", "All Records"], horizontal=True)
    
    query = """
        SELECT c.checkup_date AS 'Date', c.senior_id AS 'Senior ID', s.full_name AS 'Full Name',
               s.gender AS 'Gender', c.service_name AS 'Service Provided', 
               c.blood_pressure AS 'BP', c.observations AS 'Observations', c.recorded_by AS 'Attending Staff'
        FROM health_checkups c
        JOIN senior_citizens s ON c.senior_id = s.senior_id
    """
    df_rep = pd.read_sql(query, conn)
    
    if not df_rep.empty:
        df_rep["Date_dt"] = pd.to_datetime(df_rep["Date"])
        
        if report_type == "Daily":
            sel_date = st.date_input("Select Date", value=date.today())
            df_rep = df_rep[df_rep["Date"] == str(sel_date)]
        elif report_type == "Monthly":
            col1, col2 = st.columns(2)
            sel_year = col1.selectbox("Year", sorted(df_rep["Date_dt"].dt.year.unique(), reverse=True))
            sel_month = col2.selectbox("Month", range(1, 13), index=date.today().month - 1)
            df_rep = df_rep[(df_rep["Date_dt"].dt.year == sel_year) & (df_rep["Date_dt"].dt.month == sel_month)]
        elif report_type == "Yearly":
            sel_year = st.selectbox("Year", sorted(df_rep["Date_dt"].dt.year.unique(), reverse=True))
            df_rep = df_rep[df_rep["Date_dt"].dt.year == sel_year]
            
        display_rep = df_rep.drop(columns=["Date_dt"])
        st.metric("Total Services Rendered in Period", len(display_rep))
        st.dataframe(display_rep, use_container_width=True, hide_index=True)
        
        csv = display_rep.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Report (CSV / Excel)",
            data=csv,
            file_name=f"barangay_health_report_{report_type.lower()}.csv",
            mime="text/csv"
        )
    else:
        st.info("No records available to generate reports.")

# ==========================================
# 6. USER MANAGEMENT (ADMIN ONLY)
# ==========================================
elif choice == "⚙️ User Management":
    st.title("⚙️ System User Management")
    
    users_df = pd.read_sql("SELECT user_id, username, full_name, role FROM users", conn)
    st.dataframe(users_df, use_container_width=True, hide_index=True)
    
    with st.form("add_user_form", clear_on_submit=True):
        st.subheader("Add Authorized Health Personnel")
        u_name = st.text_input("Username")
        f_name = st.text_input("Full Name & Title (e.g., Juan Reyes, BHW)")
        role = st.selectbox("Role", ["Barangay Health Worker", "Barangay Health Nurse", "Administrator"])
        pwd = st.text_input("Password", type="password")
        
        if st.form_submit_button("Create Account"):
            if u_name and f_name and pwd:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                              (u_name.strip(), hash_password(pwd), f_name.strip(), role))
                    conn.commit()
                    st.success(f"Account created for {f_name}!")
                    st.rerun()
                except Exception:
                    st.error("Username already exists.")
            else:
                st.warning("All fields are required.")

conn.close()
