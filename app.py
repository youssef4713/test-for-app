import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="إدارة أتيليه الملكة", page_icon="👗", layout="wide")

# الاتصال بجوجل شيتس
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        # بننظف الأعمدة عشان نتفادى الـ KeyError
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df.columns = df.columns.str.strip() # إزالة أي مسافات زائدة من العناوين
        return df
    return pd.DataFrame()

# --- القائمة الجانبية ---
choice = st.sidebar.selectbox("🧭 القائمة الرئيسية:", ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "💰 الحسابات والطلبات", "🔍 تعديل المقاسات"])

# --- 2. تسجيل عميلة جديدة ---
if choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل عميلة جديدة")
    with st.form("new_customer", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("اسم الزبونة")
        phone = col2.text_input("التليفون")
        
        # ... (باقي المقاسات زي ما هي)
        if st.form_submit_button("💾 حفظ بيانات العميل"):
            customers_sheet.append_row(["QS-NEW", name, phone, "", "", "", "", "", "", "", "", "", "", "", "", "", datetime.now().strftime("%Y-%m-%d")])
            st.success("تم حفظ العميل!")

# --- 3. الحسابات والطلبات ---
elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")
    df_cust = get_data(customers_sheet)
    
    # اختيار العميل من القائمة
    st.subheader("➕ إضافة طلب جديد")
    with st.form("new_booking"):
        # اختيار اسم العميل من قائمة (عشان نضمن الاسم صح)
        customer_names = df_cust['Name'].tolist() if 'Name' in df_cust.columns else []
        selected_name = st.selectbox("اختر اسم العميل (من الداتا بيز):", customer_names)
        
        b_dress = st.text_area("تفاصيل الفستان")
        b_total = st.number_input("المبلغ الكلي", min_value=0)
        b_paid = st.number_input("المبلغ المدفوع", min_value=0)
        b_status = st.selectbox("الحالة", ["تحت التنفيذ", "جاهز", "تم التسليم"])
        
        if st.form_submit_button("حفظ الطلب"):
            bookings_sheet.append_row(["BK-NEW", selected_name, "", b_dress, b_total, b_paid, (b_total - b_paid), b_status, datetime.now().strftime("%Y-%m-%d")])
            st.success("تم حفظ الطلب!")

    st.write("---")
    df_book = get_data(bookings_sheet)
    
    if not df_book.empty and 'Name' in df_book.columns and 'Status' in df_book.columns:
        for idx, row in df_book.iterrows():
            row_idx = idx + 2
            with st.expander(f"👗 طلب: {row.get('Name', 'بدون اسم')} - {row.get('Status', 'بدون حالة')}"):
                # كود التعديل هنا...
                st.write("بيانات الطلب هنا...")
    else:
        st.warning("تأكد من تسمية الأعمدة 'Name' و 'Status' في شيت الطلبات بشكل صحيح.")
