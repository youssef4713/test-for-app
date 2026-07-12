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

# --- 1. لوحة التحكم ---
elif choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم - الأتيليه")
    
    # 1. جلب وتجهيز البيانات
    df_active = get_data(bookings_sheet)
    df_archive = get_data(completed_sheet)
    
    cols = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
    
    if not df_active.empty: df_active.columns = cols
    if not df_archive.empty: df_archive.columns = cols
    
    df_all = pd.concat([df_active, df_archive], ignore_index=True)
    
    # --- التعديل هنا: تحويل البيانات لأرقام عشان الجمع يطلع صح ---
    df_all['Paid'] = pd.to_numeric(df_all['Paid'], errors='coerce').fillna(0)
    df_all['Remaining'] = pd.to_numeric(df_all['Remaining'], errors='coerce').fillna(0)
    # --------------------------------------------------------
    
    # 2. حسابات الشهر الحالي
    df_all['Registration_Date'] = pd.to_datetime(df_all['Registration_Date'], errors='coerce')
    df_month = df_all[(df_all['Registration_Date'].dt.month == 7) & (df_all['Registration_Date'].dt.year == 2026)]
    
    # 3. استخراج الأرقام
    total_orders = len(df_month)
    delivered_orders = df_month[df_month['Status'] == 'تم التسليم']
    active_orders = df_month[df_month['Status'] != 'تم التسليم']
    
    revenue = delivered_orders['Paid'].sum()
    pending_money = active_orders['Remaining'].sum()
    
    # 4. العرض
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="إجمالي الطلبات هذا الشهر", value=f"{total_orders} طلب")
        st.metric(label="فستان تم تسليمه", value=f"{len(delivered_orders)}")
    with col2:
        st.metric(label="الأرباح المحصلة", value=f"{revenue} ج.م")
        st.metric(label="مبالغ منتظر تحصيلها", value=f"{pending_money} ج.م")
    
    st.write("---")
    st.info("💡 تم حساب البيانات بناءً على طلبات شهر يوليو 2026")

# --- 2. تسجيل عميلة جديدة ---
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

elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")
    
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("add_new_booking"):
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
                    st.success("تم إضافة الطلب!")
                    st.rerun()

    st.write("---")
    
    df_book = get_data(bookings_sheet)
    
    # ضمان ثبات أسماء الأعمدة لتجنب الـ KeyError
    if not df_book.empty:
        df_book.columns = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        
        # ترتيب حسب أقرب ميعاد تسليم
        df_book['Delivery_Date'] = pd.to_datetime(df_book['Delivery_Date'], errors='coerce')
        df_book = df_book.sort_values(by='Delivery_Date', ascending=True)
        
        for idx, row in df_book.iterrows():
            b_id = str(row.get('Booking_ID', ''))
            name_val = row.get('Name', 'بدون اسم')
            deliv_date = row.get('Delivery_Date').strftime('%Y-%m-%d') if pd.notnull(row.get('Delivery_Date')) else '-'
            status_val = row.get('Status', 'تحت التنفيذ')
            
            with st.expander(f"👗 {name_val} | ⏳ تسليم: {deliv_date} | الحالة: {status_val}"):
                # استخدام key فريد (ID + رقم الصف) لمنع الإيرور
                with st.form(key=f"edit_{b_id}_{idx}"):
                    new_details = st.text_area("تفاصيل الطلب:", value=row.get('Dress_Details', ''))
                    new_deliv_date = st.date_input("تعديل التاريخ:", value=pd.to_datetime(deliv_date))
                    new_status = st.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"], 
                                             index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(status_val) if status_val in ["تحت التنفيذ", "جاهز", "تم التسليم"] else 0)
                    
                    if st.form_submit_button("💾 تحديث"):
                        cell = bookings_sheet.find(b_id)
                        row_idx = cell.row
                        
                        if new_status == "تم التسليم":
                            # تجهيز البيانات كقيم نصية/رقمية بسيطة لتجنب إيرور الـ JSON
                            archive_row = [
                                str(row['Booking_ID']), str(row['Name']), str(row['Registration_Date']),
                                new_deliv_date.strftime("%Y-%m-%d"), "تم التسليم", str(new_details),
                                float(row['Total_Price']), float(row['Paid']), float(row['Remaining'])
                            ]
                            completed_sheet.append_row(archive_row)
                            bookings_sheet.delete_rows(row_idx)
                            st.success("تم التسليم والترحيل للأرشيف!")
                        else:
                            # تحديث الخلايا العادية
                            bookings_sheet.update_cell(row_idx, 4, new_deliv_date.strftime("%Y-%m-%d"))
                            bookings_sheet.update_cell(row_idx, 5, new_status)
                            bookings_sheet.update_cell(row_idx, 6, new_details)
                            st.success("تم التحديث!")
                        st.rerun()
                        
# --- 4. الطلبات المكتملة ---
elif choice == "📦 الطلبات المكتملة":
    st.title("📦 أرشيف الطلبات المكتملة")
    df_comp = get_data(completed_sheet)
    if not df_comp.empty:
        st.dataframe(df_comp)
    else:
        st.info("لا توجد طلبات مكتملة مؤرشفة حالياً.")

# --- 5. بحث علي عميل و تعديل ---
elif choice == "🔍 بحث علي عميل و تعديل":
    st.title("🔍 بحث علي عميل و تعديل")
    
    df_cust = get_data(customers_sheet)
    search = st.text_input("🔎 ابحث باسم العميل أو اختر من القائمة أدناه:")
    
    if not df_cust.empty:
        if search:
            display_df = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        else:
            display_df = df_cust
            
        if not display_df.empty:
            for idx, row in display_df.iterrows():
                row_idx = idx + 2 
                
                with st.expander(f"👤 {row['Name']} - {row.get('Phone', '')}"):
                    with st.form(f"edit_meas_{row_idx}"):
                        c1, c2, c3 = st.columns(3)
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
                            customers_sheet.update_cell(row_idx, 4, new_chest)
                            customers_sheet.update_cell(row_idx, 5, new_waist)
                            customers_sheet.update_cell(row_idx, 6, new_hips)
                            customers_sheet.update_cell(row_idx, 7, new_len)
                            st.success(f"تم تحديث بيانات {row['Name']}!")
        else:
            st.warning("لا يوجد عملاء بهذا الاسم.")
    else:
        st.info("لا توجد بيانات عملاء لعرضها.")
