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

# دالة سحب البيانات
def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        return pd.DataFrame(raw_data[1:], columns=raw_data[0])
    return pd.DataFrame()

# القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["📊 لوحة التحكم", "➕ إضافة عميلة وطلب", "✏️ تعديل بيانات"])

# 1️⃣ لوحة التحكم
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة تحكم الأتيليه")
    df_book = get_data(bookings_sheet)
    if not df_book.empty:
        df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
        df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)
        
        c1, c2 = st.columns(2)
        c1.metric("إجمالي التحصيل", f"{df_book['Paid'].sum():,.0f} ج.م")
        c2.metric("إجمالي المتبقي", f"{df_book['Remaining'].sum():,.0f} ج.م")
    st.dataframe(df_book)

# 2️⃣ إضافة عميلة وطلب (مدمجة)
elif choice == "➕ إضافة عميلة وطلب":
    st.title("➕ إضافة بيانات جديدة")
    with st.form("new_entry_form", clear_on_submit=True):
        tab1, tab2, tab3 = st.tabs(["البيانات الشخصية", "المقاسات", "تفاصيل الطلب"])
        
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
        
        submitted = st.form_submit_button("💾 حفظ البيانات")
        if submitted:
            # إضافة للزبائن
            customers_sheet.append_row(["QS-NEW", name, phone, chest, waist, hips, length, neck_to_waist, waist_to_bottom, crotch, inseam, thigh_width, thigh_length_k, chest_dart, sleeve_width, notes, datetime.now().strftime("%Y-%m-%d")])
            # إضافة للطلبات
            bookings_sheet.append_row(["BK-NEW", name, phone, "فستان", total_price, paid, (total_price - paid), status, datetime.now().strftime("%Y-%m-%d")])
            st.success("تم تسجيل العميل والطلب بنجاح!")

# 3️⃣ تعديل البيانات
elif choice == "✏️ تعديل بيانات":
    st.title("✏️ البحث والتعديل")
    df_cust = get_data(customers_sheet)
    search_name = st.text_input("ابحث باسم الزبونة للتعديل:")
    
    if search_name:
        result = df_cust[df_cust['Name'].str.contains(search_name, case=False, na=False)]
        if not result.empty:
            for idx, row in result.iterrows():
                # عشان نعدل في الشيت لازم نعرف رقم الصف (idx + 2 لأن الشيت بيبدأ من 1 وفيه هيدر)
                row_number = idx + 2
                with st.expander(f"تعديل بيانات: {row['Name']}"):
                    with st.form(f"edit_form_{row_number}"):
                        new_phone = st.text_input("التليفون", value=row['Phone'])
                        new_chest = st.text_input("دوران الصدر", value=row['Chest'])
                        new_notes = st.text_area("ملاحظات", value=row['Notes'])
                        
                        if st.form_submit_button("حفظ التعديلات"):
                            customers_sheet.update_cell(row_number, 3, new_phone) # رقم 3 هو عمود التليفون
                            customers_sheet.update_cell(row_number, 4, new_chest) # رقم 4 عمود الصدر
                            customers_sheet.update_cell(row_number, 16, new_notes) # رقم 16 عمود الملاحظات
                            st.success("تم التحديث!")
        else:
            st.error("لم يتم العثور على زبونة بهذا الاسم.")
