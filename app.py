import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1️⃣ إعدادات واجهة الصفحة بالكامل لشكل احترافي باللغة العربية
st.set_page_config(
    page_title="Nany's Atelier",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تعديل اتجاه الواجهة لتناسب اللغة العربية
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 2rem; }
    th, td { text-align: right !important; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)


# 2️⃣ الاتصال الآمن بقاعدة بيانات جوجل شيتس باستخدام الـ Secrets
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    
    # فتح الجداول، ولو مش موجودة بالأسماء دي بيعملها تلقائياً عشان السيستم ما يضربش
    try:
        customers_sheet = sh.worksheet("customers")
    except gspread.exceptions.WorksheetNotFound:
        customers_sheet = sh.add_worksheet(title="customers", rows="1000", cols="15")
        customers_sheet.append_row(["Customer_ID", "Name", "Phone", "Chest", "Waist", "Hips", "Shoulder", "Total_Length", "Sleeve", "Notes", "Date"])
        
    try:
        bookings_sheet = sh.worksheet("bookings")
    except gspread.exceptions.WorksheetNotFound:
        bookings_sheet = sh.add_worksheet(title="bookings", rows="1000", cols="15")
        bookings_sheet.append_row(["Booking_ID", "Customer_Name", "Phone", "Dress_Code", "Total_Price", "Paid", "Remaining", "Status"])
        
except Exception as e:
    st.error(f"❌ هناك مشكلة في الاتصال بجوجل كلاود، تأكد من إعدادات الـ Secrets. الخطأ: {e}")
    st.stop()


# 3️⃣ تصميم القائمة الجانبية للتنقل (Sidebar)
st.sidebar.title("👑 لوحة تحكم الأتيليه")
st.sidebar.write("مرحباً بك في نظام الإدارة الذكي")
st.sidebar.write("---")

choice = st.sidebar.selectbox(
    "🧭 اختر الصفحة أو العملية:", 
    ["📊 لوحة التحكم الإحصائية", "➕ تسجيل زبونة جديدة", "🔍 البحث عن مقاسات زبونة"]
)


# 4️⃣ الصفحة الأولى: لوحة التحكم الإحصائية (Dashboard)
if choice == "📊 لوحة التحكم الإحصائية":
    st.title("📊 المؤشرات العامة وحالة الأتيليه الحالية")
    st.write("ملخص سريع للحسابات والحجوزات المسجلة في قاعدة البيانات:")
    
    # جلب البيانات من الشيتس
    all_customers = customers_sheet.get_all_records()
    all_bookings = bookings_sheet.get_all_records()
    
    df_cust = pd.DataFrame(all_customers)
    df_book = pd.DataFrame(all_bookings)
    
    # حساب المؤشرات المالية بشكل تلقائي وأمن
    total_paid = 0.0
    total_remaining = 0.0
    active_bookings_count = 0
    
    if not df_book.empty:
        if 'Paid' in df_book.columns:
            total_paid = pd.to_numeric(df_book['Paid'], errors='coerce').sum()
        if 'Remaining' in df_book.columns:
            total_remaining = pd.to_numeric(df_book['Remaining'], errors='coerce').sum()
        if 'Status' in df_book.columns:
            active_bookings_count = df_book[df_book['Status'].astype(str).str.contains("نشط|مستلم|ساري", na=False, case=False)].shape[0]
            
    # عرض الـ Metrics بشكل منظم في 3 مربعات بجانب بعض
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💰 إجمالي الإيرادات المحصلة جوه الخزنة", value=f"{total_paid:,.2f} ج.م")
    with col2:
        st.metric(label="🛑 إجمالي البواقي (الديون المتبقية برة)", value=f"{total_remaining:,.2f} ج.م")
    with col3:
        st.metric(label="👗 عدد الفساتين والحجوزات النشطة حالياً", value=active_bookings_count)
        
    st.write("---")
    st.subheader("📋 جدول أحدث العملاء المسجلين مؤخراً")
    if not df_cust.empty:
        st.dataframe(df_cust.tail(10), use_container_width=True)
    else:
        st.info("قاعدة البيانات فارغة، لم يتم تسجيل أي عملاء حتى الآن.")


