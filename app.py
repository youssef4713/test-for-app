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
    
    df_book = get_data(bookings_sheet)
    if not df_book.empty:
        df_book.columns = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        
        for idx, row in df_book.iterrows():
            with st.expander(f"👗 {row['Name']} | الحالة: {row['Status']} | متبقي: {row['Remaining']} ج.م"):
                with st.form(f"form_{row['Booking_ID']}"):
                    col1, col2 = st.columns(2)
                    new_status = col1.selectbox("الحالة", ["تحت التنفيذ", "تم التسليم"], index=["تحت التنفيذ", "تم التسليم"].index(row['Status']) if row['Status'] in ["تحت التنفيذ", "تم التسليم"] else 0)
                    new_paid = col2.number_input("المبلغ المدفوع", value=float(row['Paid']))
                    
                    if st.form_submit_button("💾 تحديث وتعديل الحسابات"):
                        # الحساب الأوتوماتيك
                        total = float(row['Total_Price'])
                        if new_status == "تم التسليم":
                            new_paid = total  # لو تم التسليم يبقى دفع كل الفلوس
                            new_remaining = 0
                        else:
                            new_remaining = total - new_paid
                            
                        # تحديث الشيت
                        cell = bookings_sheet.find(str(row['Booking_ID']))
                        bookings_sheet.update(f"E{cell.row}:I{cell.row}", [[new_status, row['Dress_Details'], total, new_paid, new_remaining]])
                        
                        if new_status == "تم التسليم":
                            completed_sheet.append_row([str(row['Booking_ID']), row['Name'], row['Registration_Date'], row['Delivery_Date'], "تم التسليم", row['Dress_Details'], total, total, 0])
                            bookings_sheet.delete_rows(cell.row)
                            
                        st.success("تم التحديث وحساب المتبقي أوتوماتيك!")
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
