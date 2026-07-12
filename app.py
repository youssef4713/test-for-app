import streamlit as st
import gspread
import time
import pandas as pd
import streamlit as st
from datetime import datetime
# ضيف ده بعد الـ import مباشرة
@st.cache_resource(hash_funcs={gspread.worksheet.Worksheet: lambda _: None})
def get_cached_sheet(sheet_name):
    # افترضنا إنك مسمي الـ client بتاعك 'client' في الكود، لو مسميه حاجة تانية غير الاسم هنا
    return client.open("اسم_ملف_جوجل_شيت_بتاعك").worksheet(sheet_name)


# إعدادات الواجهة
st.set_page_config(page_title="Lobna's System", page_icon="👗", layout="wide")

# الاتصال بجوجل شيتس
@st.cache_resource
def get_all_sheets():
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open("Atelier_Database")
        
        # بنرجعهم في قاموس عشان نستخدمهم بسهولة
        return {
            "customers": sh.worksheet("customers"),
            "bookings": sh.worksheet("bookings"),
            "completed": sh.worksheet("completed_bookings")
        }
    except Exception as e:
        st.error(f"خطأ في الاتصال بالسيرفر: {e}")
        return None

# 2. استدعاء الدالة عشان نجهز المتغيرات اللي الكود بيعتمد عليها
sheets = get_all_sheets()

if sheets:
    customers_sheet = sheets["customers"]
    bookings_sheet = sheets["bookings"]
    completed_sheet = sheets["completed"]
else:
    st.stop() # لو الاتصال فشل، البرنامج هيقف عشان ميكملش وهو معندوش بيانات
#-----------زرار التحديث----------------
with st.sidebar:
    st.write("---")
    
    # تحديد فترة الانتظار بالثواني (مثلاً 10 ثواني)
    COOLDOWN_SECONDS = 10 

    if st.button("🔄 تحديث البيانات"):
        # جيب الوقت الحالي
        current_time = time.time()
        # جيب آخر وقت تم فيه التحديث (لو مفيش يبقى 0)
        last_refresh = st.session_state.get("last_refresh", 0)

        # لو الفرق أكبر من 10 ثواني، كمل
        if current_time - last_refresh > COOLDOWN_SECONDS:
            st.cache_resource.clear()
            st.cache_data.clear()
            st.session_state["main_menu"] = "📊 لوحة التحكم"
            
            # سجل وقت التحديث الجديد
            st.session_state["last_refresh"] = current_time
            st.rerun()
        else:
            # لو أقل، طلع رسالة تحذير
            remaining = int(COOLDOWN_SECONDS - (current_time - last_refresh))
            st.warning(f"اهدى شوية! استنى {remaining} ثانية قبل التحديث تاني.")
        
def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=[c.strip() for c in raw_data[0]])
        return df
    return pd.DataFrame()

# القائمة الجانبية
choice = st.sidebar.radio(
    "🧭 القائمة الرئيسية:", 
    ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "💰 الحسابات والطلبات", "📦 الطلبات المكتملة", "🔍 بحث علي عميل و تعديل", "👤 حساب العميل"],
    key="main_menu"  # <--- ده اللي هيخلينا نتحكم في الاختيار
)
      
