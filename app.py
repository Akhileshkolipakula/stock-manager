# app.py

import streamlit as st
import psycopg2
import pandas as pd
import hashlib
from datetime import date
import os

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        connect_timeout=5
    )


conn = get_conn()
conn.autocommit = True
cur = conn.cursor()


# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Soda Stock Manager",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>

/* Main container */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Table styling */
.dataframe {
    border: 1px solid #ddd !important;
    border-radius: 8px;
    overflow: hidden;
}

/* Header */
.dataframe thead th {
    background-color: #f5f7fa;
    font-weight: 600;
    text-align: center;
    border-bottom: 1px solid #ccc;
}

/* Cells */
.dataframe td {
    padding: 8px !important;
    text-align: center;
    border-bottom: 1px solid #eee;
}

/* Buttons */
.stButton > button {
    border-radius: 6px;
    padding: 6px 14px;
}

/* Inputs */
input, textarea, select {
    border-radius: 6px !important;
}

</style>
""", unsafe_allow_html=True)

LOW_STOCK_LIMIT = 10

# ---------------- TABLES ----------------

def create_tables():

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS flavors(
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        active BOOLEAN DEFAULT TRUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        flavor_id INTEGER REFERENCES flavors(id),
        stock INTEGER DEFAULT 0,
        PRIMARY KEY(flavor_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id SERIAL PRIMARY KEY,
        name TEXT,
        phone TEXT,
        shop TEXT,
        area TEXT,
        active BOOLEAN DEFAULT TRUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id SERIAL PRIMARY KEY,
        customer_id INTEGER,
        total_boxes INTEGER,
        sale_date TEXT,
        created_by TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sale_items(
        id SERIAL PRIMARY KEY,
        sale_id INTEGER,
        flavor_id INTEGER,
        quantity INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS returns(
        id SERIAL PRIMARY KEY,
        customer_name TEXT,
        return_date TEXT,
        returned_boxes INTEGER,
        damaged_boxes INTEGER,
        damaged_bottles INTEGER,
        note TEXT,
        created_by TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs(
        id SERIAL PRIMARY KEY,
        username TEXT,
        action TEXT,
        log_date TEXT
    )
    """)


create_tables()


# ---------------- HELPERS ----------------

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()


def log(action):
    cur.execute("""
    INSERT INTO activity_logs(username,action,log_date)
    VALUES(%s,%s,%s)
    """, (
        st.session_state.user["username"],
        action,
        date.today().isoformat()
    ))


def get_df(q, params=None):
    return pd.read_sql(q, conn, params=params)

def is_mobile():
    return st.session_state.get("is_mobile", False)


# ---------------- UI THEME ----------------

