import streamlit as st
import mysql.connector
from datetime import datetime

# ==============================
# DB CONNECTION
# ==============================
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1a0qaeta",   # 🔑 replace with your MySQL password
        database="super_market"     # 🔑 replace with your schema name
    )

# ==============================
# INSERT NEW ORDER
# ==============================
def insert_order(customer_name, customer_id, segment, country, state, postal_code,
                 region, category, product_name, quantity):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO orders_2
        (Customer_Name, Customer_ID, Segment, Country, State, Postal_Code, Region, Category, 
        Product_Name, Quantity, Purchase_Date, Delivered)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    values = (
        customer_name, customer_id, segment, country, state, postal_code,
        region, category, product_name, quantity,
        datetime.today().date(), "NO"   # purchase_date auto, delivered = NO
    )

    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()

# ==============================
# GET UNDELIVERED ORDERS
# ==============================
def get_undelivered_orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Customer_ID, Customer_Name, Product_Name, Quantity FROM orders_2 WHERE Delivered='NO'")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# ==============================
# UPDATE UNDELIVERED ORDER
# ==============================
def update_order(customer_id, new_product, new_quantity):
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE orders_2 SET Product_Name=%s, Quantity=%s WHERE Customer_ID=%s AND Delivered='NO'"
    cursor.execute(query, (new_product, new_quantity, customer_id))
    conn.commit()
    cursor.close()
    conn.close()

# ==============================
# MARK ORDER AS DELIVERED
# ==============================
def mark_delivered(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE orders_2 SET Delivered='YES' WHERE Customer_ID=%s AND Delivered='NO'"
    cursor.execute(query, (customer_id,))
    conn.commit()
    cursor.close()
    conn.close()

# ==============================
# GET ALL ORDERS
# ==============================
def get_orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Customer_ID, Customer_Name, Product_Name, Purchase_Date, Delivered FROM orders_2")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# ==============================
# MARK RETURN
# ==============================
def mark_return(customer_id):
    pass

# ==============================
# STREAMLIT UI
# ==============================
st.title("🛒 Super Market Order Management")

menu = st.sidebar.radio("Choose Action", 
                        ["Place New Order", "Modify Undelivered Order", "Mark Orders as Delivered", "Process Return"])

# ---------------- PLACE NEW ORDER ----------------
if menu == "Place New Order":
    st.subheader("📦 Place a New Order")

    with st.form("new_order_form"):
        customer_name = st.text_input("Customer Name")
        customer_id = st.text_input("Customer ID")
        segment = st.selectbox("Segment", ["Consumer", "Home Office", "Corporate"])
        country = st.text_input("Country")
        state = st.text_input("State")
        postal_code = st.text_input("Postal Code")
        region = st.selectbox("Region", ["West", "East", "Central", "South"])
        category = st.selectbox("Category", ["Office Supplies", "Furniture", "Technology"])
        product_name = st.text_input("Product Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)

        submitted = st.form_submit_button("Submit Order")

        if submitted:
            insert_order(customer_name, customer_id, segment, country, state, postal_code,
                         region, category, product_name, quantity)
            st.success("✅ Order placed successfully!")

# ---------------- MODIFY EXISTING UNDELIVERED ----------------
elif menu == "Modify Undelivered Order":
    st.subheader("✏️ Modify Undelivered Orders")

    orders = get_undelivered_orders()
    if not orders:
        st.info("No undelivered orders found.")
    else:
        selected = st.selectbox("Select Order by Customer ID", [o["Customer_ID"] for o in orders])
        order = next(o for o in orders if o["Customer_ID"] == selected)

        new_product = st.text_input("New Product Name", value=order["Product_Name"])
        new_quantity = st.number_input("New Quantity", min_value=1, step=1, value=order["Quantity"])

        if st.button("Update Order"):
            update_order(selected, new_product, new_quantity)
            st.success(f"✅ Order for {order['Customer_Name']} updated!")

# ---------------- MARK AS DELIVERED ----------------
elif menu == "Mark Orders as Delivered":
    st.subheader("📬 Mark Undelivered Orders as Delivered")

    orders = get_undelivered_orders()
    if not orders:
        st.info("No undelivered orders to mark delivered.")
    else:
        selected = st.selectbox("Select Order by Customer ID", [o["Customer_ID"] for o in orders])
        order = next(o for o in orders if o["Customer_ID"] == selected)

        st.write(f"**Customer:** {order['Customer_Name']}")
        st.write(f"**Product:** {order['Product_Name']}")
        st.write(f"**Quantity:** {order['Quantity']}")

        if st.button("Mark Delivered"):
            mark_delivered(selected)
            st.success(f"✅ Order for {order['Customer_Name']} marked as Delivered!")

# ---------------- PROCESS RETURNS ----------------
elif menu == "Process Return":
    st.subheader("↩️ Process Eligible Returns")

    orders = get_orders()
    if not orders:
        st.info("No orders found.")
    else:
        selected = st.selectbox("Select Order by Customer ID", [o["Customer_ID"] for o in orders])
        order = next(o for o in orders if o["Customer_ID"] == selected)

        purchase_date = order["Purchase_Date"]
        days_diff = (datetime.today().date() - purchase_date).days

        st.write(f"**Customer:** {order['Customer_Name']}")
        st.write(f"**Product:** {order['Product_Name']}")
        st.write(f"**Purchase Date:** {purchase_date}")
        st.write(f"**Days Since Purchase:** {days_diff}")
        st.write(f"**Current Status:** {order['Delivered']}")

        if order["Delivered"] == "YES" and days_diff <= 30:
            confirm = st.radio("Eligible for return. Do you want to confirm?", ["No", "Yes"])
            if confirm == "Yes":
                mark_return(selected)
                st.success("✅ Return processed successfully!")
        elif order["Delivered"] == "RETURNED":
            st.warning("⚠️ This order has already been returned.")
        elif order["Delivered"] == "NO":
            st.error("❌ This order hasn’t been delivered yet, so it cannot be returned.")
        else:
            st.error("❌ This order is not eligible for return (older than 30 days).")