# 5️⃣ الصفحة الثانية: تسجيل زبونة جديدة ومقاساتها
elif choice == "➕ تسجيل زبونة جديدة":
    st.title("➕ فتح ملف وتوثيق مقاسات زبونة جديدة")
    st.write("املأ الخانات التالية ليتم حفظها مباشرة في جدول الإكسيل أونلاين:")
    
    with st.form("customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("✍️ اسم الزبونة الثلاثي بالكامل *")
            phone = st.text_input("📱 رقم التليفون (واتساب أو إتصال) *")
            chest = st.text_input("📐 دورة الصدر (Chest)")
            waist = st.text_input("📐 دورة الوسط (Waist)")
        with col2:
            hips = st.text_input("📐 دورة الأرداف / الهنش (Hips)")
            shoulder = st.text_input("📐 عرض الكتف (Shoulder)")
            length = st.text_input("📐 الطول الكلي للفستان (Total Length)")
            sleeve = st.text_input("📐 طول الكم (Sleeve)")
            
        notes = st.text_area("📝 ملاحظات تفصيلية (نوع القماش، لون الفستان، تعديلات معينة)")
        
        submitted = st.form_submit_button("💾 حفظ السجل في قاعدة البيانات")
        
        if submitted:
            if not name or not phone:
                st.error("❌ خطأ: يجب كتابة اسم الزبونة ورقم التليفون على الأقل لحفظ الملف!")
            else:
                # حساب الرقم التعريفي للزبونة تلقائياً على حسب عدد السطور في الجدول
                total_rows = len(customers_sheet.get_all_values())
                customer_id = f"QS-{total_rows:03d}"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # ترتيب البيانات لحفظها في السطر
                row_data = [customer_id, name, phone, chest, waist, hips, shoulder, length, sleeve, notes, current_time]
                customers_sheet.append_row(row_data)
                
                st.success(f"🎉 عظيم جداً! تم حفظ ملف الزبونة ({name}) بنجاح، والآن البيانات مسجلة أونلاين.")


# 6️⃣ الصفحة الثالثة والأخيرة: البحث الاحترافي عن المقاسات (الميزة الجديدة)
elif choice == "🔍 البحث عن مقاسات زبونة":
    st.title("🔍 محرك البحث الذكي عن ملفات ومقاسات الزبائن")
    st.write("اكتب اسم العميل أو جزء منه، أو رقم التليفون، وهيطلعلك كارت المقاسات فوراً:")
    
    search_query = st.text_input("👉 ادخل اسم الزبونة أو رقم التليفون المُراد البحث عنه:")
    
    if search_query:
        all_customers = customers_sheet.get_all_records()
        
        if all_customers:
            df = pd.DataFrame(all_customers)
            
            # تحويل البيانات لنصوص لمنع أي أخطاء أثناء البحث والتصفية
            df['Name'] = df['Name'].astype(str)
            df['Phone'] = df['Phone'].astype(str)
            
            # البحث الجزئي الذكي (في خانة الاسم أو رقم الهاتف)
            result = df[df['Name'].str.contains(search_query, case=False, na=False) | 
                        df['Phone'].str.contains(search_query, na=False)]
            
            if not result.empty:
                st.success(f"🔍 تم العثور على ({len(result)}) زبونة تطابق بحثك:")
                
                for index, row in result.iterrows():
                    # إنشاء كارت منسدل شيك لكل عميل يظهر في نتائج البحث
                    with st.expander(f"👤 {row['Name']} —— 📱 {row['Phone']}"):
                        st.markdown("### 📐 المقاسات التفصيلية المسجلة:")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**الصدر:** {row.get('Chest', '—')}")
                            st.write(f"**الوسط:** {row.get('Waist', '—')}")
                            st.write(f"**الأرداف:** {row.get('Hips', '—')}")
                        with c2:
                            st.write(f"**الكتف:** {row.get('Shoulder', '—')}")
                            st.write(f"**الطول الكلي:** {row.get('Total_Length', '—')}")
                            st.write(f"**الكم:** {row.get('Sleeve', '—')}")
                        
                        st.write("---")
                        # عرض الملاحظات وتاريخ التسجيل بداخل الكارت
                        st.write(f"ℹ️ **ملاحظات العمل:** {row.get('Notes', 'لا يوجد ملاحظات مسجلة.')}")
                        st.caption(f"📅 تاريخ فتح الملف: {row.get('Date', 'غير محدد')}")
            else:
                st.error("❌ لم يتم العثور على أي زبونة مسجلة بهذا الاسم أو الرقم، تأكد من الحروف.")
        else:
            st.info("⚠️ جدول العملاء فارغ تماماً في شيت الإكسيل، قم بتسجيل عميل أولاً.")
