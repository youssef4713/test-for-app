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
elif choice == "💰 الحسابات والطلبات":
    st.title("💰 الحسابات والطلبات")
    
    # إضافة طلب جديد
    with st.expander("➕ إضافة طلب جديد"):
        with st.form("add_new_booking"):
            df_cust = get_data(customers_sheet)
            cust_names = df_cust['Name'].tolist() if not df_cust.empty else []
            new_name = st.selectbox("اختر اسم العميل:", cust_names)
            total_price = st.number_input("السعر الكلي:", min_value=0)
            paid_amount = st.number_input("المبلغ المدفوع:", min_value=0)
            
            if st.form_submit_button("✅ إضافة الطلب"):
                remaining = total_price - paid_amount
                # الترتيب حسب الأعمدة (الاسم، التاريخ، الحالة، ...، السعر، المدفوع، المتبقي)
                bookings_sheet.append_row([new_name, datetime.now().strftime("%Y-%m-%d"), "تحت التنفيذ", "", total_price, paid_amount, remaining, "تحت التنفيذ"])
                st.success("تم إضافة الطلب بنجاح!")
                st.rerun()

    st.write("---")
    # عرض وتعديل الطلبات
    df_book = get_data(bookings_sheet)
    if not df_book.empty:
        for idx, row in df_book.iterrows():
            row_idx = idx + 2
            paid_val = pd.to_numeric(row.get('Paid', 0), errors='coerce') or 0
            total_val = pd.to_numeric(row.get('Total_Price', 0), errors='coerce') or 0
            name_val = row.get('Name', 'بدون اسم')
            status_val = row.get('Status', 'تحت التنفيذ')
            
            with st.expander(f"👗 طلب: {name_val} | الحالة: {status_val}"):
                with st.form(f"edit_{row_idx}"):
                    new_status = st.selectbox("الحالة:", ["تحت التنفيذ", "جاهز", "تم التسليم"], 
                                             index=["تحت التنفيذ", "جاهز", "تم التسليم"].index(status_val) if status_val in ["تحت التنفيذ", "جاهز", "تم التسليم"] else 0)
                    new_paid = st.number_input("المدفوع حالياً:", value=float(paid_val))
                    new_total = st.number_input("المبلغ الكلي:", value=float(total_val))
                    
                    if st.form_submit_button("💾 تحديث الطلب"):
                        remaining = new_total - new_paid
                        if new_status == "تم التسليم":
                            row_values = row.tolist()
                            row_values[5] = new_paid 
                            row_values[4] = new_total
                            row_values[7] = new_status
                            completed_sheet.append_row(row_values)
                            bookings_sheet.delete_rows(row_idx)
                            st.success("تم نقل الطلب للأرشيف!")
                            st.rerun()
                        else:
                            bookings_sheet.update_cell(row_idx, 5, new_total)
                            bookings_sheet.update_cell(row_idx, 6, new_paid)
                            bookings_sheet.update_cell(row_idx, 7, remaining)
                            bookings_sheet.update_cell(row_idx, 8, new_status)
                            st.success("تم التحديث!")
                            st.rerun()
    else:
        st.info("لا توجد طلبات لعرضها.")

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
