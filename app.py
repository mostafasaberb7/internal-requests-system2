import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import os

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="نظام متابعة الطلبات الداخلية",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; direction: rtl; }
.stApp, .main, .block-container { direction: rtl; text-align: right; }
.app-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    color: white; padding: 1.5rem 2rem; border-radius: 12px;
    margin-bottom: 1.5rem; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.app-header h1 { font-size: 1.8rem; margin: 0; font-weight: 700; }
.app-header p  { font-size: 1rem; margin: 0.3rem 0 0; opacity: 0.85; }
.card {
    background: white; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 1rem;
    border-right: 4px solid #2d6a9f;
}
.card-pending  { border-right-color: #f59e0b; }
.card-approved { border-right-color: #10b981; }
.card-rejected { border-right-color: #ef4444; }
.badge { display:inline-block; padding:0.25rem 0.75rem; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-pending  { background:#fef3c7; color:#92400e; }
.badge-approved { background:#d1fae5; color:#065f46; }
.badge-rejected { background:#fee2e2; color:#991b1b; }
.stButton > button {
    width: 100%; border-radius: 8px;
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem; padding: 0.6rem 1rem; font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.stTextInput label, .stSelectbox label, .stTextArea label {
    font-family: 'Tajawal', sans-serif !important; font-weight: 600; font-size: 0.95rem;
}
.stTextInput input, .stTextArea textarea { direction: rtl; text-align: right; }
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.5rem; }
    .app-header h1 { font-size: 1.4rem; }
    .stButton > button { font-size: 0.9rem; }
}
.success-box { background:#d1fae5; border-radius:8px; padding:1rem; color:#065f46; font-weight:600; text-align:center; margin:0.5rem 0; }
.error-box   { background:#fee2e2; border-radius:8px; padding:1rem; color:#991b1b; font-weight:600; text-align:center; margin:0.5rem 0; }
.info-box    { background:#dbeafe; border-radius:8px; padding:1rem; color:#1e40af; font-weight:600; text-align:center; margin:0.5rem 0; }
hr { border-color: #e5e7eb; }
.section-title {
    font-size:1.2rem; font-weight:700; color:#1e3a5f;
    margin:1rem 0 0.75rem; border-bottom:2px solid #2d6a9f; padding-bottom:0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  ⚙️ الإعدادات – عدّل هنا فقط
# ─────────────────────────────────────────

EMAIL_SENDER   = "mostfasaber37@gmail.com"          # ← غيّر
EMAIL_PASSWORD = "***********"      # ← App Password من Google

EXCEL_FILE = "requests.xlsx"               # ← اسم ملف التخزين (يُنشأ تلقائياً)

USERS = {
    "mostfasaber37@gmail.com":      {"name": "مصطفي صابر",      "role": "مندوب"},
    "agent2@company.com":      {"name": "سارة محمد",     "role": "مندوب"},
    "supervisor1@company.com": {"name": "خالد إبراهيم",  "role": "مشرف"},
    "supervisor2@company.com": {"name": "منى حسن",       "role": "مشرف"},
    "manager@company.com":     {"name": "عبدالله الأمير", "role": "مدير البيع"},
}

REQUEST_TYPES = ["إصلاح", "شراء قطع غيار", "صيانة دورية", "بدل فاقد", "طلب تأجير", "أخرى"]

STATUS_AR = {
    "Pending":                "قيد الانتظار",
    "Approved by Supervisor": "تمت الموافقة من المشرف",
    "Rejected by Supervisor": "تم الرفض من المشرف",
    "Approved by Manager":    "تمت الموافقة من المدير",
    "Rejected by Manager":    "تم الرفض من المدير",
}

SUPERVISORS = {k: v["name"] for k, v in USERS.items() if v["role"] == "مشرف"}

COLUMNS = [
    "ID", "اسم المندوب", "البريد الإلكتروني",
    "رقم السيارة", "نوع السيارة", "نوع الطلب",
    "وصف المشكلة", "المشرف", "الحالة", "المدير",
    "التعليقات", "Timestamp"
]


# ─────────────────────────────────────────
#  EXCEL HELPERS
# ─────────────────────────────────────────

def load_data() -> pd.DataFrame:
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, dtype=str)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS].fillna("")
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)


def save_data(df: pd.DataFrame):
    df.to_excel(EXCEL_FILE, index=False)


def append_row(row: dict):
    df  = load_data()
    new = pd.DataFrame([{col: row.get(col, "") for col in COLUMNS}])
    df  = pd.concat([df, new], ignore_index=True)
    save_data(df)


def update_row(request_id: str, updates: dict):
    df   = load_data()
    mask = df["ID"] == request_id
    if mask.any():
        for col, val in updates.items():
            if col in df.columns:
                df.loc[mask, col] = val
        save_data(df)


# ─────────────────────────────────────────
#  EMAIL
# ─────────────────────────────────────────

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to_email
        html = f"""<html dir="rtl"><body style="font-family:Tajawal,Arial;direction:rtl;
              background:#f8fafc;padding:20px;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;
                    box-shadow:0 2px 10px rgba(0,0,0,.1);overflow:hidden;">
          <div style="background:linear-gradient(135deg,#1e3a5f,#2d6a9f);
                      color:white;padding:20px;text-align:center;">
            <h2 style="margin:0;">نظام متابعة الطلبات الداخلية</h2></div>
          <div style="padding:24px;">
            <p style="font-size:15px;line-height:1.8;color:#374151;">
              {body.replace(chr(10), '<br>')}</p></div>
          <div style="background:#f1f5f9;padding:12px;text-align:center;
                      font-size:12px;color:#6b7280;">هذا بريد آلي – لا تردّ عليه</div>
        </div></body></html>"""
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
    except Exception as e:
        st.warning(f"⚠️ تعذّر إرسال الإشعار: {e}")


# ─────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────

def status_badge(status: str) -> str:
    cls = "badge-approved" if "Approved" in status else \
          "badge-rejected" if "Rejected" in status else "badge-pending"
    return f'<span class="badge {cls}">{STATUS_AR.get(status, status)}</span>'


def request_card(row, card_cls="card-pending"):
    sup_name     = USERS.get(row.get("المشرف",""), {}).get("name", row.get("المشرف",""))
    comment      = row.get("التعليقات","")
    comment_html = f"<p>💬 <strong>التعليق:</strong> {comment}</p>" if comment else ""
    return f"""
    <div class="card {card_cls}">
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
        <strong>🔖 #{row.get('ID','')}</strong>
        {status_badge(row.get('الحالة','Pending'))}
      </div>
      <hr style="margin:6px 0;">
      <p>👤 <strong>المندوب:</strong> {row.get('اسم المندوب','')} &nbsp;|&nbsp;
         📧 {row.get('البريد الإلكتروني','')}</p>
      <p>🚗 <strong>السيارة:</strong> {row.get('رقم السيارة','')} – {row.get('نوع السيارة','')}</p>
      <p>📌 <strong>نوع الطلب:</strong> {row.get('نوع الطلب','')}</p>
      <p>📝 <strong>التفاصيل:</strong> {row.get('وصف المشكلة','')}</p>
      <p>🔍 <strong>المشرف:</strong> {sup_name}</p>
      <p>🕐 <strong>التاريخ:</strong> {row.get('Timestamp','')}</p>
      {comment_html}
    </div>"""


# ─────────────────────────────────────────
#  PAGE: LOGIN
# ─────────────────────────────────────────

def page_login():
    st.markdown("""
    <div class="app-header">
        <h1>📋 نظام متابعة الطلبات الداخلية</h1>
        <p>منصة رقمية لإدارة ومتابعة طلبات الصيانة والمشتريات</p>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔑 تسجيل الدخول</div>', unsafe_allow_html=True)
        email = st.text_input("البريد الإلكتروني", placeholder="example@company.com")
        if st.button("دخول →", type="primary"):
            e = email.strip().lower()
            if e in USERS:
                st.session_state["user_email"] = e
                st.session_state["user_info"]  = USERS[e]
                st.rerun()
            else:
                st.markdown('<div class="error-box">🚫 أنت غير مسموح لك بالدخول</div>',
                            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
#  PAGE: AGENT
# ─────────────────────────────────────────

def page_agent(user_email, user_info):
    st.markdown(f"""
    <div class="app-header">
        <h1>👤 مرحباً، {user_info['name']}</h1>
        <p>لوحة تحكم المندوب</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 إرسال طلب جديد", "📋 طلباتي"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">تفاصيل الطلب الجديد</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            agent_name   = st.text_input("اسم المندوب *", value=user_info["name"])
            car_number   = st.text_input("رقم السيارة *", placeholder="مثال: أ ب ج 1234")
        with c2:
            car_type     = st.text_input("نوع السيارة *", placeholder="مثال: تويوتا هايلكس 2022")
            request_type = st.selectbox("نوع الطلب *", REQUEST_TYPES)
        problem_desc      = st.text_area("وصف المشكلة / التفاصيل *", height=120,
                                         placeholder="اكتب وصفاً تفصيلياً...")
        sup_name_sel      = st.selectbox("المشرف المسؤول *", list(SUPERVISORS.values()))
        supervisor_email  = {v: k for k, v in SUPERVISORS.items()}[sup_name_sel]
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("✅ إرسال الطلب", type="primary"):
            if not all([agent_name.strip(), car_number.strip(), car_type.strip(), problem_desc.strip()]):
                st.markdown('<div class="error-box">⚠️ يرجى تعبئة جميع الحقول المطلوبة</div>',
                            unsafe_allow_html=True)
            else:
                req_id = str(uuid.uuid4())[:8].upper()
                append_row({
                    "ID": req_id, "اسم المندوب": agent_name,
                    "البريد الإلكتروني": user_email, "رقم السيارة": car_number,
                    "نوع السيارة": car_type, "نوع الطلب": request_type,
                    "وصف المشكلة": problem_desc, "المشرف": supervisor_email,
                    "الحالة": "Pending", "المدير": "", "التعليقات": "",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                st.markdown(f'<div class="success-box">✅ تم إرسال طلبك بنجاح! رقم الطلب: {req_id}</div>',
                            unsafe_allow_html=True)
                st.balloons()

    with tab2:
        df    = load_data()
        my_df = df[df["البريد الإلكتروني"] == user_email] if not df.empty else pd.DataFrame()
        if my_df.empty:
            st.markdown('<div class="info-box">لم تقم بإرسال أي طلبات حتى الآن</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">إجمالي طلباتك: {len(my_df)}</div>',
                        unsafe_allow_html=True)
            for _, row in my_df.iterrows():
                s = row.get("الحالة","Pending")
                cls = "card-approved" if "Approved" in s else \
                      "card-rejected" if "Rejected" in s else "card-pending"
                st.markdown(request_card(row, cls), unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()


# ─────────────────────────────────────────
#  PAGE: SUPERVISOR
# ─────────────────────────────────────────

def page_supervisor(user_email, user_info):
    st.markdown(f"""
    <div class="app-header">
        <h1>🔍 مرحباً، {user_info['name']}</h1>
        <p>لوحة تحكم المشرف</p>
    </div>""", unsafe_allow_html=True)

    df = load_data()
    pending = df[(df["المشرف"] == user_email) & (df["الحالة"] == "Pending")] \
              if not df.empty else pd.DataFrame()

    st.markdown(f'<div class="info-box">الطلبات المعلّقة عليك: {len(pending)}</div>',
                unsafe_allow_html=True)

    if pending.empty:
        st.markdown('<div class="success-box">✅ لا توجد طلبات معلّقة حالياً</div>',
                    unsafe_allow_html=True)
    else:
        for _, row in pending.iterrows():
            req_id = row.get("ID","")
            st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)
            comment = st.text_area(f"تعليق #{req_id}", key=f"sc_{req_id}",
                                   placeholder="أضف تعليقاً (مطلوب عند الرفض)")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ موافقة", key=f"sa_{req_id}", type="primary"):
                    update_row(req_id, {"الحالة":"Approved by Supervisor",
                                        "التعليقات":comment,
                                        "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M")})
                    send_email(row["البريد الإلكتروني"],
                               "تحديث حالة طلبك – نظام الطلبات الداخلية",
                               f"مرحباً {row['اسم المندوب']},\n\n"
                               f"تمت الموافقة على طلبك من المشرف ✅\n"
                               f"• رقم الطلب: {req_id}\n• رقم السيارة: {row['رقم السيارة']}\n"
                               f"• نوع السيارة: {row['نوع السيارة']}\n• نوع الطلب: {row['نوع الطلب']}\n"
                               f"• سيتم إحالته للمدير للمراجعة النهائية."
                               + (f"\n• تعليق المشرف: {comment}" if comment else ""))
                    st.markdown('<div class="success-box">✅ تمت الموافقة وإشعار المندوب</div>',
                                unsafe_allow_html=True)
                    st.rerun()
            with c2:
                if st.button("❌ رفض", key=f"sr_{req_id}"):
                    if not comment.strip():
                        st.warning("⚠️ يرجى كتابة سبب الرفض في التعليق")
                    else:
                        update_row(req_id, {"الحالة":"Rejected by Supervisor",
                                            "التعليقات":comment,
                                            "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M")})
                        send_email(row["البريد الإلكتروني"],
                                   "تحديث حالة طلبك – نظام الطلبات الداخلية",
                                   f"مرحباً {row['اسم المندوب']},\n\n"
                                   f"نأسف، تم رفض طلبك من المشرف ❌\n"
                                   f"• رقم الطلب: {req_id}\n• رقم السيارة: {row['رقم السيارة']}\n"
                                   f"• نوع السيارة: {row['نوع السيارة']}\n• نوع الطلب: {row['نوع الطلب']}\n"
                                   f"• سبب الرفض: {comment}")
                        st.markdown('<div class="error-box">❌ تم الرفض وإشعار المندوب</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
            st.divider()

    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()


# ─────────────────────────────────────────
#  PAGE: MANAGER
# ─────────────────────────────────────────

def page_manager(user_email, user_info):
    st.markdown(f"""
    <div class="app-header">
        <h1>🏢 مرحباً، {user_info['name']}</h1>
        <p>لوحة تحكم المدير / رئيس المركز</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📥 الطلبات الواردة", "📊 كل الطلبات"])
    df = load_data()

    with tab1:
        sup_approved = df[df["الحالة"] == "Approved by Supervisor"] \
                       if not df.empty else pd.DataFrame()
        st.markdown(f'<div class="info-box">الطلبات الواردة من المشرفين: {len(sup_approved)}</div>',
                    unsafe_allow_html=True)
        if sup_approved.empty:
            st.markdown('<div class="success-box">لا توجد طلبات بانتظار موافقتك</div>',
                        unsafe_allow_html=True)
        else:
            for _, row in sup_approved.iterrows():
                req_id = row.get("ID","")
                st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)
                comment = st.text_area(f"تعليق #{req_id}", key=f"mc_{req_id}",
                                       placeholder="أضف تعليقاً (مطلوب عند الرفض)")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ موافقة", key=f"ma_{req_id}", type="primary"):
                        update_row(req_id, {"الحالة":"Approved by Manager",
                                            "المدير":user_email, "التعليقات":comment,
                                            "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M")})
                        send_email(row["البريد الإلكتروني"],
                                   "تحديث حالة طلبك – نظام الطلبات الداخلية",
                                   f"مرحباً {row['اسم المندوب']},\n\n"
                                   f"يسعدنا إبلاغك بالموافقة النهائية على طلبك ✅\n"
                                   f"• رقم الطلب: {req_id}\n• رقم السيارة: {row['رقم السيارة']}\n"
                                   f"• نوع السيارة: {row['نوع السيارة']}\n• نوع الطلب: {row['نوع الطلب']}\n"
                                   f"• الحالة: تمت الموافقة من المدير ✅"
                                   + (f"\n• تعليق المدير: {comment}" if comment else ""))
                        st.markdown('<div class="success-box">✅ تمت الموافقة النهائية وإشعار المندوب</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
                with c2:
                    if st.button("❌ رفض", key=f"mr_{req_id}"):
                        if not comment.strip():
                            st.warning("⚠️ يرجى كتابة سبب الرفض في التعليق")
                        else:
                            update_row(req_id, {"الحالة":"Rejected by Manager",
                                                "المدير":user_email, "التعليقات":comment,
                                                "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M")})
                            send_email(row["البريد الإلكتروني"],
                                       "تحديث حالة طلبك – نظام الطلبات الداخلية",
                                       f"مرحباً {row['اسم المندوب']},\n\n"
                                       f"نأسف، تم رفض طلبك من المدير ❌\n"
                                       f"• رقم الطلب: {req_id}\n• رقم السيارة: {row['رقم السيارة']}\n"
                                       f"• نوع السيارة: {row['نوع السيارة']}\n• نوع الطلب: {row['نوع الطلب']}\n"
                                       f"• سبب الرفض: {comment}")
                            st.markdown('<div class="error-box">❌ تم الرفض وإشعار المندوب</div>',
                                        unsafe_allow_html=True)
                            st.rerun()
                st.divider()

    with tab2:
        if df.empty:
            st.markdown('<div class="info-box">لا توجد طلبات مسجلة</div>', unsafe_allow_html=True)
        else:
            show = df.copy()
            show["الحالة"] = show["الحالة"].map(lambda s: STATUS_AR.get(s, s))
            cols = ["ID","اسم المندوب","رقم السيارة","نوع السيارة","نوع الطلب","الحالة","Timestamp"]
            st.dataframe(show[[c for c in cols if c in show.columns]], use_container_width=True)
            with open(EXCEL_FILE, "rb") as f:
                st.download_button("📥 تحميل ملف Excel", data=f,
                                   file_name="requests.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────

def main():
    if "user_email" not in st.session_state:
        page_login(); return

    role = st.session_state["user_info"].get("role","")
    email = st.session_state["user_email"]
    info  = st.session_state["user_info"]

    if role == "agent":       page_agent(email, info)
    elif role == "supervisor": page_supervisor(email, info)
    elif role == "manager":    page_manager(email, info)
    else:
        st.error("دور المستخدم غير معروف.")
        if st.button("خروج"): st.session_state.clear(); st.rerun()

if __name__ == "__main__":
    main()
