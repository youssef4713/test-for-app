import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="نظام إدارة أتيليه الملكة", page_icon="👗", layout="wide")

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

# العناوين الثابتة
cust_headers = ["Customer_ID", "Name", "Phone", "Chest", "Waist", "Hips", "Length", "Neck_to_Waist", "Waist_to_Botton", "Crotch", "Inseam", "Thigh_Width", "Thigh_Length_K", "Chest_Dart", "Sleeve_Width", "Notes", "Date"]

# دالة سحب داتا فورية (بدون كاش لضمان الدقة)
def get_data():
    raw_data = customers_sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        # إزالة أي أعمدة مكررة
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    return pd.DataFrame(columns=cust_headers)

df_cust = get_data()

# القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["➕ تسجيل زبونة", "🔍 البحث"])

if choice == "➕ تسجيل زبونة":
    st.title("➕ تسجيل زبونة")
    with st.form("customer_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("اسم الزبونة")
            phone = st.text_input("التليفون")
            chest = st.text_input("Chest")
        with col2:
            waist = st.text_input("Waist")
            hips = st.text_input("Hips")
            length = st.text_input("Length")
        with col3:
            notes = st.text_input("Notes")
        
        submitted = st.form_submit_button("حفظ")
        if submitted:
            new_row = ["QS-NEW", name, phone, chest, waist, hips, length, "", "", "", "", "", "", "", "", notes, datetime.now().strftime("%Y-%m-%d")]
            customers_sheet.append_row(new_row)
            st.success("تم الحفظ بنجاح!")

elif choice == "🔍 البحث":
    st.title("🔍 محرك البحث")
    search_query = st.text_input("ادخل الاسم للبحث:")
    
    if search_query:
        df_search = df_cust.copy()
        # تحويل الأعمدة لنصوص لضمان البحث
        df_search['Name'] = df_search['Name'].astype(str)
        result = df_search[df_search['Name'].str.contains(search_query, case=False, na=False)]
        
        if not result.empty:
            for index, row in result.iterrows():
                with st.expander(f"👤 {row['Name']}"):
                    st.write(f"**التليفون:** {row.get('Phone', '-')}")
                    st.write(f"**الصدر:** {row.get('Chest', '-')}")
                    st.write(f"**الوسط:** {row.get('Waist', '-')}")
                    st.write(f"**ملاحظات:** {row.get('Notes', '-')}")
        else:
            st.error("لم يتم العثور على نتائج.")
