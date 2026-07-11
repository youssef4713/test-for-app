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

# --- 1. لوحة التحكم (محدثة لآخر 30 يوم) ---
if choice == "📊 لوحة التحكم":
    st.title("📊 ملخص الأتيليه المالي (آخر 30 يوم)")
    df_book = get_data(bookings_sheet)
    
    if not df_book.empty and 'Date' in df_book.columns:
        # تحويل التاريخ والبيانات المالية لأنواع صالحة للحساب
        df_book['Date'] = pd.to_datetime(df_book['Date'], errors='coerce')
        df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
        df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)
        
        # حساب تاريخ الـ 30 يوم اللي فاتوا
        thirty_days_ago = datetime.now() - pd.Timedelta(days=30)
        
        # فلترة البيانات
        df_filtered = df_book[df_book['Date'] >= thirty_days_ago]
        
        if not df_filtered.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي التحصيل", f"{df_filtered['Paid'].sum():,.0f} ج.م")
            c2.metric("إجمالي المتبقي", f"{df_filtered['Remaining'].sum():,.0f} ج.م")
            c3.metric("عدد الطلبات", len(df_filtered))
            
            st.write("---")
            st.subheader("📋 الطلبات خلال آخر 30 يوم:")
            st.dataframe(df_filtered)
        else:
            st.info("لا توجد طلبات في آخر 30 يوم.")
    else:
        st.warning("تأكد من وجود عمود 'Date' في شيت الطلبات وتنسيقه كـ YYYY-MM-DD")
# --- 2. تسجيل عميلة جديدة (النسخة الكاملة والمشغلة) ---
elif choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل عميلة جديدة")
    with st.form("new_customer", clear_on_submit=True):
        st.subheader("👤 البيانات الأساسية")
        col1, col2 = st.columns(2)
        name = col1.text_input("اسم الزبونة")
        phone = col2.text_input("التليفون")
        
        st.subheader("📐 المقاسات")
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
        notes = st.text_area("ملاحظات")
        
        if st.form_submit_button("💾 حفظ بيانات العميل"):
            customers_sheet.append_row(["QS-NEW", name, phone, chest, waist, hips, length, neck_to_waist, waist_to_bottom, crotch, inseam, thigh_width, thigh_length_k, chest_dart, sleeve_width, notes, datetime.now().strftime("%Y-%m-%d")])
            st.success(f"تم حفظ بيانات {name} بنجاح!")

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
    
# --- 4. بحث علي عميل و تعديل ---
elif choice == "🔍 بحث علي عميل و تعديل":
    st.title("🔍 بحث علي عميل و تعديل")
    
    # سحب الداتا
    df_cust = get_data(customers_sheet)
    
    # مربع البحث
    search = st.text_input("🔎 ابحث باسم العميل أو اختر من القائمة أدناه:")
    
    if not df_cust.empty:
        # لو كتبت حاجة في البحث، يفلتر، لو مفيش، يعرض الكل
        if search:
            display_df = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        else:
            display_df = df_cust
            
        if not display_df.empty:
            for idx, row in display_df.iterrows():
                # عشان يفضل الترقيم صح، بنستخدم الـ index الأصلي من الداتا فريم
                row_idx = idx + 2 
                
                with st.expander(f"👤 {row['Name']} - {row.get('Phone', '')}"):
                    with st.form(f"edit_meas_{row_idx}"):
                        c1, c2, c3 = st.columns(3)
                        # المقاسات
                        new_chest = c1.text_input("دوران الصدر", value=row.get('Chest', ''))
                        new_waist = c1.text_input("دوران الوسط", value=row.get('Waist', ''))
                        new_dart = c1.text_input("بنسة الصدر", value=row.get('Chest_Dart', ''))
                        
                        new_len = c2.text_input("الطول الكلي", value=row.get('Length', ''))
                        new_sleeve = c2.text_input("عرض الكم", value=row.get('Sleeve_Width', ''))
                        new_neck = c2.text_input("طول الرقبة للوسط", value=row.get('Neck_to_Waist', ''))
                        
                        new_waist_bot = c3.text_input("طول الوسط لأسفل", value=row.get('Waist_to_Bottom', ''))
                        new_hips = c3.text_input("دوران الأرداف", value=row.get('Hips', ''))
                        new_crotch = c3.text_input("الحجر", value=row.get('Crotch', ''))
                        
                        new_notes = st.text_area("ملاحظات", value=row.get('Notes', ''))
                        
                        if st.form_submit_button("💾 تحديث المقاسات"):
                            # التحديث بنفس ترتيب الأعمدة القديم
                            customers_sheet.update_cell(row_idx, 4, new_chest)
                            customers_sheet.update_cell(row_idx, 5, new_waist)
                            customers_sheet.update_cell(row_idx, 6, new_hips)
                            customers_sheet.update_cell(row_idx, 7, new_len)
                            # اتأكد إن الترتيب ده هو اللي موجود في الشيت بتاعك
                            st.success(f"تم تحديث بيانات {row['Name']}!")
        else:
            st.warning("لا يوجد عملاء بهذا الاسم.")
    else:
        st.info("لا توجد بيانات عملاء لعرضها.")
