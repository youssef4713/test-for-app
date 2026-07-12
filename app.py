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
elif choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم - الأتيليه")
    
    # 1. جلب البيانات من الشيتين
    df_active = get_data(bookings_sheet)
    df_archive = get_data(completed_sheet)
    
    # تعريف الأعمدة عشان نضمن إن الكود يقرأ صح
    cols = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
    
    # التأكد إن الداتا مش فاضية وتجهيزها
    if not df_active.empty: 
        df_active.columns = cols
        df_active['Paid'] = pd.to_numeric(df_active['Paid'], errors='coerce').fillna(0)
    else:
        df_active = pd.DataFrame(columns=cols)
        df_active['Paid'] = 0
        
    if not df_archive.empty: 
        df_archive.columns = cols
        df_archive['Paid'] = pd.to_numeric(df_archive['Paid'], errors='coerce').fillna(0)
    else:
        df_archive = pd.DataFrame(columns=cols)
        df_archive['Paid'] = 0
    
    # 2. الحسابات
    # إجمالي الأرباح المحصلة = مجموع المدفوع من النشط + مجموع المدفوع من المكتمل
    total_revenue = df_active['Paid'].sum() + df_archive['Paid'].sum()
    
    # حساب الطلبات
    total_active_count = len(df_active)
    total_completed_count = len(df_archive)
    
    # 3. عرض البيانات
    col1, col2 = st.columns(2)
    with col1:
        st.metric("عدد الطلبات الحالية", total_active_count)
        st.metric("عدد الطلبات المكتملة", total_completed_count)
        
    with col2:
        st.metric("💰 إجمالي الأرباح المحصلة", f"{total_revenue:,.0f} ج.م")
        # ملاحظة: دي بتجمع الفلوس من الشيتين مع بعض
        st.info("هذا الرقم يمثل إجمالي المبالغ التي تم دفعها في الطلبات الحالية والقديمة.")

    # اختيار اختياري: عرض جدول بسيط للطلبات الحالية
    if not df_active.empty:
        st.write("---")
        st.subheader("نظرة سريعة على الطلبات الحالية:")
        st.dataframe(df_active[['Name', 'Status', 'Paid', 'Remaining']], use_container_width=True)
        
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
# --- 3. الحسابات والطلبات (مع ميزة تعديل الفلوس وأوتوماتيك التسليم) ---

elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")

    # 1. قسم إضافة طلب جديد (مخفي في Expander عشان مياخدش مساحة)
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("add_new_booking", clear_on_submit=True):
            df_cust = get_data(customers_sheet)
            cust_names = df_cust['Name'].tolist() if not df_cust.empty else []
            new_name = st.selectbox("اختر اسم العميل:", cust_names, index=None, placeholder="اختر العميل...")
            
            delivery_date = st.date_input("📅 تاريخ التسليم المتوقع:")
            details = st.text_area("تفاصيل الطلب:")
            total_price = st.number_input("السعر الكلي:", min_value=0)
            paid_amount = st.number_input("المبلغ المدفوع:", min_value=0)
            
            if st.form_submit_button("✅ حفظ الطلب"):
                if new_name is None:
                    st.error("⚠️ يرجى اختيار العميل!")
                else:
                    booking_id = int(datetime.now().timestamp())
                    remaining = total_price - paid_amount
                    bookings_sheet.append_row([str(booking_id), new_name, datetime.now().strftime("%Y-%m-%d"), 
                                               delivery_date.strftime("%Y-%m-%d"), "تحت التنفيذ", details, 
                                               float(total_price), float(paid_amount), float(remaining)])
                    st.success("تم إضافة الطلب!")
                    st.rerun()

    st.markdown("---")
    st.header("📋 قائمة الطلبات الحالية")

    # 2. عرض الطلبات (الجزء اللي كان مختفي)
    df_book = get_data(bookings_sheet)
    
    if df_book.empty:
        st.info("لا توجد طلبات جارية حالياً.")
    else:
        # ترتيب الأعمدة وتسميتها
        df_book.columns = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        
        # عرض جدول سريع للطلبات
        st.dataframe(df_book[['Name', 'Status', 'Total_Price', 'Paid', 'Remaining']], use_container_width=True)
        
        st.write("---")
        st.subheader("⚙️ تعديل ومعالجة الطلبات:")
        
        # 3. حلقة التعديل للطلبات
        for idx, row in df_book.iterrows():
            with st.expander(f"👗 {row['Name']} | الحالة: {row['Status']} | المتبقي: {row['Remaining']} ج.م"):
                with st.form(key=f"form_{row['Booking_ID']}"):
                    c1, c2 = st.columns(2)
                    new_status = c1.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"],
                                              index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(row['Status']) if row['Status'] in ["تحت التنفيذ", "جاهز", "تم التسليم"] else 0)
                    
                    new_total = c2.number_input("السعر الكلي:", value=float(row['Total_Price']))
                    new_paid = c1.number_input("المبلغ المدفوع:", value=float(row['Paid']))
                    
                    # الحساب الأوتوماتيك للمتبقي
                    new_remaining = new_total - new_paid
                    c2.info(f"المتبقي: {new_remaining} ج.م")

                    if st.form_submit_button("💾 تحديث الطلب"):
                        cell = bookings_sheet.find(str(row['Booking_ID']))
                        
                        # منطق التسليم
                        if new_status == "تم التسليم":
                            new_paid = new_total
                            new_remaining = 0
                            # النقل للأرشيف
                            completed_sheet.append_row([str(row['Booking_ID']), row['Name'], row['Registration_Date'], row['Delivery_Date'], "تم التسليم", row['Dress_Details'], new_total, new_total, 0])
                            bookings_sheet.delete_rows(cell.row)
                            st.success("تم التسليم والترحيل للأرشيف!")
                        else:
                            # تحديث عادي
                            bookings_sheet.update(f"E{cell.row}:I{cell.row}", [[new_status, row['Dress_Details'], new_total, new_paid, new_remaining]])
                            st.success("تم التحديث!")
                        st.rerun()
                        
# --- 4. الطلبات المكتملة ---
elif choice == "📦 الطلبات المكتملة":
    st.title("📦 أرشيف الطلبات المكتملة")
    df_comp = get_data(completed_sheet)
    st.dataframe(df_comp)

# --- 5. بحث ---
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
