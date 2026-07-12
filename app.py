import streamlit as st
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

#----------السايد بار---------
    choice = st.sidebar.radio(
        "🧭 القائمة الرئيسية:", 
        ["📊 لوحة التحكم", "➕ تسجيل عميلة جديدة", "💰 الحسابات والطلبات", "📦 الطلبات المكتملة", "🔍 بحث علي عميل و تعديل", "👤 حساب العميل", "💰 مديونيات العملاء", "📅 التسليمات"],
        key="main_menu" 
    )

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
    
# --- 1. لوحة التحكم (KPIs) ---
elif choice == "📊 لوحة التحكم":
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
        st.metric("⏳ مبالغ تحت التحصيل", f"{pending_money:,.0f} ج.م")
        
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
        chest = c1.number_input("دوران الصدر", min_value=0.0, step=0.5, format="%f")
        waist = c1.number_input("دوران الوسط", min_value=0.0, step=0.5, format="%f")
        chest_dart = c1.number_input("بنسة الصدر", min_value=0.0, step=0.5, format="%f")
        length = c2.number_input("الطول الكلي", min_value=0.0, step=0.5, format="%f")
        sleeve_width = c2.number_input("عرض الكم", min_value=0.0, step=0.5, format="%f")
        neck_to_waist = c2.number_input("طول الرقبة للوسط", min_value=0.0, step=0.5, format="%f")
        waist_to_bottom = c3.number_input("طول الوسط لأسفل", min_value=0.0, step=0.5, format="%f")
        hips = c3.number_input("دوران الأرداف", min_value=0.0, step=0.5, format="%f")
        crotch = c3.number_input("الحجر", min_value=0.0, step=0.5, format="%f")
        inseam = c3.number_input("الحجر الداخلي", min_value=0.0, step=0.5, format="%f")
        thigh_width = c3.number_input("عرض الفخذ", min_value=0.0, step=0.5, format="%f")
        thigh_length_k = c3.number_input("طول الفخذ للركبة", min_value=0.0, step=0.5, format="%f")
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
            Paid = st.number_input("المبلغ المدفوع:", min_value=0)
            
            if st.form_submit_button("✅ حفظ الطلب"):
                if new_name is None:
                    st.error("⚠️ يرجى اختيار العميل!")
                else:
                    booking_id = int(datetime.now().timestamp())
                    remaining = total_price - Paid
                    bookings_sheet.append_row([str(booking_id), new_name, datetime.now().strftime("%Y-%m-%d"), 
                                             delivery_date.strftime("%Y-%m-%d"), "تحت التنفيذ", details, 
                                             float(total_price), float(Paid), float(remaining)])
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
            # تظبيط العنوان
            short_details = str(row['Dress_Details'])
            if len(short_details) > 20:
                short_details = short_details[:20] + "..."
            
            expander_title = f"🆔 {row['Booking_ID']} | {row['Name']} | {short_details} | المتبقي: {row['Remaining']} ج.م"
            
            with st.expander(expander_title):
                with st.form(key=f"form_{row['Booking_ID']}"):
                    c1, c2 = st.columns(2)
                    
                    status_options = ["تحت التنفيذ", "جاهز", "تم التسليم"]
                    current_status_idx = status_options.index(row['Status']) if row['Status'] in status_options else 0
                    
                    new_status = c1.selectbox("الحالة:", status_options, index=current_status_idx)
                    new_total = c2.number_input("السعر الكلي:", value=float(row['Total_Price']), disabled=True)
                    
                    # --- الجزء الجديد: عرض وتعديل تفاصيل الطلب ---
                    new_details = st.text_area("تفاصيل الطلب:", value=row['Dress_Details'])
                    
                    # عرض المبلغ المدفوع الحالي
                    st.number_input("المبلغ المدفوع حالياً:", value=float(row['Paid']), disabled=True)
                    
                    additional_payment = c1.number_input("إضافة دفعة :", min_value=0.0, value=0.0)
                    
                    new_paid = float(row['Paid']) + additional_payment
                    new_remaining = new_total - new_paid
                    c2.info(f"المتبقي بعد الإضافة: {new_remaining} ج.م")

                    if st.form_submit_button("💾 تحديث الطلب"):
                        cell = bookings_sheet.find(str(row['Booking_ID']))
                        
                        if new_status == "تم التسليم":
                            final_paid = new_total 
                            final_remaining = 0
                            completed_sheet.append_row([str(row['Booking_ID']), row['Name'], row['Registration_Date'], row['Delivery_Date'], "تم التسليم", new_details, new_total, final_paid, final_remaining])
                            bookings_sheet.delete_rows(cell.row)
                            st.success("تم التسليم والترحيل للأرشيف!")
                        else:
                            # تحديث باستخدام new_details بدل row['Dress_Details']
                            bookings_sheet.update(f"E{cell.row}:I{cell.row}", [[new_status, new_details, new_total, new_paid, new_remaining]])
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

    def to_num(val):
        try: return float(val)
        except: return 0.0
    
    # جلب البيانات
    df_cust = get_data(customers_sheet)
    search = st.text_input("🔎 ابحث باسم العميل:")
    
    if not df_cust.empty:
        # البحث والفلترة
        if search:
            display_df = df_cust[df_cust['Name'].str.contains(search, case=False, na=False)]
        else:
            display_df = df_cust
            
        if not display_df.empty:
            for idx, row in display_df.iterrows():
                with st.expander(f"👤 {row['Name']}"):
                    with st.form(f"edit_meas_{idx}"):
                        c1, c2, c3 = st.columns(3)
                        
                        # الحقول - ضفنا هنا خانة التليفون
                        new_phone = c1.text_input("رقم التليفون", value=str(row.get('Phone', '')), key=f"phone_{idx}")
                        new_chest = c1.number_input("دوران الصدر", value=to_num(row.get('Chest', '')), format="%f", step=0.5, key=f"chest_{idx}")
                        new_waist = c1.number_input("دوران الوسط", value=to_num(row.get('Waist', '')), format="%f", step=0.5, key=f"waist_{idx}")
                        new_dart = c1.number_input("بنسة الصدر", value=to_num(row.get('Chest_Dart', '')), format="%f", step=0.5, key=f"dart_{idx}")
                        new_thigh = c1.number_input("عرض الفخذ", value=to_num(row.get('Thigh_Width', '')), format="%f", step=0.5, key=f"thigh_{idx}")
                        
                        new_len = c2.number_input("الطول الكلي", value=to_num(row.get('Length', '')), format="%f", step=0.5, key=f"len_{idx}")
                        new_sleeve = c2.number_input("عرض الكم", value=to_num(row.get('Sleeve_Width', '')), format="%f", step=0.5, key=f"sleeve_{idx}")
                        new_neck = c2.number_input("طول الرقبة للوسط", value=to_num(row.get('Neck_to_Waist', '')), format="%f", step=0.5, key=f"neck_{idx}")
                        new_inseam = c2.number_input("الحجر الداخلي", value=to_num(row.get('Inseam', '')), format="%f", step=0.5, key=f"inseam_{idx}")
                        
                        new_waist_bot = c3.number_input("طول الوسط لأسفل", value=to_num(row.get('Waist_to_Bottom', '')), format="%f", step=0.5, key=f"wbot_{idx}")
                        new_hips = c3.number_input("دوران الأرداف", value=to_num(row.get('Hips', '')), format="%f", step=0.5, key=f"hips_{idx}")
                        new_crotch = c3.number_input("الحجر", value=to_num(row.get('Crotch', '')), format="%f", step=0.5, key=f"crotch_{idx}")
                        new_thigh_knee = c3.number_input("طول الفخذ للركبة", value=to_num(row.get('thigh_length_k', '')), format="%f", step=0.5, key=f"thk_{idx}")
                        new_notes = st.text_area("ملاحظات", value=str(row.get('Notes', '')), key=f"notes_{idx}")
                        
                        if st.form_submit_button("💾 تحديث المقاسات"):
                            try:
                                # 1. تحديد رقم السطر الفعلي
                                cell = customers_sheet.find(row['Name'])
                                actual_row_idx = cell.row
                                
                                # 2. جلب عناوين الأعمدة الحالية من الشيت
                                headers = customers_sheet.row_values(1)
                                
                                # 3. نظام "الربط الصارم"
                                def get_col_idx(name):
                                    try:
                                        return headers.index(name) + 1
                                    except:
                                        raise Exception(f"العمود '{name}' غير موجود في ملف الإكسيل!")

                                # 4. تجهيز قائمة التحديثات (الربط بالاسم)
                                updates = [
                                    (get_col_idx('Phone'), new_phone), # ضفنا دي هنا
                                    (get_col_idx('Chest'), new_chest),
                                    (get_col_idx('Waist'), new_waist),
                                    (get_col_idx('Chest_Dart'), new_dart),
                                    (get_col_idx('Thigh_Width'), new_thigh),
                                    (get_col_idx('Length'), new_len),
                                    (get_col_idx('Sleeve_Width'), new_sleeve),
                                    (get_col_idx('Neck_to_Waist'), new_neck),
                                    (get_col_idx('Inseam'), new_inseam),
                                    (get_col_idx('Waist_to_Bottom'), new_waist_bot),
                                    (get_col_idx('Hips'), new_hips),
                                    (get_col_idx('Crotch'), new_crotch),
                                    (get_col_idx('thigh_length_k'), new_thigh_knee),
                                    (get_col_idx('Notes'), new_notes)
                                ]
                                
                                # 5. التنفيذ
                                for col_idx, value in updates:
                                    customers_sheet.update_cell(actual_row_idx, col_idx, value)
                                
                                st.success(f"تم تحديث بيانات {row['Name']} بنجاح!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"⚠️ خطأ في التحديث: {e}")
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
        # **الإضافة الجديدة هنا:**
        st.write(f"📞 **رقم التليفون:** {cust_data.get('Phone', 'غير مسجل')}")
        
        if not cust_history.empty:
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
            st.dataframe(cust_history[['Registration_Date', 'Status', 'Total_Price', 'Paid', 'Remaining', 'Dress_Details']], use_container_width=True)
        else:
            st.warning("لا يوجد تاريخ طلبات لهذا العميل.")
            
#------------مديونيات العملاء--------------

elif choice == "💰 مديونيات العملاء":
    st.title("📂 ملفات المديونيات")
    
    # 1. جلب البيانات
    df = get_data(bookings_sheet)
    
    # تنظيف البيانات
    df['Total_Price'] = pd.to_numeric(df['Total_Price'], errors='coerce').fillna(0)
    df['Paid'] = pd.to_numeric(df['Paid'], errors='coerce').fillna(0)
    df['Remaining'] = df['Total_Price'] - df['Paid']
    
    # فلترة المديونيات فقط
    df_debtors = df[df['Remaining'] > 0]
    
    if not df_debtors.empty:
        total_all = df_debtors['Remaining'].sum()
        st.metric("💰 إجمالي المديونيات عند كل العملاء", f"{total_all:,.0f} ج.م")
        
        grouped = df_debtors.groupby('Name')
        
        for name, group in grouped:
            client_total_debt = group['Remaining'].sum()
            
            with st.expander(f"📁 العميل: {name} | إجمالي المديونية: {client_total_debt:,.0f} ج.م"):
                for idx, row in group.iterrows():
                    st.write("---")
                    
                    # عرض تفاصيل الطلب (قراءة فقط)
                    details_text = row.get('Dress_Details', 'لا توجد تفاصيل إضافية')
                    st.write(f"**الطلب:** {row.get('Status', 'غير محدد')}")
                    st.text_area("تفاصيل الطلب:", value=details_text, disabled=True, key=f"det_{idx}")
                    
                    with st.form(f"update_{idx}"):
                        st.write(f"💳 المدفوع حالياً: {row['Paid']} ج.م")
                        
                        # --- خانة الإجمالي بقت مقفولة (disabled=True) ---
                        st.number_input("إجمالي الحساب (للعلم فقط):", value=float(row['Total_Price']), disabled=True)
                        
                        # خانة إضافة دفعة جديدة
                        new_payment = st.number_input("إضافة دفعة جديدة:", value=0.0, step=50.0, key=f"p_{idx}")

                        if st.form_submit_button("💾 حفظ التحديث"):
                            try:
                                old_paid = float(row['Paid'])
                                updated_paid = old_paid + new_payment 
                                
                                actual_row_idx = idx + 2 
                                headers = bookings_sheet.row_values(1)
                                def get_col_idx(col_name): return headers.index(col_name) + 1
                                
                                # التحديث هنا هيحدث المدفوع فقط، الإجمالي يفضل زي ما هو
                                bookings_sheet.update_cell(actual_row_idx, get_col_idx('Paid'), str(updated_paid))
                                
                                st.success("تم التحديث!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ: {e}")
    else:
        st.success("مفيش أي مديونيات حالياً.")
        
#--------------تواريخ التسليم----------------

elif choice == "📅 التسليمات":
    st.title("📅 مواعيد التسليم القادمة")
    
    # جلب البيانات
    df_orders = get_data(bookings_sheet) # تأكد إن ده اسم شيت الطلبات عندك

    if not df_orders.empty:
        # 1. فلترة الطلبات التي لم يتم تسليمها (افترضنا إن اللي مش "تم التسليم" لسه شغال)
        # لو اسم العمود عندك مختلف (مثلاً 'الحالة') غيره في السطر ده
        active_orders = df_orders[df_orders['Status'] != 'تم التسليم']
        
        if not active_orders.empty:
            # 2. تحويل عمود التاريخ لنوع "تاريخ" عشان نقدر نرتبه
            # اتأكد إن اسم العمود عندك 'Delivery_Date' أو غيره حسب شيت الإكسيل
            active_orders['Delivery_Date'] = pd.to_datetime(active_orders['Delivery_Date'], dayfirst=True)
            
            # 3. ترتيب البيانات (من الأقرب للتاريخ الحالي للأبعد)
            active_orders = active_orders.sort_values(by='Delivery_Date', ascending=True)
            
            # عرض الطلبات
            for idx, row in active_orders.iterrows():
                # تلوين الطلبات اللي ميعادها النهاردة أو فات (تنبيه)
                delivery_date = row['Delivery_Date'].strftime('%Y-%m-%d')
                
                with st.expander(f"📦 {row['Name']} - موعد التسليم: {delivery_date}"):
                    st.write(f"**اسم العميل:** {row['Name']}")
                    st.write(f"**حالة الطلب:** {row['Status']}")
                    st.write(f"**المبلغ المتبقي:** {row['Remaining']} ج.م")
                    st.write(f"**ملاحظات:** {row['Dress_Details']}")
                    # هنا تقدر تضيف زرار "تم التسليم" لو تحب
        else:
            st.success("عاش! لا توجد طلبات معلقة حالياً.")
    else:
        st.info("لا توجد بيانات طلبات لعرضها.")


