import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="Lobna's System", page_icon="👗", layout="wide")

# الاتصال بجوجل شيتس
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings")
    completed_sheet = sh.worksheet("completed_bookings") 
except Exception as e:
    st.error(f"خطأ في الاتصال بالسيرفر: {e}")
    st.stop()

def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=[c.strip() for c in raw_data[0]])
        return df
    return pd.DataFrame()

# القائمة الجانبية
choice = st.sidebar.selectbox("🧭 القائمة الرئيسية:", 
                              ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "💰 الحسابات والطلبات", "📦 الطلبات المكتملة", "🔍 بحث علي عميل و تعديل"])

# --- 1. لوحة التحكم (KPIs) ---
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم - الأتيليه")
    
    df_active = get_data(bookings_sheet)
    df_archive = get_data(completed_sheet)
    cols = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
    
    if not df_active.empty: df_active.columns = cols
    if not df_archive.empty: df_archive.columns = cols
    
    df_all = pd.concat([df_active, df_archive], ignore_index=True)
    df_all['Paid'] = pd.to_numeric(df_all['Paid'], errors='coerce').fillna(0)
    df_all['Remaining'] = pd.to_numeric(df_all['Remaining'], errors='coerce').fillna(0)
    
    df_all['Registration_Date'] = pd.to_datetime(df_all['Registration_Date'], errors='coerce')
    df_month = df_all[(df_all['Registration_Date'].dt.month == 7) & (df_all['Registration_Date'].dt.year == 2026)]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي الطلبات هذا الشهر", f"{len(df_month)} طلب")
        st.metric("فستان تم تسليمه", f"{len(df_month[df_month['Status'] == 'تم التسليم'])}")
    with col2:
        st.metric("الأرباح المحصلة", f"{df_month[df_month['Status'] == 'تم التسليم']['Paid'].sum()} ج.م")
        st.metric("مبالغ منتظر تحصيلها", f"{df_month[df_month['Status'] != 'تم التسليم']['Remaining'].sum()} ج.م")

# --- 2. تسجيل عميلة جديدة ---
elif choice == "➕ تسجيل عميلة جديدة":
    st.title("➕ تسجيل عميلة جديدة")
    with st.form("new_customer", clear_on_submit=True):
        name = st.text_input("اسم الزبونة")
        phone = st.text_input("التليفون")
        if st.form_submit_button("💾 حفظ بيانات العميل"):
            customers_sheet.append_row(["QS-NEW", name, phone, "", "", "", "", "", "", "", "", "", "", "", "", "", datetime.now().strftime("%Y-%m-%d")])
            st.success(f"تم حفظ بيانات {name} بنجاح!")

# --- 3. الحسابات والطلبات (مع ميزة تعديل الفلوس وأوتوماتيك التسليم) ---

elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")

    # 1. قسم إضافة طلب جديد
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("add_new_booking", clear_on_submit=True):
            df_cust = get_data(customers_sheet)
            cust_names = df_cust['Name'].tolist() if not df_cust.empty else []
            new_name = st.selectbox("اختر اسم العميل:", cust_names, index=None, placeholder="اختر العميل...")

            delivery_date = st.date_input("📅 تاريخ التسليم المتوقع:")
            details = st.text_area("تفاصيل الطلب:")
            total_price = st.number_input("السعر الكلي:", min_value=0)
            paid_amount = st.number_input("المبلغ المدفوع:", min_value=0)

            if st.form_submit_button("✅ إضافة الطلب"):
                if new_name is None:
                    st.error("⚠️ من فضلك اختر اسم العميل أولاً!")
                else:
                    booking_id = int(datetime.now().timestamp())
                    remaining = total_price - paid_amount
                    # إضافة الصف في جوجل شيتس (الترتيب ضروري)
                    bookings_sheet.append_row([
                        str(booking_id), new_name, datetime.now().strftime("%Y-%m-%d"),
                        delivery_date.strftime("%Y-%m-%d"), "تحت التنفيذ", details,
                        float(total_price), float(paid_amount), float(remaining)
                    ])
                    st.success("تم إضافة الطلب بنجاح!")
                    st.rerun()

    st.write("---")

    # 2. قسم عرض وتعديل الطلبات
elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")

    # 1. قسم إضافة طلب جديد
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("add_new_booking", clear_on_submit=True):
            df_cust = get_data(customers_sheet)
            cust_names = df_cust['Name'].tolist() if not df_cust.empty else []
            new_name = st.selectbox("اختر اسم العميل:", cust_names, index=None, placeholder="اختر العميل...")

            delivery_date = st.date_input("📅 تاريخ التسليم المتوقع:")
            details = st.text_area("تفاصيل الطلب:")
            total_price = st.number_input("السعر الكلي:", min_value=0)
            paid_amount = st.number_input("المبلغ المدفوع:", min_value=0)

            if st.form_submit_button("✅ إضافة الطلب"):
                if new_name is None:
                    st.error("⚠️ من فضلك اختر اسم العميل أولاً!")
                else:
                    booking_id = int(datetime.now().timestamp())
                    remaining = total_price - paid_amount
                    bookings_sheet.append_row([
                        str(booking_id), new_name, datetime.now().strftime("%Y-%m-%d"),
                        delivery_date.strftime("%Y-%m-%d"), "تحت التنفيذ", details,
                        float(total_price), float(paid_amount), float(remaining)
                    ])
                    st.success("تم إضافة الطلب بنجاح!")
                    st.rerun()

    st.write("---")

    # 2. قسم عرض وتعديل الطلبات
    df_book = get_data(bookings_sheet)

    if df_book.empty:
        st.info("لا توجد طلبات حالياً.")
    else:
        df_book.columns = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        
        for idx, row in df_book.iterrows():
            with st.expander(f"👗 {row['Name']} | 💰 متبقي: {row['Remaining']} ج.م"):
                with st.form(key=f"form_{row['Booking_ID']}"):
                    c1, c2 = st.columns(2)
                    new_status = c1.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"],
                                              index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(row['Status']) if row['Status'] in ["تحت التنفيذ", "جاهز", "تم التسليم"] else 0)
                    
                    new_total = c2.number_input("السعر الكلي:", value=float(row['Total_Price']))
                    new_paid = c1.number_input("المبلغ المدفوع:", value=float(row['Paid']))
                    
                    # حساب المتبقي أوتوماتيكياً
                    new_remaining = new_total - new_paid
                    c2.write(f"### المتبقي: {new_remaining} ج.م")

                    if st.form_submit_button("💾 تحديث الطلب"):
                        cell = bookings_sheet.find(str(row['Booking_ID']))
                        
                        # لو تم التسليم، نعتبر الحساب اتصفى
                        if new_status == "تم التسليم":
                            new_paid = new_total
                            new_remaining = 0
                            
                        # تحديث القيم في الشيت
                        bookings_sheet.update(f"E{cell.row}:I{cell.row}", [[new_status, row['Dress_Details'], new_total, new_paid, new_remaining]])

                        if new_status == "تم التسليم":
                            completed_sheet.append_row([
                                str(row['Booking_ID']), row['Name'], row['Registration_Date'],
                                row['Delivery_Date'], "تم التسليم", row['Dress_Details'],
                                new_total, new_total, 0
                            ])
                            bookings_sheet.delete_rows(cell.row)
                            st.success("تم التسليم والترحيل للأرشيف!")
                        else:
                            st.success("تم تحديث البيانات!")
                        st.rerun()

# --- 4. الطلبات المكتملة ---
elif choice == "📦 الطلبات المكتملة":
    st.title("📦 أرشيف الطلبات المكتملة")
    df_comp = get_data(completed_sheet)
    st.dataframe(df_comp)

# --- 5. بحث ---
elif choice == "🔍 بحث علي عميل و تعديل":
    st.title("🔍 بحث")
    # (كود البحث كما هو)
