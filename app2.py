import streamlit as st
import pandas as pd
import datetime
from groq import Groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt


# Connect to Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["service_account"], scope)
client_gs = gspread.authorize(creds)

sheet = client_gs.open("mindcare_users").sheet1

# ---- ✅ ADD THE TWO FUNCTIONS HERE ----

def register_user(username, email, password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    existing_users = sheet.col_values(1)
    if username in existing_users:
        return False, "Username already exists."
    sheet.append_row([username, email, password_hash])
    return True, "Account created successfully!"

def login_user(username, password):
    users = sheet.get_all_records()
    for user in users:
        if user["username"] == username:
            if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                return True
    return False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

auth_choice = st.sidebar.selectbox("Account", ["Login", "Sign Up"])

if not st.session_state.logged_in:
    if auth_choice == "Login":
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid username or password")

    elif auth_choice == "Sign Up":
        st.title("Create Account")
        username = st.text_input("Create Username")
        email = st.text_input("Email")
        password = st.text_input("Create Password", type="password")
        if st.button("Sign Up"):
            ok, msg = register_user(username, email, password)
            if ok:
                st.success(msg)
                st.info("Now go to Login")
            else:
                st.error(msg)

    st.stop()

with st.sidebar:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


# ---------- LOAD API KEY ----------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """
You are a gentle, warm mental health support companion.
Your goal is to:
• Comfort the user
• Help them express feelings safely
• Suggest healthy coping strategies
• Support emotional well-being

Do NOT interrogate the user. Do NOT ask too many questions.
Speak in short, soft, supportive responses.

NEVER attempt to diagnose mental illness or mention clinical terms.
You are NOT a doctor.

If the user talks about:
• Stress
• Anxiety
• Sadness
• Overthinking
• Depression feelings
• Self-esteem issues
• Relationships
• Loneliness
• Motivation
• Joy
• Passion
• Goodness
• Kindness
• Love

→ Respond with emotional support, empathy, grounding advice, and reassurance.

If the user asks anything NOT related to emotional or mental well-being
(e.g., programming, homework, sex tips, medical advice, politics, finance, math):

→ Respond with:
"I'm here only to support emotional and mental well-being. If you want to share how you're feeling, I'm here with you. 💛"
"""

MODEL_NAME = "llama-3.1-8b-instant"


# ---------- MEMORY ----------
def update_memory(history, current_memory):
    if len(history) < 6 or len(history) % 4 != 0:
        return current_memory

    recent = history[-6:]
    convo_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent])

    summary_prompt = f"""
Summarize emotional tone only. Keep gentle and short.

Current memory:
{current_memory}

Conversation:
{convo_text}
"""

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    return completion.choices[0].message.content.strip()


# ---------- UI CONFIG ----------
st.set_page_config(
    page_title="MindCare Companion",
    page_icon="💛",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- SIDEBAR TOGGLE ---
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = True   # True = Expanded, False = Collapsed

# Toggle button (three dots icon)
toggle = st.button("☰", help="Toggle Menu")

if toggle:
    st.session_state.sidebar_state = not st.session_state.sidebar_state

# Apply CSS based on state
if st.session_state.sidebar_state:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {transform: translateX(0); transition: all 0.3s;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {transform: translateX(-350px); transition: all 0.3s;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
button[title="Toggle Menu"] {
    font-size: 28px !important;      /* Bigger hamburger */
    font-weight: 700 !important;
    padding: 10px 18px !important;   /* Comfortable click size */
    border-radius: 10px !important;
    background: rgba(255, 255, 255, 0.85) !important;
    border: 1.5px solid #d4bfff !important;
    cursor: pointer;
    position: fixed;                 /* So it stays visible */
    top: 12px;
    left: 12px;
    z-index: 9999;
}

/* Hover effect */
button[title="Toggle Menu"]:hover {
    background: #f0e5ff !important;
    border-color: #b388ff !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
body {background: linear-gradient(135deg, #d6dce8, #f4e7f7);}
#MainMenu, footer, header {visibility: hidden;}
.big-title {text-align: center; font-size: 38px; font-weight: 900; color: #3b2b56;}
.sub-title {text-align: center; color: #6a5b7e; font-size: 18px;}
.glass-card {background: rgba(255,255,255,0.35); backdrop-filter: blur(12px); border-radius: 16px; padding: 25px; margin-top: 10px; box-shadow: 0 4px 28px rgba(0,0,0,0.08);}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='big-title'>💛 MindCare Companion</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Here to support you gently, one conversation at a time.</p>", unsafe_allow_html=True)


# ---------- SESSION ----------
if "memory" not in st.session_state:
    st.session_state.memory = "The user may be sharing emotional thoughts."

if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "assistant", "content": "Hey, I'm here with you. What’s on your mind?"}
    ]


# ---------- SIDEBAR NAVIGATION ----------
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigate", ["💬 Chat", "📝 Mood Journal", "📊 Dashboard", "🧘 Coping Tools"])


# =========================================================
#                         CHAT
# =========================================================
if page == "💬 Chat":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Talk to me")

    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Share whatever you're feeling...")

    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.memory = update_memory(st.session_state.history, st.session_state.memory)

        # Topic Check

        # Topic Check (Improved)
        check_prompt = f"""
Classify the topic of this message:

"{user_input}"

If the message expresses or discusses:
• feelings
• emotions
• mood
• joy
• sadness
• anxiety
• stress
• motivation
• love
• loneliness
• self-worth
• relationships
• personal reflection
• mental state

→ Reply: MENTAL

If the message is about:
• programming
• math/homework
• politics/news
• finance
• medical or health diagnosis
• sexual instructions
• technical knowledge questions

→ Reply: OTHER

Return only one word: MENTAL or OTHER.
"""

        
        check = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": check_prompt}]
        ).choices[0].message.content.strip()

        if check != "MENTAL":
            reply = "I'm here only to help with emotional and mental well-being. If you want to share your feelings, I'm here with you. 💛"
        else:
            prompt = f"""
{SYSTEM_PROMPT}

Memory:
{st.session_state.memory}

User: {user_input}
Assistant:
"""
            reply = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content.strip()

        st.session_state.history.append({"role": "assistant", "content": reply})

        with st.chat_message("assistant"):
            st.write(reply)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#                     MOOD JOURNAL
# =========================================================
elif page == "📝 Mood Journal":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("How are you feeling today?")

    moods = {"😄 Very Good": 5, "🙂 Good": 4, "😐 Okay": 3, "☹️ Bad": 2, "😢 Very Bad": 1}
    mood = st.selectbox("Select mood:", list(moods.keys()))
    note = st.text_area("Anything you want to express? (optional)")

    if st.button("Save"):
        entry = {"date": datetime.date.today().isoformat(), "mood": moods[mood], "note": note}
        try:
            df = pd.read_csv("journal.csv")
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        except:
            df = pd.DataFrame([entry])
        df.to_csv("journal.csv", index=False)
        st.success("Saved 💛")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#                     DASHBOARD
# =========================================================
elif page == "📊 Dashboard":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Your Mood Trend")

    try:
        df = pd.read_csv("journal.csv")
        df = df.set_index("date")
        st.line_chart(df["mood"])
        st.write(df)
    except:
        st.info("No entries yet. Add some from Mood Journal.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#                     COPING TOOLS
# =========================================================
elif page == "🧘 Coping Tools":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Grounding Exercises")

    st.write("### 4-6 Breathing")
    st.write("Inhale 4 seconds, exhale 6 seconds. Slow. Calm.")

    st.write("---")
    st.write("### 5-4-3-2-1 Grounding")
    st.write("""
5 things you can see  
4 things you can touch  
3 things you can hear  
2 things you can smell  
1 thing you feel inside  
""")
    st.markdown("</div>", unsafe_allow_html=True)