# --- 1. لوحة التحكم (KPIs) ---
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة التحكم - الأتيليه")
    
    # دالة لجلب وتنظيف البيانات الخاصة بلوحة التحكم فقط
    # تم التعديل هنا: استخدام sheet.title كـ hash key عشان الـ cache يفرق بين الشيتات
    @st.cache_data(hash_funcs={gspread.worksheet.Worksheet: lambda sheet: sheet.title})
    def get_clean_df(sheet):
        df = get_data(sheet)
        if df.empty:
            return pd.DataFrame(columns=['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining'])
        
        # التأكد من ترتيب الأعمدة
        cols = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        df.columns = cols
        
        # تحويل الأعمدة لأرقام لتجنب أي أخطاء حسابية
        df['Paid'] = pd.to_numeric(df['Paid'], errors='coerce').fillna(0)
        df['Remaining'] = pd.to_numeric(df['Remaining'], errors='coerce').fillna(0)
        return df

    # جلب البيانات من الشيتين
    df_active = get_clean_df(bookings_sheet)
    df_archive = get_clean_df(completed_sheet)
    
    # الحسابات
    # إجمالي المحصل = كل اللي اتدفع في الطلبات النشطة + كل اللي اتدفع في الأرشيف
    total_revenue = df_active['Paid'].sum() + df_archive['Paid'].sum()
    
    # المبالغ المنتظر تحصيلها = المتبقي في الطلبات النشطة فقط
    pending_money = df_active['Remaining'].sum()
    
    # العرض
    col1, col2 = st.columns(2)
    with col1:
        st.metric("عدد الطلبات الحالية", len(df_active))
        st.metric("عدد الطلبات المكتملة", len(df_archive))
    with col2:
        st.metric("💰 إجمالي الايرادات", f"{total_revenue:,.0f} ج.م")
        st.metric("⏳ مبالغ منتظر تحصيلها", f"{pending_money:,.0f} ج.م")
        
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
    
    # 2. تعديل ومعالجة الطلبات
    st.header("⚙️ تعديل ومعالجة الطلبات")
    df_book = get_data(bookings_sheet)
    
    if df_book.empty:
        st.info("لا توجد طلبات جارية حالياً.")
    else:
        df_book.columns = ['Booking_ID', 'Name', 'Registration_Date', 'Delivery_Date', 'Status', 'Dress_Details', 'Total_Price', 'Paid', 'Remaining']
        
        for idx, row in df_book.iterrows():
            with st.expander(f"👗 {row['Name']} | الحالة: {row['Status']} | المتبقي: {row['Remaining']} ج.م"):
                with st.form(key=f"form_{row['Booking_ID']}"):
                    c1, c2 = st.columns(2)
                    
                    status_options = ["تحت التنفيذ", "جاهز", "تم التسليم"]
                    current_status_idx = status_options.index(row['Status']) if row['Status'] in status_options else 0
                    
                    new_status = c1.selectbox("الحالة:", status_options, index=current_status_idx)
                    new_total = c2.number_input("السعر الكلي:", value=float(row['Total_Price']))
                    
                    # عرض المبلغ المدفوع الحالي (مقفول)
                    st.number_input("المبلغ المدفوع حالياً:", value=float(row['Paid']), disabled=True)
                    
                    # خانة إضافة مبلغ جديد
                    additional_payment = c1.number_input("إضافة مبلغ جديد:", min_value=0.0, value=0.0)
                    
                    # حساب المبلغ المدفوع الجديد والمتبقي
                    new_paid = float(row['Paid']) + additional_payment
                    new_remaining = new_total - new_paid
                    c2.info(f"المتبقي بعد الإضافة: {new_remaining} ج.م")

                    if st.form_submit_button("💾 تحديث الطلب"):
                        cell = bookings_sheet.find(str(row['Booking_ID']))
                        
                        if new_status == "تم التسليم":
                            # لو تم التسليم، نفترض إنه سدد الباقي
                            final_paid = new_total 
                            final_remaining = 0
                            completed_sheet.append_row([str(row['Booking_ID']), row['Name'], row['Registration_Date'], row['Delivery_Date'], "تم التسليم", row['Dress_Details'], new_total, final_paid, final_remaining])
                            bookings_sheet.delete_rows(cell.row)
                            st.success("تم التسليم والترحيل للأرشيف!")
                        else:
                            # تحديث بالقيم الجديدة المحسوبة
                            bookings_sheet.update(f"E{cell.row}:I{cell.row}", [[new_status, row['Dress_Details'], new_total, new_paid, new_remaining]])
                            st.success("تم التحديث بنجاح!")
                        st.rerun()

    # 3. قائمة الطلبات الحالية
    st.markdown("---")
    st.header("📋 قائمة الطلبات الحالية (نظرة سريعة)")
    if not df_book.empty:
        st.dataframe(df_book[['Name', 'Status', 'Total_Price', 'Paid', 'Remaining']], use_container_width=True)
        
