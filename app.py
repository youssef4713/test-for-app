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

# دالة سحب داتا
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
        st.dataframe(df_book, use_container_width=True)

# --- 2. تسجيل عميلة جديدة ---
elif choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل بيانات العميل والطلب")
    with st.form("new_entry", clear_on_submit=True):
        tab1, tab2, tab3 = st.tabs(["👤 البيانات الأساسية", "📐 المقاسات (14 خانة)", "💰 الحسابات"])
        with tab1:
            name = st.text_input("اسم الزبونة")
            phone = st.text_input("التليفون")
        with tab2:
            c1, c2, c3 = st.columns(3)
            chest = c1.text_input("دوران الصدر")
            waist = c1.text_input("دوران الوسط")
            chest_dart = c1.text_input("بنسة الصدر")
            length = c2.text_input("الطول الكلي")
            sleeve_width = c2.text_input("عرض الكم")
            neck_to_waist = c2.text_input("طول الرقبة للوسط")
            waist_to_bottom = c3.text_input("طول الوسط لأسفل")
            hips = c3.text_input("دوران الأرداف")
            crotch = c3.text_input("الحجر")
            inseam = c3.text_input("الحجر الداخلي")
            thigh_width = c3.text_input("عرض الفخذ")
            thigh_length_k = c3.text_input("طول الفخذ للركبة")
        with tab3:
            total_price = st.number_input("المبلغ الكلي", min_value=0)
            paid = st.number_input("المبلغ المدفوع", min_value=0)
            status = st.selectbox("حالة الطلب", ["تحت التنفيذ", "جاهز", "تم التسليم"])
            notes = st.text_area("ملاحظات")
        
        if st.form_submit_button("💾 حفظ البيانات"):
            customers_sheet.append_row(["QS-NEW", name, phone, chest, waist, hips, length, neck_to_waist, waist_to_bottom, crotch, inseam, thigh_width, thigh_length_k, chest_dart, sleeve_width, notes, datetime.now().strftime("%Y-%m-%d")])
            bookings_sheet.append_row(["BK-NEW", name, phone, "فستان", total_price, paid, (total_price - paid), status, datetime.now().strftime("%Y-%m-%d")])
            st.success("تم الحفظ!")

# --- 3. بحث وتعديل (مفصلة) ---
elif choice == "🔍 بحث وتعديل":
    st.title("🔍 البحث وتعديل البيانات")
    search = st.text_input("ابحث باسم الزبونة:")
    df_cust = get_data(customers_sheet)
    
    if search:
        result = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        if not result.empty:
            for idx, row in result.iterrows():
                row_idx = idx + 2
                with st.expander(f"👤 تعديل بيانات: {row['Name']}"):
                    with st.form(f"edit_form_{row_idx}"):
                        c1, c2, c3 = st.columns(3)
                        # تحديث البيانات الأساسية والمقاسات
                        with c1:
                            v_phone = st.text_input("التليفون", row.get('Phone', ''))
                            v_chest = st.text_input("دوران الصدر", row.get('Chest', ''))
                            v_waist = st.text_input("دوران الوسط", row.get('Waist', ''))
                            v_hips = st.text_input("دوران الأرداف", row.get('Hips', ''))
                        with c2:
                            v_len = st.text_input("الطول الكلي", row.get('Length', ''))
                            v_neck = st.text_input("طول الرقبة للوسط", row.get('Neck_to_Waist', ''))
                            v_waist_bot = st.text_input("طول الوسط لأسفل", row.get('Waist_to_Bottom', ''))
                            v_crotch = st.text_input("الحجر", row.get('Crotch', ''))
                        with c3:
                            v_inseam = st.text_input("الحجر الداخلي", row.get('Inseam', ''))
                            v_thigh = st.text_input("عرض الفخذ", row.get('Thigh_Width', ''))
                            v_thigh_k = st.text_input("طول الفخذ للركبة", row.get('Thigh_Length_K', ''))
                            v_dart = st.text_input("بنسة الصدر", row.get('Chest_Dart', ''))
                            v_sleeve = st.text_input("عرض الكم", row.get('Sleeve_Width', ''))
                        
                        v_notes = st.text_area("ملاحظات", row.get('Notes', ''))
                        
                        if st.form_submit_button("💾 تحديث كل البيانات"):
                            # تحديث كل الأعمدة (الترتيب: Name(2), Phone(3), Chest(4), Waist(5), Hips(6), Length(7)...)
                            customers_sheet.update_cell(row_idx, 3, v_phone)
                            customers_sheet.update_cell(row_idx, 4, v_chest)
                            customers_sheet.update_cell(row_idx, 5, v_waist)
                            customers_sheet.update_cell(row_idx, 6, v_hips)
                            customers_sheet.update_cell(row_idx, 7, v_len)
                            customers_sheet.update_cell(row_idx, 8, v_neck)
                            customers_sheet.update_cell(row_idx, 9, v_waist_bot)
                            customers_sheet.update_cell(row_idx, 10, v_crotch)
                            customers_sheet.update_cell(row_idx, 11, v_inseam)
                            customers_sheet.update_cell(row_idx, 12, v_thigh)
                            customers_sheet.update_cell(row_idx, 13, v_thigh_k)
                            customers_sheet.update_cell(row_idx, 14, v_dart)
                            customers_sheet.update_cell(row_idx, 15, v_sleeve)
                            customers_sheet.update_cell(row_idx, 16, v_notes)
                            st.success("تم التحديث!")
        else:
            st.warning("لم يتم العثور على نتائج.")
