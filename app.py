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
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة تحكم الأتيليه")
    df_book = get_data(bookings_sheet)
    
    if not df_book.empty and 'Date' in df_book.columns:
        df_book['Date'] = pd.to_datetime(df_book['Date'], errors='coerce')
        df_book['Paid'] = pd.to_numeric(df_book['Paid'], errors='coerce').fillna(0)
        df_book['Remaining'] = pd.to_numeric(df_book['Remaining'], errors='coerce').fillna(0)
        
        total_paid = df_book['Paid'].sum()
        total_remaining = df_book['Remaining'].sum()
        total_count = len(df_book)
        
        thirty_days_ago = datetime.now() - pd.Timedelta(days=30)
        df_filtered = df_book[df_book['Date'] >= thirty_days_ago]
        
        recent_paid = df_filtered['Paid'].sum()
        recent_count = len(df_filtered)
        
        st.subheader("📈 الإجمالي الكلي (منذ البداية)")
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي التحصيل الكلي", f"{total_paid:,.0f} ج.م")
        c2.metric("إجمالي المتبقي الكلي", f"{total_remaining:,.0f} ج.م")
        c3.metric("عدد الطلبات الكلي", total_count)
        
        st.write("---")
        st.subheader("🗓️ أداء آخر 30 يوم")
        c4, c5 = st.columns(2)
        c4.metric("تحصيل آخر 30 يوم", f"{recent_paid:,.0f} ج.م")
        c5.metric("عدد الطلبات في 30 يوم", recent_count)
        
        if not df_filtered.empty:
            st.write("📋 الطلبات الأخيرة:")
            st.dataframe(df_filtered[['Name', 'Status', 'Paid', 'Date']])
        else:
            st.info("لا توجد طلبات جديدة في آخر 30 يوم.")
    else:
        st.warning("تأكد من وجود البيانات في الشيت وتسمية عمود التاريخ بـ 'Date'.")

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

# --- 3. الحسابات والطلبات ---
st.write("---")
    df_book =get_data(bookings_sheet)
    if not df_book.empty:
        # ترتيب الطلبات من الأحدث للأقدم
        df_book = df_book.sort_index(ascending=False)
        
        for idx, row in df_book.iterrows():
            row_idx = idx + 2  # لأن الـ index بيبدأ من 0 والشيت بيبدأ من صف 2
            
            # جلب البيانات الحالية من الصف
            name_val = row.get('Name', 'بدون اسم')
            reg_date = row.get('Registration_Date', '-')
            deliv_date = row.get('Delivery_Date', '-')
            status_val = row.get('Status', 'تحت التنفيذ')
            details_val = row.get('Dress_Details', '')
            total_val = pd.to_numeric(row.get('Total_Price', 0), errors='coerce') or 0
            paid_val = pd.to_numeric(row.get('Paid', 0), errors='coerce') or 0
            
            # عرض التاريخ والحالة في عنوان الـ Expander للتابلت
            with st.expander(f"👗 {name_val} | ⏳ التسليم: {deliv_date} | الحالة: {status_val}"):
                st.markdown(f"📅 **تاريخ الحجز:** {reg_date}  |  🚀 **تاريخ التسليم المتوقع:** `{deliv_date}`")
                
                with st.form(f"edit_{row_idx}"):
                    new_details = st.text_area("تفاصيل الطلب:", value=details_val)
                    
                    # معالجة التاريخ القديم بأمان عشان الفايرفوكس أو المتصفح ميعملش إيرور
                    try:
                        default_date = pd.to_datetime(deliv_date).date()
                    except:
                        default_date = datetime.now().date()
                        
                    new_deliv_date = st.date_input("تعديل تاريخ التسليم:", value=default_date)
                    
                    # اختيار الحالة الجديدة
                    new_status = st.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"], 
                                             index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(status_val) if status_val in ["تحت التنفيذ", "جاهز", "تم التسليم"] else 0)
                    
                    new_total = st.number_input("المبلغ الكلي:", value=float(total_val), min_value=0.0)
                    new_paid = st.number_input("المدفوع حالياً:", value=float(paid_val), min_value=0.0)
                    
                    if st.form_submit_button("💾 تحديث الطلب"):
                        remaining = new_total - new_paid
                        
                        # --- سيناريو 1: إذا اختار "تم التسليم" -> يتم النقل للأرشيف فوراً وحذفه ---
                        if new_status == "تم التسليم":
                            # تجهيز البيانات المرتبة لنقلها لشيت completed_bookings
                            row_to_archive = [
                                name_val,
                                reg_date,
                                new_deliv_date.strftime("%Y-%m-%d"),
                                "تم التسليم",
                                new_details,
                                new_total,
                                new_paid,
                                remaining
                            ]
                            
                            # إضافة الصف لشيت الأرشيف completed_bookings
                            completed_sheet.append_row(row_to_archive)
                            
                            # مسح الصف من شيت الـ bookings الأساسي
                            bookings_sheet.delete_rows(row_idx)
                            
                            st.success(f"🎉 مبروك! تم تسليم طلب العميل {name_val} بنجاح ونقله إلى شيت الطلبات المكتملة.")
                            st.rerun()
                        
                        # --- سيناريو 2: تحديث البيانات العادية لو الحالة لسه مخلصتش ---
                        else:
                            # تحديث الخلايا بناءً على ترتيبها الصحيح في الشيت
                            bookings_sheet.update_cell(row_idx, 3, new_deliv_date.strftime("%Y-%m-%d")) # Delivery_Date
                            bookings_sheet.update_cell(row_idx, 4, new_status)                         # Status
                            bookings_sheet.update_cell(row_idx, 5, new_details)                        # Dress_Details
                            bookings_sheet.update_cell(row_idx, 6, new_total)                          # Total_Price
                            bookings_sheet.update_cell(row_idx, 7, new_paid)                           # Paid
                            bookings_sheet.update_cell(row_idx, 8, remaining)                          # Remaining
                            
                            st.success("تم تحديث بيانات الطلب بنجاح!")
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
