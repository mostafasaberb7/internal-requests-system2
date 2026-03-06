import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import os
import hashlib

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
#  CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
}
.stApp, .main, .block-container {
    direction: rtl;
    text-align: right;
}

/* ── شاشة الدخول ── */
.login-wrapper {
    min-height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-box {
    background: white;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 40px rgba(0,0,0,0.12);
    max-width: 420px;
    width: 100%;
    text-align: center;
}
.login-logo { font-size: 3.5rem; margin-bottom: 0.5rem; }
.login-title { font-size: 1.5rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0.3rem; }
.login-sub   { font-size: 0.9rem; color: #6b7280; margin-bottom: 1.5rem; }
.login-help {
    background: #f0f9ff;
    border-radius: 10px;
    padding: 1rem;
    margin-top: 1.2rem;
    text-align: right;
    font-size: 0.85rem;
    color: #1e40af;
    line-height: 1.8;
}
.login-help b { color: #1e3a5f; }

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    color: white; padding: 1.2rem 2rem; border-radius: 12px;
    margin-bottom: 1.2rem; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.app-header h1 { font-size: 1.6rem; margin: 0; font-weight: 700; }
.app-header p  { font-size: 0.95rem; margin: 0.3rem 0 0; opacity: 0.85; }

/* ── Cards ── */
.card {
    background: white; border-radius: 12px; padding: 1.4rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); margin-bottom: 1rem;
    border-right: 4px solid #2d6a9f;
}
.card-pending  { border-right-color: #f59e0b; }
.card-approved { border-right-color: #10b981; }
.card-rejected { border-right-color: #ef4444; }

/* ── Badge ── */
.badge { display:inline-block; padding:0.2rem 0.7rem; border-radius:20px; font-size:0.78rem; font-weight:700; }
.badge-pending  { background:#fef3c7; color:#92400e; }
.badge-approved { background:#d1fae5; color:#065f46; }
.badge-rejected { background:#fee2e2; color:#991b1b; }

/* ── Buttons ── */
.stButton > button {
    width: 100%; border-radius: 8px;
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem; padding: 0.55rem 1rem; font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

/* ── Inputs ── */
.stTextInput label, .stSelectbox label, .stTextArea label, .stDateInput label {
    font-family: 'Tajawal', sans-serif !important; font-weight: 600; font-size: 0.93rem;
}
.stTextInput input, .stTextArea textarea { direction: rtl; text-align: right; }

/* ── Alerts ── */
.success-box { background:#d1fae5; border-radius:8px; padding:0.9rem; color:#065f46; font-weight:600; text-align:center; margin:0.5rem 0; }
.error-box   { background:#fee2e2; border-radius:8px; padding:0.9rem; color:#991b1b; font-weight:600; text-align:center; margin:0.5rem 0; }
.info-box    { background:#dbeafe; border-radius:8px; padding:0.9rem; color:#1e40af; font-weight:600; text-align:center; margin:0.5rem 0; }
.warn-box    { background:#fef3c7; border-radius:8px; padding:0.9rem; color:#92400e; font-weight:600; text-align:center; margin:0.5rem 0; }

/* ── User badge ── */
.user-badge {
    background: #1e3a5f; color: white; padding: 0.35rem 1rem;
    border-radius: 20px; font-size: 0.82rem; font-weight: 600;
    display: inline-block; margin-bottom: 0.8rem;
}

hr { border-color: #e5e7eb; }
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #1e3a5f;
    margin: 1rem 0 0.6rem; border-bottom: 2px solid #2d6a9f; padding-bottom: 0.3rem;
}

@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.4rem; }
    .app-header h1 { font-size: 1.3rem; }
    .login-box { padding: 1.8rem 1.2rem; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  ⚙️ الإعدادات
# ─────────────────────────────────────────

EMAIL_SENDER   = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EXCEL_FILE     = "requests.xlsx"

def h(p): return hashlib.sha256(p.encode()).hexdigest()

# ─── المستخدمون ───
# الأدوار: agent | supervisor | maintenance_supervisor | manager
USERS = {
    "ahmed":        {"password": h("1234"),   "name": "أحمد علي",        "role": "agent"},
    "sara":         {"password": h("1234"),   "name": "سارة محمد",       "role": "agent"},
    "omar":         {"password": h("1234"),   "name": "عمر خالد",        "role": "agent"},
    "mohamed":      {"password": h("1234"),   "name": "محمد سعيد",       "role": "agent"},
    "khalid":       {"password": h("sup1"),   "name": "خالد إبراهيم",    "role": "supervisor"},
    "mona":         {"password": h("sup2"),   "name": "منى حسن",         "role": "supervisor"},
    "ali_maint":    {"password": h("maint1"), "name": "علي الصيانة",     "role": "maintenance_supervisor"},
    "sami_maint":   {"password": h("maint2"), "name": "سامي الصيانة",    "role": "maintenance_supervisor"},
    "manager":      {"password": h("mgr1"),   "name": "عبدالله الأمير",  "role": "manager"},
}

AGENT_NAMES      = [v["name"] for v in USERS.values() if v["role"] == "agent"]
SUPERVISOR_NAMES = [v["name"] for v in USERS.values() if v["role"] == "supervisor"]

CAR_NUMBERS = [
    "أ ب ج 1234", "د هـ و 5678", "ز ح ط 9012",
    "ي ك ل 3456", "م ن س 7890", "ع غ ف 1111",
]

REQUEST_TYPES = ["إصلاح", "شراء قطع غيار", "صيانة دورية", "بدل فاقد", "طلب تأجير", "أخرى"]

STATUS_AR = {
    "Pending":                "⏳ قيد الانتظار",
    "Approved by Supervisor": "✅ موافقة المشرف",
    "Rejected by Supervisor": "❌ رفض المشرف",
    "Approved by Manager":    "✅ موافقة المدير",
    "Rejected by Manager":    "❌ رفض المدير",
}

ROLE_AR = {
    "agent":                  "مندوب",
    "supervisor":             "مشرف",
    "maintenance_supervisor": "مشرف صيانة",
    "manager":                "مدير",
}

COLUMNS = [
    "ID", "اسم المندوب", "اسم المستخدم",
    "رقم السيارة", "نوع السيارة", "نوع الطلب",
    "وصف المشكلة", "المشرف", "الحالة", "المدير",
    "التعليقات", "آخر تاريخ صيانة", "Timestamp",
]


# ─────────────────────────────────────────
#  EXCEL
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
    if not to_email or "@" not in to_email:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to_email
        html = f"""<html dir="rtl"><body style="font-family:Tajawal,Arial;direction:rtl;background:#f8fafc;padding:20px;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.1);overflow:hidden;">
          <div style="background:linear-gradient(135deg,#1e3a5f,#2d6a9f);color:white;padding:20px;text-align:center;">
            <h2 style="margin:0;">نظام متابعة الطلبات الداخلية</h2></div>
          <div style="padding:24px;">
            <p style="font-size:15px;line-height:1.8;color:#374151;">{body.replace(chr(10),'<br>')}</p></div>
          <div style="background:#f1f5f9;padding:12px;text-align:center;font-size:12px;color:#6b7280;">هذا بريد آلي – لا تردّ عليه</div>
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
    comment    = row.get("التعليقات","")
    last_maint = row.get("آخر تاريخ صيانة","")
    c_html = f"<p>💬 <strong>التعليق:</strong> {comment}</p>" if comment else ""
    m_html = f"<p>🔧 <strong>آخر تاريخ صيانة:</strong> {last_maint}</p>" if last_maint else ""
    return f"""
    <div class="card {card_cls}">
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
        <strong>🔖 #{row.get('ID','')}</strong>
        {status_badge(row.get('الحالة','Pending'))}
      </div>
      <hr style="margin:6px 0;">
      <p>👤 <strong>المندوب:</strong> {row.get('اسم المندوب','')}</p>
      <p>🚗 <strong>السيارة:</strong> {row.get('رقم السيارة','')} – {row.get('نوع السيارة','')}</p>
      <p>📌 <strong>نوع الطلب:</strong> {row.get('نوع الطلب','')}</p>
      <p>📝 <strong>التفاصيل:</strong> {row.get('وصف المشكلة','')}</p>
      <p>🔍 <strong>المشرف:</strong> {row.get('المشرف','')}</p>
      <p>🕐 <strong>التاريخ:</strong> {row.get('Timestamp','')}</p>
      {m_html}{c_html}
    </div>"""

def show_user_bar():
    info = st.session_state.get("user_info", {})
    st.markdown(
        f'<div class="user-badge">👤 {info.get("name","")} &nbsp;|&nbsp; '
        f'{ROLE_AR.get(info.get("role",""), "")}</div>',
        unsafe_allow_html=True)

def logout_btn():
    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        for k in ["logged_in","username","user_info"]:
            st.session_state.pop(k, None)
        st.rerun()

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ─────────────────────────────────────────
#  صفحة تسجيل الدخول
# ─────────────────────────────────────────

def page_login():
    st.markdown("""
    <div class="app-header">
        <h1>📋 نظام متابعة الطلبات الداخلية</h1>
        <p>منصة رقمية لإدارة طلبات الصيانة والمشتريات</p>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:2.5rem 2rem;
             box-shadow:0 8px 40px rgba(0,0,0,0.12);text-align:center;">
            <div style="font-size:3.5rem;">📋</div>
            <div style="font-size:1.5rem;font-weight:700;color:#1e3a5f;margin-bottom:0.3rem;">
                تسجيل الدخول
            </div>
            <div style="font-size:0.9rem;color:#6b7280;margin-bottom:1.5rem;">
                أدخل بيانات حسابك للمتابعة
            </div>
        </div>""", unsafe_allow_html=True)

        username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("🔒 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")

        if st.button("دخول ←", type="primary"):
            u = username.strip().lower()
            if u in USERS and USERS[u]["password"] == h(password):
                st.session_state["logged_in"] = True
                st.session_state["username"]  = u
                st.session_state["user_info"] = USERS[u]
                st.rerun()
            else:
                st.markdown(
                    '<div class="error-box">🚫 اسم المستخدم أو كلمة المرور غير صحيحة،<br>يرجى المحاولة مرة أخرى</div>',
                    unsafe_allow_html=True)

        # ── شرح طريقة الدخول ──
        st.markdown("""
        <div class="login-help">
            <b>📌 كيفية تسجيل الدخول:</b><br>
            ١. اكتب اسم المستخدم الخاص بك في الخانة الأولى<br>
            ٢. اكتب كلمة المرور في الخانة الثانية<br>
            ٣. اضغط زر <b>دخول</b><br><br>
            <b>💡 ملاحظة:</b> إذا كنت تدخل لأول مرة أو نسيت بياناتك،<br>
            تواصل مع مسؤول النظام للحصول على حسابك.
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────
#  صفحة المندوب
# ─────────────────────────────────────────

def page_agent():
    info = st.session_state["user_info"]
    st.markdown(f"""
    <div class="app-header">
        <h1>👤 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم المندوب – إرسال ومتابعة الطلبات</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    tab1, tab2 = st.tabs(["📝 إرسال طلب جديد", "📋 متابعة طلباتي"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">تفاصيل الطلب الجديد</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            default_i  = AGENT_NAMES.index(info["name"]) if info["name"] in AGENT_NAMES else 0
            agent_name = st.selectbox("👤 اسم المندوب *", AGENT_NAMES, index=default_i)
            car_number = st.selectbox("🚗 رقم السيارة *", CAR_NUMBERS)
        with c2:
            car_type     = st.text_input("🏷️ نوع السيارة *", placeholder="مثال: تويوتا هايلكس 2022")
            request_type = st.selectbox("📌 نوع الطلب *", REQUEST_TYPES)

        problem_desc = st.text_area("📝 وصف المشكلة / التفاصيل *", height=120,
                                    placeholder="اكتب وصفاً تفصيلياً للمشكلة أو الطلب...")
        supervisor   = st.selectbox("🔍 المشرف المسؤول *", SUPERVISOR_NAMES)

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("✅ إرسال الطلب", type="primary"):
            if not all([car_type.strip(), problem_desc.strip()]):
                st.markdown('<div class="error-box">⚠️ يرجى تعبئة جميع الحقول المطلوبة</div>',
                            unsafe_allow_html=True)
            else:
                req_id = str(uuid.uuid4())[:8].upper()
                append_row({
                    "ID":               req_id,
                    "اسم المندوب":      agent_name,
                    "اسم المستخدم":     st.session_state["username"],
                    "رقم السيارة":      car_number,
                    "نوع السيارة":      car_type,
                    "نوع الطلب":        request_type,
                    "وصف المشكلة":      problem_desc,
                    "المشرف":           supervisor,
                    "الحالة":           "Pending",
                    "المدير":           "",
                    "التعليقات":        "",
                    "آخر تاريخ صيانة": "",
                    "Timestamp":        now_str(),
                })
                st.markdown(
                    f'<div class="success-box">✅ تم إرسال طلبك بنجاح!<br>'
                    f'رقم طلبك: <strong style="font-size:1.2rem">{req_id}</strong><br>'
                    f'<small>احتفظ بهذا الرقم لمتابعة طلبك</small></div>',
                    unsafe_allow_html=True)
                st.balloons()

    with tab2:
        df    = load_data()
        my_df = df[df["اسم المستخدم"] == st.session_state["username"]] \
                if not df.empty else pd.DataFrame()

        if my_df.empty:
            st.markdown('<div class="info-box">📭 لم تقم بإرسال أي طلبات حتى الآن</div>',
                        unsafe_allow_html=True)
        else:
            # إحصائيات سريعة
            total    = len(my_df)
            pending  = len(my_df[my_df["الحالة"] == "Pending"])
            approved = len(my_df[my_df["الحالة"].str.contains("Approved", na=False)])
            rejected = len(my_df[my_df["الحالة"].str.contains("Rejected", na=False)])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي الطلبات", total)
            c2.metric("⏳ قيد الانتظار", pending)
            c3.metric("✅ معتمدة", approved)
            c4.metric("❌ مرفوضة", rejected)
            st.divider()

            for _, row in my_df.iterrows():
                s   = row.get("الحالة","Pending")
                cls = "card-approved" if "Approved" in s else \
                      "card-rejected" if "Rejected" in s else "card-pending"
                st.markdown(request_card(row, cls), unsafe_allow_html=True)

    logout_btn()


# ─────────────────────────────────────────
#  صفحة المشرف
# ─────────────────────────────────────────

def page_supervisor():
    info     = st.session_state["user_info"]
    sup_name = info["name"]

    st.markdown(f"""
    <div class="app-header">
        <h1>🔍 مرحباً، {sup_name}</h1>
        <p>لوحة تحكم المشرف – مراجعة الطلبات والبت فيها</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    df = load_data()
    pending = df[
        (df["المشرف"] == sup_name) & (df["الحالة"] == "Pending")
    ] if not df.empty else pd.DataFrame()

    st.markdown(f'<div class="info-box">📬 الطلبات المعلّقة عليك: <strong>{len(pending)}</strong></div>',
                unsafe_allow_html=True)

    if pending.empty:
        st.markdown('<div class="success-box">✅ لا توجد طلبات معلّقة حالياً، أنجزت جميع الطلبات!</div>',
                    unsafe_allow_html=True)
    else:
        for _, row in pending.iterrows():
            req_id = row.get("ID","")
            st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)

            comment = st.text_area(
                f"💬 تعليق على الطلب #{req_id}",
                key=f"sc_{req_id}",
                placeholder="أضف تعليقاً – مطلوب عند الرفض، اختياري عند الموافقة")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ موافقة على الطلب", key=f"sa_{req_id}", type="primary"):
                    update_row(req_id, {
                        "الحالة":    "Approved by Supervisor",
                        "التعليقات": comment,
                        "Timestamp": now_str(),
                    })
                    st.markdown(
                        '<div class="success-box">✅ تمت الموافقة – الطلب انتقل للمدير للموافقة النهائية</div>',
                        unsafe_allow_html=True)
                    st.rerun()
            with c2:
                if st.button("❌ رفض الطلب", key=f"sr_{req_id}"):
                    if not comment.strip():
                        st.markdown('<div class="error-box">⚠️ يرجى كتابة سبب الرفض في خانة التعليق أولاً</div>',
                                    unsafe_allow_html=True)
                    else:
                        update_row(req_id, {
                            "الحالة":    "Rejected by Supervisor",
                            "التعليقات": comment,
                            "Timestamp": now_str(),
                        })
                        st.markdown('<div class="error-box">❌ تم رفض الطلب وتسجيله</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
            st.divider()

    logout_btn()


# ─────────────────────────────────────────
#  صفحة مشرف الصيانة
# ─────────────────────────────────────────

def page_maintenance_supervisor():
    info = st.session_state["user_info"]

    st.markdown(f"""
    <div class="app-header">
        <h1>🔧 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم مشرف الصيانة – تسجيل تواريخ الصيانة</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    st.markdown("""
    <div class="info-box">
        📌 صلاحيتك: تسجيل وتحديث <strong>آخر تاريخ صيانة</strong> للطلبات المعتمدة فقط.<br>
        هذا الحقل لا يستطيع تعديله أي شخص آخر في النظام.
    </div>""", unsafe_allow_html=True)

    df = load_data()

    if df.empty:
        st.markdown('<div class="info-box">📭 لا توجد طلبات في النظام بعد</div>',
                    unsafe_allow_html=True)
        logout_btn()
        return

    approved_df = df[df["الحالة"].str.contains("Approved", na=False)].copy()

    if approved_df.empty:
        st.markdown('<div class="warn-box">⏳ لا توجد طلبات معتمدة حتى الآن</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box">📋 عدد الطلبات المعتمدة: <strong>{len(approved_df)}</strong></div>',
                    unsafe_allow_html=True)
        st.divider()

        for _, row in approved_df.iterrows():
            req_id     = row.get("ID","")
            last_maint = row.get("آخر تاريخ صيانة","")
            s          = row.get("الحالة","")
            cls        = "card-approved"

            st.markdown(request_card(row, cls), unsafe_allow_html=True)

            current_label = f"التاريخ المسجّل حالياً: {last_maint}" if last_maint else "لم يُسجَّل تاريخ صيانة بعد"
            st.markdown(f'<div class="warn-box">🔧 {current_label}</div>', unsafe_allow_html=True)

            new_date = st.date_input(
                f"📅 تحديث آخر تاريخ صيانة – طلب #{req_id}",
                key=f"mdate_{req_id}",
                value=datetime.today(),
                format="YYYY/MM/DD"
            )
            if st.button(f"💾 حفظ تاريخ الصيانة – #{req_id}", key=f"msave_{req_id}", type="primary"):
                update_row(req_id, {"آخر تاريخ صيانة": str(new_date)})
                st.markdown('<div class="success-box">✅ تم حفظ تاريخ الصيانة بنجاح</div>',
                            unsafe_allow_html=True)
                st.rerun()
            st.divider()

    logout_btn()


# ─────────────────────────────────────────
#  صفحة المدير
# ─────────────────────────────────────────

def page_manager():
    info = st.session_state["user_info"]

    st.markdown(f"""
    <div class="app-header">
        <h1>🏢 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم المدير – الموافقة النهائية وعرض التقارير</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    tab1, tab2, tab3 = st.tabs([
        "📥 طلبات بانتظار موافقتي",
        "⚡ موافقة مباشرة",
        "📊 كل الطلبات والتقارير",
    ])

    df = load_data()

    # ── تبويب ١: موافقة المشرف → بانتظار المدير ──
    with tab1:
        st.markdown('<div class="section-title">الطلبات التي وافق عليها المشرف وتنتظر موافقتك</div>',
                    unsafe_allow_html=True)

        sup_appr = df[df["الحالة"] == "Approved by Supervisor"] \
                   if not df.empty else pd.DataFrame()

        st.markdown(f'<div class="info-box">📬 عدد الطلبات الواردة: <strong>{len(sup_appr)}</strong></div>',
                    unsafe_allow_html=True)

        if sup_appr.empty:
            st.markdown('<div class="success-box">✅ لا توجد طلبات بانتظار موافقتك حالياً</div>',
                        unsafe_allow_html=True)
        else:
            for _, row in sup_appr.iterrows():
                req_id = row.get("ID","")
                st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)
                comment = st.text_area(f"💬 تعليق #{req_id}", key=f"mc1_{req_id}",
                                       placeholder="أضف تعليقاً – مطلوب عند الرفض")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ موافقة نهائية", key=f"ma1_{req_id}", type="primary"):
                        update_row(req_id, {
                            "الحالة":    "Approved by Manager",
                            "المدير":    info["name"],
                            "التعليقات": comment,
                            "Timestamp": now_str(),
                        })
                        st.markdown('<div class="success-box">✅ تمت الموافقة النهائية على الطلب</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
                with c2:
                    if st.button("❌ رفض الطلب", key=f"mr1_{req_id}"):
                        if not comment.strip():
                            st.markdown('<div class="error-box">⚠️ يرجى كتابة سبب الرفض أولاً</div>',
                                        unsafe_allow_html=True)
                        else:
                            update_row(req_id, {
                                "الحالة":    "Rejected by Manager",
                                "المدير":    info["name"],
                                "التعليقات": comment,
                                "Timestamp": now_str(),
                            })
                            st.markdown('<div class="error-box">❌ تم رفض الطلب</div>',
                                        unsafe_allow_html=True)
                            st.rerun()
                st.divider()

    # ── تبويب ٢: موافقة مباشرة (بدون المشرف) ──
    with tab2:
        st.markdown("""
        <div class="warn-box">
            ⚡ <strong>الموافقة المباشرة:</strong> تتيح لك الموافقة على الطلبات أو رفضها مباشرةً
            دون انتظار موافقة المشرف أولاً.
        </div>""", unsafe_allow_html=True)

        pending_all = df[df["الحالة"] == "Pending"] \
                      if not df.empty else pd.DataFrame()

        st.markdown(f'<div class="info-box">📬 الطلبات المعلّقة (لم يراجعها المشرف بعد): <strong>{len(pending_all)}</strong></div>',
                    unsafe_allow_html=True)

        if pending_all.empty:
            st.markdown('<div class="success-box">✅ لا توجد طلبات معلّقة</div>',
                        unsafe_allow_html=True)
        else:
            for _, row in pending_all.iterrows():
                req_id = row.get("ID","")
                st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)
                comment = st.text_area(f"💬 تعليق #{req_id}", key=f"mc2_{req_id}",
                                       placeholder="أضف تعليقاً (اختياري)")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ موافقة مباشرة", key=f"ma2_{req_id}", type="primary"):
                        update_row(req_id, {
                            "الحالة":    "Approved by Manager",
                            "المدير":    info["name"],
                            "التعليقات": comment,
                            "Timestamp": now_str(),
                        })
                        st.markdown('<div class="success-box">✅ تمت الموافقة المباشرة</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
                with c2:
                    if st.button("❌ رفض مباشر", key=f"mr2_{req_id}"):
                        if not comment.strip():
                            st.markdown('<div class="error-box">⚠️ يرجى كتابة سبب الرفض أولاً</div>',
                                        unsafe_allow_html=True)
                        else:
                            update_row(req_id, {
                                "الحالة":    "Rejected by Manager",
                                "المدير":    info["name"],
                                "التعليقات": comment,
                                "Timestamp": now_str(),
                            })
                            st.markdown('<div class="error-box">❌ تم الرفض</div>',
                                        unsafe_allow_html=True)
                            st.rerun()
                st.divider()

    # ── تبويب ٣: كل الطلبات + تحميل ──
    with tab3:
        if df.empty:
            st.markdown('<div class="info-box">📭 لا توجد طلبات مسجلة في النظام</div>',
                        unsafe_allow_html=True)
        else:
            # إحصائيات
            total    = len(df)
            pending  = len(df[df["الحالة"] == "Pending"])
            approved = len(df[df["الحالة"].str.contains("Approved", na=False)])
            rejected = len(df[df["الحالة"].str.contains("Rejected", na=False)])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📋 إجمالي الطلبات", total)
            c2.metric("⏳ قيد الانتظار", pending)
            c3.metric("✅ معتمدة", approved)
            c4.metric("❌ مرفوضة", rejected)
            st.divider()

            show = df.copy()
            show["الحالة"] = show["الحالة"].map(lambda s: STATUS_AR.get(s, s))
            cols = ["ID","اسم المندوب","رقم السيارة","نوع السيارة",
                    "نوع الطلب","الحالة","المشرف","آخر تاريخ صيانة","Timestamp"]
            st.dataframe(show[[c for c in cols if c in show.columns]],
                         use_container_width=True)

            if os.path.exists(EXCEL_FILE):
                with open(EXCEL_FILE, "rb") as f:
                    st.download_button(
                        "📥 تحميل كل الطلبات (Excel)",
                        data=f,
                        file_name=f"الطلبات_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    logout_btn()


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────

def main():
    if not st.session_state.get("logged_in"):
        page_login()
        return

    role = st.session_state["user_info"].get("role","")

    if   role == "agent":                  page_agent()
    elif role == "supervisor":             page_supervisor()
    elif role == "maintenance_supervisor": page_maintenance_supervisor()
    elif role == "manager":                page_manager()
    else:
        st.error("⚠️ دور غير معروف، تواصل مع مسؤول النظام")
        if st.button("خروج"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
