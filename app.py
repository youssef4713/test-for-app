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

# دالة سحب داتا فورية (بدون كاش لضمان السرعة والتحديث اللحظي)
def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        return pd.DataFrame(raw_data[1:], columns=raw_data[0])
    return pd.DataFrame()

# التنقل
choice = st.sidebar.selectbox("🧭 القائمة الرئيسية:", ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "🔍 بحث وتعديل"])

# --- 1. لوحة التحكم ---
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة تحكم الأتيليه")
    df_book = get_data(bookings_sheet)
    
    if not df_book.empty:
        df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
        df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي التحصيل", f"{df_book['Paid'].sum():,.0f} ج.م")
        c2.metric("إجمالي المتبقي", f"{df_book['Remaining'].sum():,.0f} ج.م")
        c3.metric("عدد الطلبات", len(df_book))
        
        st.write("### 📋 سجل الطلبات الأخير:")
        st.dataframe(df_book, use_container_width=True)
    else:
        st.info("لا توجد طلبات مسجلة بعد.")

# --- 2. تسجيل عميلة جديدة ---
elif choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل بيانات العميل والطلب")
    with st.form("new_entry", clear_on_submit=True):
        tab1, tab2, tab3 = st.tabs(["👤 البيانات الأساسية", "📐 المقاسات (14 خانة)", "💰 الحسابات والملاحظات"])
        
        with tab1:
            name = st.text_input("اسم الزبونة")
            phone = st.text_input("التليفون")
        
        with tab2:
            c1, c2, c3 = st.columns(3)
            with c1:
                chest = st.text_input("دوران الصدر")
                waist = st.text_input("دوران الوسط")
                chest_dart = st.text_input("بنسة الصدر")
                length = st.text_input("الطول الكلي")
            with c2:
                sleeve_width = st.text_input("عرض الكم")
                neck_to_waist = st.text_input("طول من الرقبة للوسط")
                waist_to_bottom = st.text_input("طول من الوسط لأسفل")
                hips = st.text_input("دوران الأرداف")
            with c3:
                crotch = st.text_input("الحجر")
                inseam = st.text_input("الحجر الداخلي")
                thigh_width = st.text_input("عرض الفخذ")
                thigh_length_k = st.text_input("طول الفخذ للركبة")
        
        with tab3:
            total_price = st.number_input("المبلغ الكلي", min_value=0)
            paid = st.number_input("المبلغ المدفوع", min_value=0)
            status = st.selectbox("حالة الطلب", ["تحت التنفيذ", "جاهز", "تم التسليم"])
            notes = st.text_area("ملاحظات")
        
        if st.form_submit_button("💾 حفظ البيانات"):
            customers_sheet.append_row(["QS-NEW", name, phone, chest, waist, hips, length, neck_to_waist, waist_to_bottom, crotch, inseam, thigh_width, thigh_length_k, chest_dart, sleeve_width, notes, datetime.now().strftime("%Y-%m-%d")])
            bookings_sheet.append_row(["BK-NEW", name, phone, "فستان", total_price, paid, (total_price - paid), status, datetime.now().strftime("%Y-%m-%d")])
            st.success("تم الحفظ!")

# --- 3. بحث وتعديل ---
elif choice == "🔍 بحث وتعديل":
    st.title("🔍 البحث وتعديل البيانات")
    search = st.text_input("ابحث باسم الزبونة:")
    df_cust = get_data(customers_sheet)
    
    if search:
        result = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        if not result.empty:
            for idx, row in result.iterrows():
                row_idx = idx + 2
                with st.expander(f"👤 {row['Name']}"):
                    with st.form(f"form_{row_idx}"):
                        c1, c2 = st.columns(2)
                        new_phone = c1.text_input("التليفون", row['Phone'])
                        new_chest = c2.text_input("دوران الصدر", row['Chest'])
                        new_notes = st.text_area("ملاحظات", row['Notes'])
                        
                        if st.form_submit_button("تحديث البيانات"):
                            customers_sheet.update_cell(row_idx, 3, new_phone)
                            customers_sheet.update_cell(row_idx, 4, new_chest)
                            customers_sheet.update_cell(row_idx, 16, new_notes)
                            st.success("تم التعديل!")
        else:
            st.warning("لم يتم العثور على نتائج.")
