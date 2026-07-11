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
        # إزالة أي مسافات زائدة من أسماء الأعمدة لمنع الـ KeyError
        df = pd.DataFrame(raw_data[1:], columns=[col.strip() for col in raw_data[0]])
        return df
    return pd.DataFrame()

# التنقل
choice = st.sidebar.selectbox("🧭 القائمة الرئيسية:", ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "💰 الحسابات والطلبات", "🔍 تعديل المقاسات"])

# --- 1. لوحة التحكم ---
if choice == "📊 لوحة التحكم":
    st.title("📊 ملخص الأتيليه المالي")
    df_book = get_data(bookings_sheet)
    if not df_book.empty:
        # تحويل الأعمدة لأرقام للعمليات الحسابية
        df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
        df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي التحصيل", f"{df_book['Paid'].sum():,.0f} ج.م")
        c2.metric("إجمالي المتبقي", f"{df_book['Remaining'].sum():,.0f} ج.م")
        c3.metric("عدد الطلبات", len(df_book))

# --- 2. تسجيل عميلة جديدة ---
elif choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل عميلة جديدة")
    # ... (كود تسجيل العميل كما هو)

# --- 3. الحسابات والطلبات (التعديل هنا) ---
elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")
    df_book = get_data(bookings_sheet)
    df_cust = get_data(customers_sheet)

    # اختيار العميل لطلب جديد
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("new_book_form"):
            customer_names = df_cust['Name'].tolist() if not df_cust.empty else []
            selected_name = st.selectbox("اختر العميل:", customer_names)
            details = st.text_area("تفاصيل الفستان")
            total = st.number_input("المبلغ الكلي", min_value=0)
            paid = st.number_input("المدفوع", min_value=0)
            
            if st.form_submit_button("حفظ الطلب"):
                bookings_sheet.append_row(["BK-NEW", selected_name, "", details, total, paid, (total-paid), "تحت التنفيذ", datetime.now().strftime("%Y-%m-%d")])
                st.success("تم الحفظ!")

    st.write("---")
    
    # عرض وتعديل الطلبات
    if not df_book.empty:
        for idx, row in df_book.iterrows():
            row_idx = idx + 2 # لأن الشيت يبدأ بصف الهيدر
            with st.expander(f"👗 طلب: {row.get('Name', 'بدون اسم')} | الحالة: {row.get('Status', 'غير محدد')}"):
                with st.form(f"edit_{row_idx}"):
                    # عرض البيانات
                    st.write(f"**العميل:** {row.get('Name')}")
                    new_status = st.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"], 
                                             index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(row.get('Status', 'تحت التنفيذ')))
                    new_paid = st.number_input("المدفوع حالياً:", value=float(row.get('Paid', 0)))
                    new_total = st.number_input("المبلغ الكلي:", value=float(row.get('Total_Price', 0)))
                    
                    if st.form_submit_button("💾 تحديث الطلب"):
                        # حساب المتبقي تلقائياً
                        remaining = new_total - new_paid
                        # تحديث الخلايا (الترتيب: Total=5, Paid=6, Remaining=7, Status=8)
                        bookings_sheet.update_cell(row_idx, 5, new_total)
                        bookings_sheet.update_cell(row_idx, 6, new_paid)
                        bookings_sheet.update_cell(row_idx, 7, remaining)
                        bookings_sheet.update_cell(row_idx, 8, new_status)
                        st.success("تم التحديث بنجاح!")

# --- 4. تعديل المقاسات ---
elif choice == "🔍 تعديل المقاسات":
    st.title("🔍 تعديل المقاسات")
    # ... (كود التعديل كما هو)