st.markdown("""
<style>

/* App Background */
.stApp {
    background: linear-gradient(135deg, #f8fafc, #eef2f7);
    font-family: "Segoe UI", sans-serif;
}

/* Main container */
.block-container {
    padding: 2rem 2rem 4rem 2rem;
    max-width: 1200px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b, #0f172a);
    color: white;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Sidebar title */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-weight: 600;
}

/* Page Titles */
h1, h2, h3 {
    color: #0f172a;
    font-weight: 600;
}

/* Inputs */
input, textarea, select {
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    padding: 8px !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
    transition: 0.2s;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af);
    transform: scale(1.02);
}

/* Delete Buttons */
button[kind="secondary"] {
    background: #dc2626 !important;
}

/* Data Tables */
[data-testid="stDataFrame"] {
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Table Header */
thead tr th {
    background: #e2e8f0 !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Table Rows */
tbody tr:nth-child(even) {
    background-color: #f8fafc;
}

tbody tr:hover {
    background-color: #e0f2fe !important;
}

/* Cards */
.metric-box {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* Alerts */
.stAlert {
    border-radius: 10px;
}

/* Success */
div[data-baseweb="notification"] {
    border-radius: 10px;
}

/* Mobile Optimization */
@media (max-width: 768px) {

    .block-container {
        padding: 1rem;
    }

    h1 {
        font-size: 1.4rem;
    }

    h2 {
        font-size: 1.2rem;
    }

    .stButton>button {
        width: 100%;
        margin-top: 5px;
    }

    input, select {
        width: 100% !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------- INIT ADMIN ----------------

cur.execute("SELECT COUNT(*) FROM users")
if cur.fetchone()[0] == 0:
    cur.execute("""
    INSERT INTO users(username,password,role)
    VALUES(%s,%s,%s)
    """, ("admin", hash_pass("admin123"), "admin"))


# ---------------- SESSION ----------------

if "user" not in st.session_state:
    st.session_state.user = None


# ---------------- LOGIN ----------------

def login_page():

    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        cur.execute("""
        SELECT id,role FROM users
        WHERE username=%s AND password=%s
        """, (u, hash_pass(p)))

        r = cur.fetchone()

        if r:
            st.session_state.user = {
                "id": r[0],
                "username": u,
                "role": r[1]
            }
            st.rerun()

        else:
            st.error("Invalid Login")


if not st.session_state.user:
    login_page()
    st.stop()


# ---------------- SIDEBAR ----------------

st.sidebar.title("🥤 Soda Manager")
st.sidebar.write("User:", st.session_state.user["username"])

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()


ROLE = st.session_state.user["role"]


if ROLE == "admin":
    pages = [
        "Dashboard",
        "Flavors",
        "Add Stock",
        "Record Sale",
        "Returns",
        "Customers",
        "Users",
        "Admin Activity"
    ]
else:
    pages = [
        "Dashboard",
        "Record Sale",
        "Returns",
        "Customers"
    ]


page = st.sidebar.radio("Menu", pages)


# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("📊 Dashboard")

    df = get_df("""
        SELECT
            f.name,
            COALESCE(i.stock,0) AS stock
        FROM flavors f
        LEFT JOIN inventory i ON f.id=i.flavor_id
        WHERE f.active=TRUE
        ORDER BY f.name
        """)

    if df.empty:

        st.info("No stock yet")

    else:

        # Low stock flag
        df["Low"] = df["stock"] < LOW_STOCK_LIMIT

        # Metrics
        total_stock = int(df["stock"].sum())
        low_count = int(df["Low"].sum())

        # ---------- CARDS ----------
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <h3>📦 Total Stock</h3>
                <h1>{total_stock}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <h3>⚠️ Low Stock</h3>
                <h1>{low_count}</h1>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------- MAIN TABLE ----------
        st.subheader("📦 Stock Overview")

        st.dataframe(
            df[["name", "stock", "Low"]],
            use_container_width=True,
            height=400
        )

        # ---------- LOW STOCK ALERT ----------
        low = df[df["Low"] == True]

        if not low.empty:

            st.subheader("⚠️ Low Stock Alert")

            st.dataframe(
                low[["name", "stock"]],
                use_container_width=True
            )

# ---------------- FLAVORS ----------------

elif page == "Flavors":

    if ROLE != "admin":
        st.stop()

    st.title("🧃 Flavors")

    with st.form("flavor_form"):

        name = st.text_input("New Flavor")

        add = st.form_submit_button("Add")

    if add and name.strip():

        fname = name.strip()

        # Check if flavor exists (even inactive)
        cur.execute("""
        SELECT id, active FROM flavors WHERE name=%s
        """, (fname,))

        row = cur.fetchone()

        if row:

            fid, active = row

            if not active:
                # Reactivate flavor and reset stock
                cur.execute("""
                UPDATE flavors SET active=TRUE WHERE id=%s
                """, (int(fid),))

                cur.execute("""
                UPDATE inventory SET stock=0 WHERE flavor_id=%s
                """, (int(fid),))

                log(f"Reactivated flavor {fname}")

                st.success("Flavor reactivated with 0 stock")
                st.rerun()

            else:
                st.error("Flavor already exists")

        else:

            # New flavor
            cur.execute("""
            INSERT INTO flavors(name)
            VALUES(%s)
            RETURNING id
            """, (fname,))

            fid = cur.fetchone()[0]

            cur.execute("""
            INSERT INTO inventory(flavor_id,stock)
            VALUES(%s,0)
            """, (int(fid),))

            log(f"Added flavor {fname}")

            st.success("Flavor added")
            st.rerun()

    st.subheader("📋 Flavor List")

    df = get_df("""
    SELECT f.id,f.name,i.stock
    FROM flavors f
    LEFT JOIN inventory i ON f.id=i.flavor_id
    WHERE f.active=TRUE
    ORDER BY f.name
    """)

    if df.empty:

        st.info("No flavors yet")

    else:

        for _, r in df.iterrows():

            c1, c2, c3 = st.columns([3,2,1])

            c1.write(r["name"])
            c2.write(f"Stock: {r['stock']}")

            if c3.button("❌", key=f"fl_{r['id']}"):

                cur.execute("""
                UPDATE flavors SET active=FALSE WHERE id=%s
                """, (int(r["id"]),))

                log(f"Deleted flavor {r['name']}")

                st.rerun()

# ---------------- ADD STOCK ----------------

elif page == "Add Stock":

    if ROLE != "admin":
        st.stop()

    st.title("🏭 Add Stock")

    df = get_df("SELECT * FROM flavors WHERE active=TRUE")

    f = st.selectbox("Flavor", df["name"])

    qty = st.number_input("Quantity", 1, step=1)

    if st.button("Add Stock"):

        fid = int(df[df["name"] == f]["id"].values[0])

        cur.execute("""
        UPDATE inventory
        SET stock = stock + %s
        WHERE flavor_id=%s
        """, (qty, fid))

        log(f"Added {qty} to {f}")

        st.success("Updated")
        st.rerun()

        st.subheader("📦 Current Stock")

    stock_df = get_df("""
        SELECT f.name,i.stock
        FROM flavors f
        JOIN inventory i ON f.id=i.flavor_id
        WHERE f.active=TRUE
        ORDER BY f.name
        """)

    if stock_df.empty:
        st.info("No stock yet")
    else:
        st.dataframe(
            stock_df,
            use_container_width=True,
            height=300
        )


# ---------------- RECORD SALE ----------------

elif page == "Record Sale":

    st.title("🧾 Record Sale")

    customers = get_df("SELECT * FROM customers WHERE active=TRUE")

    stock = get_df("""
    SELECT f.id,f.name,i.stock
    FROM flavors f
    JOIN inventory i ON f.id=i.flavor_id
    WHERE f.active=TRUE
    """)

    # -------- Sale Form --------

    if customers.empty or stock.empty:

        st.warning("Add customers and stock first.")
        st.stop()

    cust = st.selectbox("Customer", customers["name"])

    boxes = st.number_input("Total Boxes Given", 0, step=1)

    items = []

    st.subheader("Select Items")

    for _, r in stock.iterrows():

        label = f"{r['name']} (Available: {r['stock']})"

        q = st.number_input(
            label,
            0,
            int(r["stock"]),
            key=f"sale_{r['id']}"
        )

        if q > 0:
            items.append((r["id"], r["name"], q))

    # -------- Save Sale --------

    if st.button("Save Sale"):

        if not items:

            st.error("Select at least one item")
            st.stop()

        cid = int(
            customers[customers["name"] == cust]["id"].values[0]
        )

        # Insert sale
        cur.execute("""
        INSERT INTO sales(customer_id,total_boxes,sale_date,created_by)
        VALUES(%s,%s,%s,%s)
        RETURNING id
        """, (
            cid,
            int(boxes),
            date.today().isoformat(),
            st.session_state.user["username"]
        ))

        sid = cur.fetchone()[0]

        # Insert items + update stock
        for fid, name, q in items:

            cur.execute("""
            INSERT INTO sale_items(sale_id,flavor_id,quantity)
            VALUES(%s,%s,%s)
            """, (sid, fid, int(q)))

            cur.execute("""
            UPDATE inventory
            SET stock = stock - %s
            WHERE flavor_id=%s
            """, (int(q), fid))

        log(f"Sale to {cust}")

        st.success("Sale recorded successfully")
        st.rerun()

    # -------- Sales History --------

    st.subheader("📋 Sales History")

    sales_df = get_df("""
    SELECT
        s.sale_date,
        c.name AS customer,
        f.name AS flavor,
        si.quantity,
        s.total_boxes,
        s.created_by
    FROM sales s
    JOIN customers c ON s.customer_id = c.id
    JOIN sale_items si ON s.id = si.sale_id
    JOIN flavors f ON si.flavor_id = f.id
    ORDER BY s.id DESC
    LIMIT 50
    """)

    if sales_df.empty:

        st.info("No sales recorded yet.")

    else:

        sales_df.columns = [
            "Date",
            "Customer",
            "Flavor",
            "Quantity",
            "Boxes Given",
            "Staff"
        ]

        st.dataframe(
            sales_df,
            use_container_width=True,
            height=400
        )

# ---------------- RETURNS ----------------

elif page == "Returns":

    st.title("↩️ Returns")

    custs = get_df("SELECT name FROM customers WHERE active=TRUE")

    cname = st.selectbox("Customer", custs["name"])

    rbox = st.number_input("Returned Boxes", 0)
    dbox = st.number_input("Damaged Boxes", 0)
    dbot = st.number_input("Damaged Bottles", 0)

    note = st.text_input("Note")

    if st.button("Save Return"):

        cur.execute("""
        INSERT INTO returns(
            customer_name,
            return_date,
            returned_boxes,
            damaged_boxes,
            damaged_bottles,
            note,
            created_by
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (
            cname,
            date.today().isoformat(),
            rbox,
            dbox,
            dbot,
            note,
            st.session_state.user["username"]
        ))

        log(f"Return from {cname}")

        st.success("Saved")
        st.rerun()
        st.subheader("History")

    df = get_df("SELECT * FROM returns ORDER BY id DESC")

    if df.empty:
        st.info("No returns recorded yet.")
    else:

        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )



# ---------------- CUSTOMERS ----------------

elif page == "Customers":

    st.title("👥 Customers")

    df = get_df("SELECT * FROM customers WHERE active=TRUE ORDER BY id DESC")

    st.subheader("➕ Add / Update Customer")

    with st.form("cust_form"):

        cid = st.selectbox(
            "Select (For Edit)",
            ["New"] + df["name"].tolist()
        )

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        shop = st.text_input("Shop")
        area = st.text_input("Area")

        save = st.form_submit_button("Save")

    # Load existing
    if cid != "New":

        row = df[df["name"] == cid].iloc[0]

        name = row["name"]
        phone = row["phone"]
        shop = row["shop"]
        area = row["area"]

    if save:

        if cid == "New":

            # Check if customer exists (even inactive)
            cur.execute("""
            SELECT id, active FROM customers WHERE name=%s
            """, (name,))

            row2 = cur.fetchone()

            if row2:

                cid2, active2 = row2

                if not active2:

                    # Reactivate and update
                    cur.execute("""
                    UPDATE customers
                    SET phone=%s, shop=%s, area=%s, active=TRUE
                    WHERE id=%s
                    """, (phone, shop, area, cid2))

                    log(f"Reactivated customer {name}")

                    st.success("Customer reactivated")
                    st.rerun()

                else:
                    st.error("Customer already exists")

            else:

                # New customer
                cur.execute("""
                INSERT INTO customers(name,phone,shop,area)
                VALUES(%s,%s,%s,%s)
                """, (name, phone, shop, area))

                log(f"Added customer {name}")

        else:

            cur.execute("""
            UPDATE customers
            SET name=%s, phone=%s, shop=%s, area=%s
            WHERE id=%s
            """, (
                name, phone, shop, area,
                int(row["id"])
            ))

            log(f"Updated customer {name}")

        st.success("Saved")
        st.rerun()

    st.subheader("📋 Customer List")

    for _, r in df.iterrows():

        c1, c2, c3, c4, c5 = st.columns([2,2,2,2,1])

        c1.write(r["name"])
        c2.write(r["phone"])
        c3.write(r["shop"])
        c4.write(r["area"])

        if ROLE == "admin":

            if c5.button("❌", key=f"del_{r['id']}"):

                cur.execute("""
                UPDATE customers SET active=FALSE WHERE id=%s
                """, (int(r["id"]),))

                log(f"Deleted customer {r['name']}")

                st.rerun()

elif page == "Users":

    if ROLE != "admin":
        st.stop()

    st.title("👤 User Management")

    df = get_df("SELECT id,username,role FROM users ORDER BY id")

    st.subheader("➕ Add Staff")

    with st.form("user_form"):

        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        role = st.selectbox("Role", ["staff", "admin"])

        save = st.form_submit_button("Create")

    if save:

        if uname and pwd:

            try:

                cur.execute("""
                INSERT INTO users(username,password,role)
                VALUES(%s,%s,%s)
                """, (
                    uname,
                    hash_pass(pwd),
                    role
                ))

                log(f"Created user {uname}")

                st.success("User created")
                st.rerun()

            except:

                st.error("Username exists")

    st.subheader("📋 Existing Users")

    st.dataframe(df, use_container_width=True)

# ---------------- ADMIN ACTIVITY ----------------

elif page == "Admin Activity":

    if ROLE != "admin":
        st.stop()

    st.title("🛡️ Activity Log")

    df = get_df("SELECT * FROM activity_logs ORDER BY id DESC")

    st.dataframe(
        df,
        use_container_width=True,
        height=400
    )