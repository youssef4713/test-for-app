import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1️⃣ إعدادات الواجهة
st.set_page_config(page_title="Lobna's System", page_icon="👗", layout="wide")

# 2️⃣ الاتصال بجوجل شيتس
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    
    # تعريف العناوين
    cust_headers = ["Customer_ID", "Name", "Phone", "Chest", "Waist", "Hips", "Length", "Neck_to_Waist", "Waist_to_Botton", "Crotch", "Inseam", "Thigh_Width", "Thigh_Length_K", "Chest_Dart", "Sleeve_Width", "Notes", "Date"]
    book_headers = ["Booking_ID", "Customer_Name", "Phone", "Dress_Code", "Total_Price", "Paid", "Remaining", "Status", "Date"]
    
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# 3️⃣ دالة قوية لجلب البيانات
def get_dataframe_safely(sheet, default_columns):
    try:
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=default_columns[:len(raw_data[0])])
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        return pd.DataFrame(columns=default_columns)
    except:
        return pd.DataFrame(columns=default_columns)

# 4️⃣ **هنا الخطوة المهمة: تعريف المتغيرات عالمياً لضمان عدم حدوث NameError**
df_cust = get_dataframe_safely(customers_sheet, cust_headers)
df_book = get_dataframe_safely(bookings_sheet, book_headers)

# 5️⃣ القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["📊 لوحة التحكم", "➕ تسجيل زبونة", "👗 تسجيل طلب", "🔍 البحث"])

# 6️⃣ الصفحات
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم")
    st.write("إحصائيات سريعة...")

elif choice == "➕ تسجيل زبونة":
    st.title("➕ تسجيل زبونة")
    with st.form("customer_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("الاسم")
            phone = st.text_input("التليفون")
            chest = st.text_input("Chest")
        # (باقي المقاسات هنا...)
        submitted = st.form_submit_button("حفظ")
        if submitted:
            row_data = ["QS-NEW", name, phone, chest, "", "", "", "", "", "", "", "", "", "", "", "", datetime.now().strftime("%Y-%m-%d")]
            customers_sheet.append_row(row_data)
            st.success("تم الحفظ!")

elif choice == "🔍 البحث":
    st.title("🔍 محرك البحث")
    search_query = st.text_input("ادخل الاسم للبحث:")
    
    # بما أن df_cust تم تعريفه في الأعلى، هذا الجزء سيعمل الآن بدون أخطاء
    if not df_cust.empty:
        df_search = df_cust.copy()
        for col in df_search.columns:
            df_search[col] = df_search[col].astype(str)
            
        result = df_search[df_search['Name'].str.contains(search_query, case=False, na=False)]
        
        if not result.empty:
            for index, row in result.iterrows():
                with st.expander(f"👤 {row['Name']}"):
                    st.write(f"**الصدر:** {row['Chest']}")
                    # (باقي التفاصيل...)
        else:
            st.error("لا توجد نتائج.")
    else:
        st.info("البيانات فارغة.")
