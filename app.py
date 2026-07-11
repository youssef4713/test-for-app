import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1️⃣ إعدادات واجهة الصفحة بالكامل لشكل احترافي باللغة العربية
st.set_page_config(
    page_title="lobna's System",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تعديل اتجاه الواجهة لتناسب اللغة العربية وتنسيق الأرقام
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
    
    # الأعمدة الكاملة للمقاسات بعد إضافة بنسة الصدر وعرض الكم
    cust_headers = [
        "Customer_ID", "Name", "Phone", "Chest", "Waist", "Hips", "Shoulder", 
        "Total_Length", "Sleeve", "Neck_to_Waist", "Waist_to_Bottom", "Crotch", 
        "Inseam", "Thigh_Length_Knee", "Thigh_Width", "Chest_Dart", "Sleeve_Width", "Notes", "Date"
    ]
    book_headers = ["Booking_ID", "Customer_Name", "Phone", "Dress_Code", "Total_Price", "Paid", "Remaining", "Status", "Date"]
    
    try:
        customers_sheet = sh.worksheet("customers")
    except gspread.exceptions.WorksheetNotFound:
        customers_sheet = sh.add_worksheet(title="customers", rows="1000", cols="25")
        customers_sheet.append_row(cust_headers)
        
    try:
        bookings_sheet = sh.worksheet("bookings")
    except gspread.exceptions.WorksheetNotFound:
        bookings_sheet = sh.add_worksheet(title="bookings", rows="1000", cols="15")
        bookings_sheet.append_row(book_headers)
        
except Exception as e:
    st.error(f"❌ هناك مشكلة في الاتصال بجوجل كلاود، تأكد من إعدادات الـ Secrets. الخطأ: {e}")
    st.stop()


# دالة جلب البيانات الآمنة وتحويلها لـ DataFrame
def get_dataframe_safely(sheet, default_columns):
    try:
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            df.columns = df.columns.str.strip()
            return df
        else:
            return pd.DataFrame(columns=default_columns)
    except Exception:
        return pd.DataFrame(columns=default_columns)


# جلب البيانات أوتوماتيكياً
df_cust = get_dataframe_safely(customers_sheet, cust_headers)
df_book = get_dataframe_safely(bookings_sheet, book_headers)


# 3️⃣ تصميم القائمة الجانبية للتنقل (Sidebar)
st.sidebar.title("👑 لوحة تفصيل الملكة")
st.sidebar.write("نظام إدارة وتفصيل الفساتين الذكي")
st.sidebar.write("---")

choice = st.sidebar.selectbox(
    "🧭 اختر الصفحة أو العملية:", 
    ["📊 لوحة التحكم الإحصائية", "➕ تسجيل زبونة ومقاسات جديدة", "👗 تسجيل طلب تفصيل جديد", "🔍 البحث عن مقاسات زبونة"]
)


# 4️⃣ الصفحة الأولى: لوحة التحكم الإحصائية (Dashboard)
if choice == "📊 لوحة التحكم الإحصائية":
    st.title("📊 الحسابات العامة وحالة طلبات التفصيل")
    st.write("ملخص مالي سريع لطلبات التفصيل الحالية في الأتيليه:")
    
    total_paid = 0.0
    total_remaining = 0.0
    active_orders_count = 0
    
    if not df_book.empty:
        if 'Total_Price' in df_book.columns:
            df_book['Total_Price'] = pd.to_numeric(df_book['Total_Price'], errors='coerce')
        if 'Paid' in df_book.columns:
            total_paid = pd.to_numeric(df_book['Paid'], errors='coerce').sum()
        if 'Remaining' in df_book.columns:
            total_remaining = pd.to_numeric(df_book['Remaining'], errors='coerce').sum()
        if 'Status' in df_book.columns:
            active_orders_count = df_book[df_book['Status'].astype(str).str.contains("تفصيل|تجهيز|بروفة|جاري", na=False, case=False)].shape[0]
            
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💰 إجمالي المبالغ المدفوعة (داخل الخزنة)", value=f"{total_paid:,.2f} ج.م")
    with col2:
        st.metric(label="🛑 إجمالي البواقي المستحقة (لينا برة)", value=f"{total_remaining:,.2f} ج.م")
    with col3:
        st.metric(label="👗 عدد طلبات التفصيل الجارية حالياً", value=active_orders_count)
        
    st.write("---")
    st.subheader("📋 أحدث الزبائن المسجلين في الأتيليه")
    if not df_cust.empty:
        st.dataframe(df_cust.tail(10), use_container_width=True)
    else:
        st.info("قاعدة البيانات فارغة، لم يتم تسجيل أي زبائن حتى الآن.")


# 5️⃣ الصفحة الثانية: تسجيل زبونة جديدة بالمقاسات الـ 14 الاحترافية
elif choice == "➕ تسجيل زبونة ومقاسات جديدة":
    st.title("➕ فتح ملف وتوثيق مقاسات تفصيل جديدة")
    st.write("املأ المقاسات المطلوبة بدقة ليتم حفظها أوتوماتيكياً:")
    
    with st.form("customer_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 👤 البيانات الأساسية")
            name = st.text_input("✍️ اسم الزبونة بالكامل *")
            phone = st.text_input("📱 رقم التليفون (واتساب) *")
            st.markdown("##### 📐 مقاسات وِجسد علوي")
            chest = st.text_input("دوران الصدر")
            waist = st.text_input("دوران الوسط")
            chest_dart = st.text_input("بنسة الصدر")
            
        with col2:
            st.markdown("##### 📐 مقاسات الأطوال والأكمام")
            shoulder = st.text_input("عرض الكتف")
            length = st.text_input("الطول الكلي للفستان")
            sleeve = st.text_input("طول الكم")
            sleeve_width = st.text_input("عرض الكم")
            neck_to_waist = st.text_input("طول من الرقبة للوسط")
            waist_to_bottom = st.text_input("طول من الوسط لأسفل")
            
        with col3:
            st.markdown("##### 📐 مقاسات الجزء السفلي والبنطلون")
            hips = st.text_input("دوران الأرداف/الهنش")
            crotch = st.text_input("الحجر")
            inseam = st.text_input("الحجر الداخلي")
            thigh_length_knee = st.text_input("طول الفخذ لحد الركبة")
            thigh_width = st.text_input("عرض الفخذ")
            
        st.write("---")
        notes = st.text_area("📝 ملاحظات إضافية (نوع القماش المطلوب، الموديل، تعديلات خاصة بالزبونة)")
        
        submitted = st.form_submit_button("💾 حفظ ملف الزبونة والمقاسات")
        
        if submitted:
            if not name or not phone:
                st.error("❌ خطأ: يجب كتابة الاسم ورقم التليفون لحفظ السجل!")
            else:
                total_rows = len(customers_sheet.get_all_values())
                customer_id = f"QS-{total_rows:03d}"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # ترتيب البيانات بدقة شديدة حسب مصفوفة الشيتس المعدلة
                row_data = [
                    customer_id, name, phone, chest, waist, hips, shoulder, length, sleeve,
                    neck_to_waist, waist_to_bottom, crotch, inseam, thigh_length_knee, thigh_width,
                    chest_dart, sleeve_width, notes, current_time
                ]
                customers_sheet.append_row(row_data)
                st.success(f"🎉 ممتاز! تم حفظ كارت مقاسات الزبونة ({name}) بنجاح في قاعدة البيانات.")


# 6️⃣ الصفحة الثالثة: تسجيل طلب تفصيل مالي جديد
elif choice == "👗 تسجيل طلب تفصيل جديد":
    st.title("👗 تسجيل طلب تفصيل مالي وفستان لزبونة مسجلة")
    st.write("اختر اسم الزبونة، واكتب موديل الفستان، وسيتم حساب المتبقي تلقائياً:")
    
    if not df_cust.empty and 'Name' in df_cust.columns:
        customer_list = df_cust['Name'].tolist()
        
        with st.form("booking_form", clear_on_submit=True):
            selected_customer = st.selectbox("👤 اختر اسم الزبونة المسجلة:", customer_list)
            dress_code = st.text_input("👗 نوع أو موديل الفستان المراد تفصيله *")
            
            col1, col2 = st.columns(2)
            with col1:
                total_price = st.number_input("💰 المبلغ الكلي المتفق عليه للتفصيل (ج.م)", min_value=0.0, step=50.0)
            with col2:
                paid = st.number_input("💵 المبلغ المدفوع حالياً (المقدم) (ج.م)", min_value=0.0, step=50.0)
                
            status = st.selectbox("📌 حالة طلب التفصيل الحالية:", ["قيد التفصيل والتجهيز", "تم التقفيل وفي انتظار البروفة", "تم التسليم النهائي للزبونة"])
            
            submit_booking = st.form_submit_button("💾 تسجيل الحجز المالي للطلب")
            
            if submit_booking:
                if not dress_code:
                    st.error("❌ خطأ: يجب كتابة نوع أو موديل الفستان لحفظ الطلب!")
                else:
                    cust_phone = df_cust[df_cust['Name'] == selected_customer]['Phone'].values[0]
                    remaining = total_price - paid
                    
                    total_b_rows = len(bookings_sheet.get_all_values())
                    booking_id = f"BK-{total_b_rows:03d}"
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    booking_data = [booking_id, selected_customer, str(cust_phone), dress_code, str(total_price), str(paid), str(remaining), status, current_time]
                    bookings_sheet.append_row(booking_data)
                    
                    st.success(f"🎉 تم تسجيل طلب التفصيل لـ ({selected_customer}) بنجاح! المبلغ الكلي: {total_price} ج.م | الباقي عليها: {remaining} ج.م")
    else:
        st.warning("⚠️ يجب تسجيل زبونة واحدة على الأقل في السيستم قبل القدرة على إنشاء طلب تفصيل مالي لها.")


# 7️⃣ الصفحة الرابعة: البحث الاحترافي الشامل وعرض الـ 14 مقاساً
elif choice == "🔍 البحث عن مقاسات زبونة":
    st.title("🔍 محرك البحث الذكي عن ملفات ومقاسات الزبائن")
    st.write("اكتب اسم الزبونة أو رقم تليفونها، وهيظهرلك كارت المقاسات التفصيلي فوراً:")
    
    search_query = st.text_input("👉 ادخل اسم الزبونة أو رقم التليفون:")
    
    if search_query:
        if not df_cust.empty:
            df_search = df_cust.copy()
            df_search['Name'] = df_search['Name'].astype(str)
            df_search['Phone'] = df_search['Phone'].astype(str)
            
            result = df_search[df_search['Name'].str.contains(search_query, case=False, na=False) | 
                               df_search['Phone'].str.contains(search_query, na=False)]
            
            if not result.empty:
                st.success(f"🔍 تم العثور على ({len(result)}) ملف يطابق بحثك:")
                
                for index, row in result.iterrows():
                    with st.expander(f"👤 {row['Name']} —— 📱 {row['Phone']}"):
                        st.markdown("### 📐 المقاسات الـ 14 بالتفصيل:")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"**الصدر:** {row.get('Chest', '—')}")
                            st.write(f"**الوسط:** {row.get('Waist', '—')}")
                            st.write(f"**بنسة الصدر:** {row.get('Chest_Dart', '—')}")
                            st.write(f"**الكتف:** {row.get('Shoulder', '—')}")
                        with c2:
                            st.write(f"**الطول الكلي:** {row.get('Total_Length', '—')}")
                            st.write(f"**الكم:** {row.get('Sleeve', '—')}")
                            st.write(f"**عرض الكم:** {row.get('Sleeve_Width', '—')}")
                            st.write(f"**طول من الرقبة للوسط:** {row.get('Neck_to_Waist', '—')}")
                            st.write(f"**طول من الوسط لأسفل:** {row.get('Waist_to_Bottom', '—')}")
                        with c3:
                            st.write(f"**الأرداف:** {row.get('Hips', '—')}")
                            st.write(f"**الحجر:** {row.get('Crotch', '—')}")
                            st.write(f"**الحجر الداخلي:** {row.get('Inseam', '—')}")
                            st.write(f"**طول الفخذ للركبة:** {row.get('Thigh_Length_Knee', '—')}")
                            st.write(f"**عرض الفخذ:** {row.get('Thigh_Width', '—')}")
                        
                        st.write("---")
                        st.write(f"ℹ️ **ملاحظات وتفاصيل الموديل:** {row.get('Notes', 'لا يوجد ملاحظات مسجلة.')}")
                        st.caption(f"📅 تاريخ فتح ملف المقاسات: {row.get('Date', 'غير محدد')}")
            else:
                st.error("❌ لم يتم العثور على أي زبونة مسجلة بهذا الاسم أو الرقم.")
        else:
            st.info("⚠️ جدول العملاء فارغ تماماً.")
