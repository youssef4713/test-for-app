import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="Lobna's | Dashboard", page_icon="👗", layout="wide")

# --- حقن الـ CSS الاحترافي (الأنيميشن واللمس) ---
st.markdown("""
    <style>
    /* أنيميشن الدخول */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stApp { background-color: #f8f9fa; }
    
    /* تصميم الكروت مع أنيميشن */
    .css-card {
        background-color: white;
        padding: 25px;
        border-radius: 20px;
        border: none;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        animation: slideUp 0.6s ease-out;
    }
    
    /* جعل الأزرار مناسبة لللمس */
    div.stButton > button {
        border-radius: 12px;
        padding: 15px 30px;
        width: 100%;
        background-color: #2c3e50;
        color: white;
        font-weight: 600;
        border: none;
        transition: 0.3s;
        min-height: 50px; /* مريح للتابلت */
    }
    div.stButton > button:hover { background-color: #34495e; transform: scale(1.02); }
    
    /* تنسيق القائمة الجانبية للتابلت */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eee;
    }
    
    /* تحسين حقول الإدخال للمس */
    .stTextInput > div > div > input, .stTextArea textarea {
        border-radius: 12px !important;
        padding: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# الاتصال (نفس كود الاتصال السابق)
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("Atelier_Database")
    customers_sheet = sh.worksheet("customers")
    bookings_sheet = sh.worksheet("bookings")
    completed_sheet = sh.worksheet("completed_bookings") 
except Exception as e:
    st.error("خطأ في الاتصال، تأكد من إعدادات الـ Secrets.")
    st.stop()

def get_data(sheet):
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=[c.strip() for c in raw_data[0]])
        return df
    return pd.DataFrame()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown("## 👗 Lobna's")
    choice = st.radio("القائمة:", ["📊 لوحة التحكم", "➕ عميلة جديدة", "💰 الطلبات", "📦 الأرشيف", "🔍 بحث وتعديل"])

# --- الصفحة ---
st.markdown('<div class="css-card">', unsafe_allow_html=True)

if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة تحكم Lobna's")
    # هنا تحط كود الـ Metrics بتاعك
    st.write("أهلاً بك في نظام إدارة أتيليه Lobna's. اختر إجراء من القائمة الجانبية.")

elif choice == "➕ عميلة جديدة":
    st.subheader("➕ تسجيل عميلة جديدة")
    with st.form("new_cust"):
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم الزبونة")
        phone = c2.text_input("رقم التليفون")
        # .. باقي حقول المقاسات
        if st.form_submit_button("حفظ"):
            st.success("تم الحفظ!")

elif choice == "💰 الطلبات":
    st.subheader("💰 الطلبات الحالية")
    # إضافة زر إضافة طلب
    if st.button("➕ إضافة طلب جديد"):
        st.info("قم بملء البيانات أدناه...")
        # هنا الفورم
    
    # عرض الطلبات في كروت أنيقة
    df_book = get_data(bookings_sheet)
    for _, row in df_book.iterrows():
        st.markdown(f'''
            <div class="css-card" style="animation: none;">
                <h4>{row.get('Name')}</h4>
                <p>الحالة: <b>{row.get('Status')}</b></p>
            </div>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