# --- 4. الطلبات المكتملة ---
elif choice == "📦 الطلبات المكتملة":
    st.title("📦 أرشيف الطلبات المكتملة")
    df_comp = get_data(completed_sheet)
    st.dataframe(df_comp)

# --- 5. بحث ---
elif choice == "🔍 بحث علي عميل و تعديل":
    st.title("🔍 بحث علي عميل و تعديل")
    
    # جلب البيانات
    df_cust = get_data(customers_sheet)
    
    # مربع البحث
    search = st.text_input("🔎 ابحث باسم العميل:")
    
    if not df_cust.empty:
        if search:
            display_df = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        else:
            display_df = df_cust
            
        if not display_df.empty:
            for idx, row in display_df.iterrows():
                # استخدام الاسم لفتح العميل
                with st.expander(f"👤 {row['Name']}"):
                    # إضافة key فريد للفورم بناءً على الـ idx
                    with st.form(f"edit_meas_{idx}"):
                        c1, c2, c3 = st.columns(3)
                        
                        # إضافة key فريد لكل خانة عشان الداتا متلخبطش
                        new_chest = c1.text_input("دوران الصدر", value=str(row.get('Chest', '')), key=f"chest_{idx}")
                        new_waist = c1.text_input("دوران الوسط", value=str(row.get('Waist', '')), key=f"waist_{idx}")
                        new_dart = c1.text_input("بنسة الصدر", value=str(row.get('Chest_Dart', '')), key=f"dart_{idx}")
                        new_thigh = c1.text_input("عرض الفخذ", value=str(row.get('Thigh_Width', '')), key=f"thigh_{idx}")
                        
                        new_len = c2.text_input("الطول الكلي", value=str(row.get('Length', '')), key=f"len_{idx}")
                        new_sleeve = c2.text_input("عرض الكم", value=str(row.get('Sleeve_Width', '')), key=f"sleeve_{idx}")
                        new_neck = c2.text_input("طول الرقبة للوسط", value=str(row.get('Neck_to_Waist', '')), key=f"neck_{idx}")
                        new_inseam = c2.text_input("الحجر الداخلي", value=str(row.get('Inseam', '')), key=f"inseam_{idx}")
                        
                        new_waist_bot = c3.text_input("طول الوسط لأسفل", value=str(row.get('Waist_to_Bottom', '')), key=f"wbot_{idx}")
                        new_hips = c3.text_input("دوران الأرداف", value=str(row.get('Hips', '')), key=f"hips_{idx}")
                        new_crotch = c3.text_input("الحجر", value=str(row.get('Crotch', '')), key=f"crotch_{idx}")
                        new_thigh_knee = c3.text_input("طول الفخذ للركبة", value=str(row.get('thigh_length_k', '')), key=f"thk_{idx}")
                        
                        new_notes = st.text_area("ملاحظات", value=str(row.get('Notes', '')), key=f"notes_{idx}")
                        
                        if st.form_submit_button("💾 تحديث المقاسات"):
                            try:
                                # البحث عن رقم السطر الفعلي للعميل
                                cell = customers_sheet.find(row['Name'])
                                actual_row_idx = cell.row
                                
                                # ترتيب القيم بالظبط (لازم تطابق أعمدة الشيت من D لـ P)
                                updated_values = [
                                    new_chest, new_waist, new_dart, new_thigh, 
                                    new_len, new_sleeve, new_neck, new_inseam, 
                                    new_waist_bot, new_hips, new_crotch, new_thigh_knee, new_notes
                                ]
                                
                                # تحديث النطاق كامل
                                customers_sheet.update(f"D{actual_row_idx}:P{actual_row_idx}", [updated_values])
                                
                                st.success(f"تم تحديث بيانات {row['Name']} بنجاح!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"حدث خطأ: {e}")
        else:
            st.warning("لا يوجد عملاء بهذا الاسم.")
    else:
        st.info("لا توجد بيانات عملاء لعرضها.")
        
#------------حساب العميل----------------
elif choice == "👤 حساب العميل":
    st.title("👤 حساب العميل (سجل كامل)")
    
    # جلب الداتا
    df_cust = get_data(customers_sheet)
    df_book = get_data(bookings_sheet)
    df_comp = get_data(completed_sheet) 
    
    # دمج الطلبات (الجارية + المكتملة)
    # التأكد من وجود بيانات قبل الدمج لتجنب الأخطاء
    if not df_book.empty and not df_comp.empty:
        all_orders = pd.concat([df_book, df_comp], ignore_index=True)
    elif not df_book.empty:
        all_orders = df_book
    elif not df_comp.empty:
        all_orders = df_comp
    else:
        all_orders = pd.DataFrame()

    cust_names = df_cust['Name'].unique().tolist() if not df_cust.empty else []
    selected_name = st.selectbox("🔍 اختر العميل لعرض ملفه:", cust_names)
    
    if selected_name:
        # بيانات العميل
        cust_data = df_cust[df_cust['Name'] == selected_name].iloc[0]
        
        # طلبات العميل
        if not all_orders.empty:
            cust_history = all_orders[all_orders['Name'] == selected_name].copy()
        else:
            cust_history = pd.DataFrame()
        
        # --- الجزء الأول: الإحصائيات المالية ---
        st.subheader(f"📊 نظرة عامة: {selected_name}")
        
        if not cust_history.empty:
            # ** التعديل المهم هنا: تحويل الأعمدة لأرقام قبل الجمع **
            cust_history['Paid'] = pd.to_numeric(cust_history['Paid'], errors='coerce').fillna(0)
            cust_history['Remaining'] = pd.to_numeric(cust_history['Remaining'], errors='coerce').fillna(0)
            
            c1, c2, c3 = st.columns(3)
            
            total_spent = cust_history['Paid'].sum()
            total_orders = len(cust_history)
            remaining_balance = cust_history['Remaining'].sum()
            
            c1.metric("💰 إجمالي ما تم دفعه", f"{total_spent} ج.م")
            c2.metric("👗 عدد القطع (الطلبات)", total_orders)
            c3.metric("⏳ المتبقي عليه حالياً", f"{remaining_balance} ج.م")
        else:
            st.info("لا توجد طلبات مسجلة لهذا العميل.")
        
        # --- الجزء الثاني: المقاسات ---
        with st.expander("📏 مقاسات العميل الحالية"):
            col1, col2, col3 = st.columns(3)
            col1.write(f"**الصدر:** {cust_data.get('Chest', '---')}")
            col1.write(f"**الوسط:** {cust_data.get('Waist', '---')}")
            col1.write(f"**بنسة الصدر:** {cust_data.get('Chest_Dart', '---')}")
            col1.write(f"**عرض الفخذ:** {cust_data.get('Thigh_Width', '---')}")
            
            col2.write(f"**الطول الكلي:** {cust_data.get('Length', '---')}")
            col2.write(f"**عرض الكم:** {cust_data.get('Sleeve_Width', '---')}")
            col2.write(f"**طول الرقبة:** {cust_data.get('Neck_to_Waist', '---')}")
            col2.write(f"**الحجر الداخلي:** {cust_data.get('Inseam', '---')}")
            
            col3.write(f"**طول الوسط لأسفل:** {cust_data.get('Waist_to_Bottom', '---')}")
            col3.write(f"**دوران الأرداف:** {cust_data.get('Hips', '---')}")
            col3.write(f"**الحجر:** {cust_data.get('Crotch', '---')}")
            col3.write(f"**طول الفخذ للركبة:** {cust_data.get('thigh_length_k', '---')}")
            
            st.write(f"**ملاحظات:** {cust_data.get('Notes', '---')}")
            
        # --- الجزء الثالث: تاريخ التعاملات ---
        st.subheader("📜 تاريخ الطلبات")
        if not cust_history.empty:
            # ترتيب الجدول بالأحدث (بافتراض إن عمود Registration_Date موجود)
            st.dataframe(cust_history[['Registration_Date', 'Status', 'Total_Price', 'Paid', 'Remaining', 'Dress_Details']], use_container_width=True)
        else:
            st.warning("لا يوجد تاريخ طلبات لهذا العميل.")
