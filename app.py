import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="نظام إدارة أتيليه الملكة", page_icon="👗", layout="wide")

# الاتصال المباشر بجوجل شيتس
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings") # تأكد من وجود هذا الشيت
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# دوال سحب البيانات
def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        return pd.DataFrame(raw_data[1:], columns=raw_data[0])
    return pd.DataFrame()

df_cust = get_data(customers_sheet)
df_book = get_data(bookings_sheet)

# تحويل البيانات لأرقام للداش بورد
if not df_book.empty:
    df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
    df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)

# القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["📊 لوحة التحكم", "➕ تسجيل فستان جديد", "🔍 بحث عن زبونة"])

# 1️⃣ لوحة التحكم (Dashboard)
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة تحكم الأتيليه")
    
    if not df_book.empty:
        total_paid = df_book['Paid'].sum()
        total_remaining = df_book['Remaining'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("إجمالي التحصيل (المدفوع)", f"{total_paid:,.0f} ج.م")
        c2.metric("إجمالي المتبقي (عند الزبائن)", f"{total_remaining:,.0f} ج.م")
        
        st.write("---")
        st.subheader("📋 أحدث الطلبات")
        st.dataframe(df_book.tail(10))
    else:
        st.info("لا توجد طلبات مسجلة بعد.")

# 2️⃣ تسجيل فستان جديد
elif choice == "➕ تسجيل فستان جديد":
    st.title("👗 تسجيل طلب فستان")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم الزبونة")
            phone = st.text_input("التليفون")
            dress_details = st.text_area("تفاصيل الفستان")
        with col2:
            total_price = st.number_input("المبلغ الكلي", min_value=0)
            paid = st.number_input("المبلغ المدفوع", min_value=0)
            remaining = total_price - paid
            st.write(f"### المتبقي: {remaining} ج.م")
            status = st.selectbox("حالة الطلب", ["تحت التنفيذ", "جاهز", "تم التسليم"])
        
        submitted = st.form_submit_button("💾 حفظ الطلب")
        if submitted:
            new_row = ["BK-NEW", name, phone, dress_details, total_price, paid, remaining, status, datetime.now().strftime("%Y-%m-%d")]
            bookings_sheet.append_row(new_row)
            st.success("تم تسجيل الطلب بنجاح!")

# 3️⃣ البحث
elif choice == "🔍 بحث عن زبونة":
    st.title("🔍 محرك البحث")
    search_query = st.text_input("ادخل اسم الزبونة:")
    
    if search_query and not df_cust.empty:
        df_search = df_cust[df_cust['Name'].str.contains(search_query, case=False, na=False)]
        if not df_search.empty:
            for _, row in df_search.iterrows():
                with st.expander(f"👤 {row['Name']}"):
                    st.write(f"**التليفون:** {row.get('Phone', '-')}")
                    # عرض المقاسات هنا لو حبيت
        else:
            st.error("لم يتم العثور على نتائج.")
