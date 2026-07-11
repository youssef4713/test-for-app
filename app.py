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
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# دالة سحب داتا فورية (سريعة ومباشرة)
def get_data():
    raw_data = customers_sheet.get_all_values()
    if len(raw_data) > 1:
        # بنعتمد على الصف الأول كعناوين، وباقي الصفوف كبيانات
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        return df
    return pd.DataFrame()

df_cust = get_data()

# القائمة الجانبية
choice = st.sidebar.selectbox("🧭 اختر العملية:", ["➕ تسجيل زبونة", "🔍 البحث"])

if choice == "➕ تسجيل زبونة":
    st.title("➕ تسجيل زبونة ومقاسات جديدة")
    with st.form("customer_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("اسم الزبونة")
            phone = st.text_input("التليفون")
            chest = st.text_input("دوران الصدر (Chest)")
            waist = st.text_input("دوران الوسط (Waist)")
            chest_dart = st.text_input("بنسة الصدر (Chest Dart)")
        with col2:
            length = st.text_input("الطول الكلي (Length)")
            sleeve_width = st.text_input("عرض الكم (Sleeve Width)")
            neck_to_waist = st.text_input("طول من الرقبة للوسط")
            waist_to_bottom = st.text_input("طول من الوسط لأسفل")
        with col3:
            hips = st.text_input("دوران الأرداف (Hips)")
            crotch = st.text_input("الحجر (Crotch)")
            inseam = st.text_input("الحجر الداخلي (Inseam)")
            thigh_width = st.text_input("عرض الفخذ (Thigh Width)")
            thigh_length_k = st.text_input("طول الفخذ للركبة")
        
        notes = st.text_area("ملاحظات إضافية")
        
        submitted = st.form_submit_button("💾 حفظ البيانات")
        if submitted:
            # ترتيب البيانات لازم يطابق أعمدة الشيت بالضبط
            new_row = ["QS-NEW", name, phone, chest, waist, hips, length, neck_to_waist, waist_to_bottom, crotch, inseam, thigh_width, thigh_length_k, chest_dart, sleeve_width, notes, datetime.now().strftime("%Y-%m-%d")]
            customers_sheet.append_row(new_row)
            st.success("تم الحفظ بنجاح!")

elif choice == "🔍 البحث":
    st.title("🔍 محرك البحث عن المقاسات")
    search_query = st.text_input("ادخل اسم الزبونة للبحث:")
    
    if search_query and not df_cust.empty:
        df_search = df_cust.copy()
        if 'Name' in df_search.columns:
            df_search['Name'] = df_search['Name'].astype(str)
            result = df_search[df_search['Name'].str.contains(search_query, case=False, na=False)]
            
            if not result.empty:
                for index, row in result.iterrows():
                    with st.expander(f"👤 {row.get('Name', 'بدون اسم')}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"**دوران الصدر:** {row.get('Chest', '-')}")
                            st.write(f"**دوران الوسط:** {row.get('Waist', '-')}")
                            st.write(f"**بنسة الصدر:** {row.get('Chest_Dart', '-')}")
                            st.write(f"**الطول الكلي:** {row.get('Length', '-')}")
                        with c2:
                            st.write(f"**عرض الكم:** {row.get('Sleeve_Width', '-')}")
                            st.write(f"**طول من الرقبة للوسط:** {row.get('Neck_to_Waist', '-')}")
                            st.write(f"**طول من الوسط لأسفل:** {row.get('Waist_to_Botton', '-')}")
                            st.write(f"**دوران الأرداف:** {row.get('Hips', '-')}")
                        with c3:
                            st.write(f"**الحجر:** {row.get('Crotch', '-')}")
                            st.write(f"**الحجر الداخلي:** {row.get('Inseam', '-')}")
                            st.write(f"**عرض الفخذ:** {row.get('Thigh_Width', '-')}")
                            st.write(f"**طول الفخذ للركبة:** {row.get('Thigh_Length_K', '-')}")
                        
                        st.write("---")
                        st.write(f"**ملاحظات:** {row.get('Notes', '-')}")
            else:
                st.error("لم يتم العثور على نتائج بهذا الاسم.")
