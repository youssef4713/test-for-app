import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(layout="wide", page_title="سيستم الأتيليه", page_icon="👗")

# 1. الربط الأمني مع جوجل شيتس باستخدام الـ Secrets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# هنا بنقول للكود يقرأ ملف الأمان من سيرفر الاستضافة
gc_creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(gc_creds)

# فتح ملف الاكسيل
sh = gc.open("Atelier_Database")
sheet_cust = sh.worksheet("customers")
sheet_dress = sh.worksheet("dresses")
sheet_rent = sh.worksheet("rentals")

# 2. قراءة البيانات وتحويلها لـ DataFrames عشان نعمل الـ Join
df_cust = pd.DataFrame(sheet_cust.get_all_records())
df_dress = pd.DataFrame(sheet_dress.get_all_records())
df_rent = pd.DataFrame(sheet_rent.get_all_records())

st.title("Nany's Atelier")

# 3. بناء الـ rentals_enriched (الـ Join الذكي)
if not df_rent.empty and not df_cust.empty and not df_dress.empty:
    # عمل JOIN بناءً على كود العميل وكود الفستان
    enriched_df = df_rent.merge(df_cust, on="Customer_ID").merge(df_dress, on="Dress_ID")
    
    # حساب الأيام المتبقية للمناسبة (days_until_event)
    enriched_df['Event_Date'] = pd.to_datetime(enriched_df['Event_Date'])
    enriched_df['days_until_event'] = (enriched_df['Event_Date'] - datetime.now()).dt.days
    
    # حساب المالي (الباقي = سعر الإيجار - المدفوع)
    enriched_df['Remaining_Balance'] = enriched_df['Rental_Price'] - enriched_df['Paid_Amount']
    
    # عرض الـ Dashboard المالي
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الإيرادات المحصلة", f"{enriched_df['Paid_Amount'].sum()} ج.م")
    col2.metric("إجمالي البواقي برة", f"{enriched_df['Remaining_Balance'].sum()} ج.م")
    col3.metric("عدد الحجوزات النشطة", len(enriched_df))
    
    st.subheader("📋 كشف الحجوزات التفصيلي المدمج (Rentals Enriched)")
    st.dataframe(enriched_df[["Rental_ID", "Name", "Phone", "Dress_Name", "Event_Date", "days_until_event", "Rental_Price", "Paid_Amount", "Remaining_Balance", "Status_x"]])
else:
    st.info("لا توجد بيانات حجوزات مسجلة حالياً.")

# 4. شاشات الإدخال (Sidebar لعدم زحمة الشاشة)
st.sidebar.header("➕ إضافة بيانات جديدة")
menu = st.sidebar.selectbox("اختار الإجراء", ["تسجيل زبونة جديدة", "إضافة فستان جديد", "عمل حجز جديد"])

if menu == "تسجيل زبونة جديدة":
    with st.sidebar.form("cust_form"):
        c_id = f"C-{len(df_cust)+101}"
        name = st.text_input("اسم الزبونة")
        phone = st.text_input("رقم التليفون")
        chest = st.number_input("مقاس الصدر (سم)", min_value=0)
        waist = st.number_input("مقاس الوسط (سم)", min_value=0)
        hips = st.number_input("مقاس الأرداف (سم)", min_value=0)
        length = st.number_input("الطول الكلي (سم)", min_value=0)
        notes = st.text_area("ملاحظات")
        submit = st.form_submit_button("حفظ الزبونة")
        
        if submit:
            sheet_cust.append_row([c_id, name, phone, chest, waist, hips, length, notes])
            st.sidebar.success("تم الحفظ بنجاح! ريفريش للشاشة.")

elif menu == "إضافة فستان جديد":
    with st.sidebar.form("dress_form"):
        d_id = f"D-{len(df_dress)+101}"
        d_name = st.text_input("اسم / وصف الفستان")
        cat = st.selectbox("الفئة", ["زفاف", "سواريه"])
        size = st.text_input("المقاس (S, M, L, XL)")
        price = st.number_input("سعر الإيجار", min_value=0)
        status = st.selectbox("الحالة الحالية", ["متاح", "مؤجر", "في التنظيف"])
        submit = st.form_submit_button("حفظ الفستان")
        
        if submit:
            sheet_dress.append_row([d_id, d_name, cat, size, price, status])
            st.sidebar.success("تم حفظ الفستان!")

elif menu == "عمل حجز جديد":
    with st.sidebar.form("rent_form"):
        r_id = f"R-{len(df_rent)+1001}"
        # اختيار العميل والفستان من الداتا المتاحة لمنع الأخطاء
        cust_opt = dict(zip(df_cust['Name'], df_cust['Customer_ID'])) if not df_cust.empty else {}
        dress_opt = dict(zip(df_dress['Dress_Name'], df_dress['Dress_ID'])) if not df_dress.empty else {}
        
        sel_cust = st.selectbox("اختر الزبونة", list(cust_opt.keys()))
        sel_dress = st.selectbox("اختر الفستان", list(dress_opt.keys()))
        event_date = st.date_input("تاريخ المناسبة")
        paid = st.number_input("المبلغ المدفوع مقدمًا", min_value=0)
        r_status = st.selectbox("حالة الحجز", ["محجوز", "تم الاستلام", "تم الإرجاع"])
        submit = st.form_submit_button("تأكيد الحجز")
        
        if submit:
            sheet_rent.append_row([r_id, cust_opt[sel_cust], dress_opt[sel_dress], str(event_date), paid, r_status])
            st.sidebar.success("تم تسجيل الحجز بنجاح!")
