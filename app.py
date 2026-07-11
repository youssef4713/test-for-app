import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1️⃣ إعدادات الواجهة
st.set_page_config(page_title="Lobna's System", page_icon="👗", layout="wide")

# 2️⃣ دالة التحميل الذكي (بتخزن الداتا في الكاش عشان السرعة)
@st.cache_data(ttl=600) # الكاش بيفضل 10 دقايق عشان السيستم ميبطأش
def load_data():
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings")
    
    # جلب البيانات
    cust_data = customers_sheet.get_all_values()
    book_data = bookings_sheet.get_all_values()
    
    df_cust = pd.DataFrame(cust_data[1:], columns=cust_data[0]) if len(cust_data) > 1 else pd.DataFrame()
    df_book = pd.DataFrame(book_data[1:], columns=book_data[0]) if len(book_data) > 1 else pd.DataFrame()
    
    # تنظيف الأعمدة المتكررة
    df_cust = df_cust.loc[:, ~df_cust.columns.duplicated()]
    df_book = df_book.loc[:, ~df_book.columns.duplicated()]
    
    return df_cust, df_book

# استدعاء الدالة
df_cust, df_book = load_data()

# 3️⃣ القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["📊 لوحة التحكم", "➕ تسجيل زبونة", "🔍 البحث"])

# 4️⃣ الصفحات
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم")
    st.write("إحصائيات سريعة...")
    st.dataframe(df_cust)

elif choice == "➕ تسجيل زبونة":
    st.title("➕ تسجيل زبونة")
    with st.form("customer_form", clear_on_submit=True):
        name = st.text_input("الاسم")
        phone = st.text_input("التليفون")
        submitted = st.form_submit_button("حفظ")
        if submitted:
            st.success("تم الحفظ! (قم بعمل Refresh للصفحة بعد 10 دقائق لرؤية التحديث)")

elif choice == "🔍 البحث":
    st.title("🔍 محرك البحث")
    search_query = st.text_input("ادخل الاسم للبحث:")
    
    if not df_cust.empty:
        df_search = df_cust.copy()
        result = df_search[df_search['Name'].str.contains(search_query, case=False, na=False)]
        if not result.empty:
            for index, row in result.iterrows():
                with st.expander(f"👤 {row['Name']}"):
                    st.write(f"**الصدر:** {row.get('Chest', '—')}")
        else:
            st.error("لا توجد نتائج.")
