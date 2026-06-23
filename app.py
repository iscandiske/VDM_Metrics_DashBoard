import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(
    page_title="Agency Ads Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-container { background: #f8f9fa; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .rank-top { border-left: 4px solid #28a745; padding-left: 12px; margin: 6px 0; }
    .rank-bot { border-left: 4px solid #dc3545; padding-left: 12px; margin: 6px 0; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
""", unsafe_allow_html=True)


# ── Google Sheets connection ──────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_gsheet_client():
    """Connect using service-account credentials stored in Streamlit secrets."""
    # Check secrets exist
    if "gcp_service_account" not in st.secrets:
        st.sidebar.error("❌ No [gcp_service_account] found in Secrets. Add your JSON credentials.")
        return None
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Fix the most common issue: Streamlit escapes \n in private_key as literal \\n
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        st.sidebar.success("✅ Google Sheets connected!")
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Auth error: {e}")
        return None


def load_accounts_from_sheet(sheet_url: str) -> pd.DataFrame:
    client = get_gsheet_client()
    if not client:
        return None
    try:
        sh = client.open_by_url(sheet_url)
        # Try to find the Accounts tab — show available tabs if not found
        try:
            ws = sh.worksheet("Accounts")
        except Exception:
            tabs = [w.title for w in sh.worksheets()]
            st.error(f"❌ No tab named 'Accounts' found. Your tabs are: {tabs} — rename one to 'Accounts'")
            return None
        data = ws.get_all_records()
        if not data:
            st.error("❌ The Accounts tab is empty — make sure it has headers in row 1 and data below.")
            return None
        df = pd.DataFrame(data)
        df.columns = [c.lower().strip() for c in df.columns]
        for col in ["spend","roas","cpl","leads","ctr","cpc","frequency","engagements","impressions","results","freq","cpe","reach"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        st.sidebar.success(f"✅ Loaded {len(df)} accounts from sheet!")
        return df
    except Exception as e:
        st.error(f"❌ Could not load sheet: {e}")
        return None


def save_lead_to_sheet(sheet_url: str, lead: dict):
    client = get_gsheet_client()
    if not client:
        return False
    try:
        sh = client.open_by_url(sheet_url)
        try:
            ws = sh.worksheet("Pipeline")
        except Exception:
            ws = sh.add_worksheet("Pipeline", rows=200, cols=10)
            ws.append_row(["name","contact","industry","budget","stage","notes","date_added"])
        ws.append_row([
            lead["name"], lead["contact"], lead["industry"],
            lead["budget"], lead["stage"], lead["notes"],
            datetime.now().strftime("%Y-%m-%d")
        ])
        return True
    except Exception as e:
        st.error(f"Could not save lead: {e}")
        return False


def save_account_to_sheet(sheet_url: str, account: dict):
    client = get_gsheet_client()
    if not client:
        return False
    try:
        sh = client.open_by_url(sheet_url)
        ws = sh.worksheet("Accounts")
        ws.append_row([
            account["name"], account["industry"], account["spend"],
            account["roas"], account["cpl"], account["leads"],
            account["ctr"], account["cpc"], account["frequency"],
            account["engagements"], account["impressions"], account["status"]
        ])
        return True
    except Exception as e:
        st.error(f"Could not save account: {e}")
        return False


# ── Demo data ─────────────────────────────────────────────────────────────────

DEMO_ACCOUNTS = pd.DataFrame([
    {"name":"Bella's Bakery","industry":"Food & Bev","spend":4200,"roas":5.8,"cpl":9.20,"leads":218,"ctr":3.9,"cpc":0.82,"frequency":1.8,"engagements":4200,"impressions":72000,"status":"active"},
    {"name":"FitZone Gym","industry":"Fitness","spend":6800,"roas":5.1,"cpl":11.40,"leads":182,"ctr":3.5,"cpc":1.10,"frequency":2.1,"engagements":5800,"impressions":98000,"status":"active"},
    {"name":"Luxe Dermatology","industry":"Health","spend":9200,"roas":4.7,"cpl":14.20,"leads":156,"ctr":3.1,"cpc":1.45,"frequency":2.4,"engagements":7200,"impressions":118000,"status":"active"},
    {"name":"AutoFix Centro","industry":"Auto","spend":5500,"roas":4.3,"cpl":16.80,"leads":134,"ctr":2.8,"cpc":1.62,"frequency":2.7,"engagements":3900,"impressions":88000,"status":"active"},
    {"name":"Green Leaf Spa","industry":"Beauty","spend":3900,"roas":4.0,"cpl":17.50,"leads":118,"ctr":2.6,"cpc":1.74,"frequency":3.0,"engagements":3200,"impressions":64000,"status":"active"},
    {"name":"TechRepair Pro","industry":"Tech","spend":2800,"roas":3.2,"cpl":22.10,"leads":76,"ctr":2.1,"cpc":2.21,"frequency":3.4,"engagements":2100,"impressions":52000,"status":"active"},
    {"name":"Casa Real Estate","industry":"Real Estate","spend":12000,"roas":2.8,"cpl":28.40,"leads":64,"ctr":1.8,"cpc":2.84,"frequency":3.8,"engagements":5400,"impressions":142000,"status":"active"},
    {"name":"Petshop Paradise","industry":"Pets","spend":2100,"roas":2.5,"cpl":31.00,"leads":48,"ctr":1.6,"cpc":3.10,"frequency":4.2,"engagements":1800,"impressions":48000,"status":"paused"},
    {"name":"Dental Smile","industry":"Health","spend":7400,"roas":2.2,"cpl":35.80,"leads":38,"ctr":1.4,"cpc":3.58,"frequency":4.6,"engagements":3100,"impressions":112000,"status":"active"},
    {"name":"Moda Boutique","industry":"Fashion","spend":3300,"roas":1.9,"cpl":42.50,"leads":28,"ctr":1.1,"cpc":4.25,"frequency":5.1,"engagements":1400,"impressions":68000,"status":"active"},
    {"name":"Rooftop Bar REC","industry":"Nightlife","spend":4600,"roas":1.6,"cpl":54.20,"leads":18,"ctr":0.9,"cpc":5.42,"frequency":5.8,"engagements":980,"impressions":82000,"status":"paused"},
    {"name":"City Law Firm","industry":"Legal","spend":8400,"roas":1.2,"cpl":68.00,"leads":12,"ctr":0.6,"cpc":6.80,"frequency":6.4,"engagements":620,"impressions":124000,"status":"active"},
])

DEMO_LEADS = [
    {"name":"Ocean Surf School","contact":"Rodrigo Lima","industry":"Sports","budget":2500,"stage":"prospect","notes":"Instagram DM","date_added":"2026-06-10"},
    {"name":"Viva Restaurant","contact":"Ana Torres","industry":"Restaurant","budget":4000,"stage":"proposal","notes":"Sent proposal 3 days ago","date_added":"2026-06-12"},
    {"name":"Glow Aesthetics","contact":"Fernanda Costa","industry":"Beauty","budget":6000,"stage":"signed","notes":"Starting July","date_added":"2026-06-01"},
    {"name":"ProMove Logistics","contact":"Carlos Mendes","industry":"Logistics","budget":8000,"stage":"onboarding","notes":"Setting up ad account","date_added":"2026-05-28"},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def calc_cpe(df):
    df = df.copy()
    for col in ["engagements","impressions","reach","roas","cpl","leads","ctr","cpc","frequency","results","spend"]:
        if col not in df.columns:
            df[col] = 0
    df["cpe"] = df.apply(
        lambda r: round(float(r["spend"]) / float(r["engagements"]), 2) if float(r.get("engagements", 0)) > 0 else 0, axis=1
    )
    return df

KPI_CONFIG = {
    "Spend ($)":   {"col":"spend",       "higher_better":True,  "fmt":"${}"},
    "ROAS":        {"col":"roas",        "higher_better":True,  "fmt":"{}x"},
    "CPL ($)":     {"col":"cpl",         "higher_better":False, "fmt":"${}"},
    "Results":     {"col":"results",     "higher_better":True,  "fmt":"{}"},
    "CTR (%)":     {"col":"ctr",         "higher_better":True,  "fmt":"{}%"},
    "CPE ($)":     {"col":"cpe",         "higher_better":False, "fmt":"${}"},
    "Frequency":   {"col":"frequency",   "higher_better":False, "fmt":"{}"},
    "Impressions": {"col":"impressions", "higher_better":True,  "fmt":"{}"},
}

def fmt_val(v, key):
    cfg = KPI_CONFIG.get(key, {})
    template = cfg.get("fmt", "{}")
    if "spend" in cfg.get("col","") or cfg.get("col","") in ["cpl","cpe","cpc"]:
        return f"${v:,.2f}" if isinstance(v, float) else f"${v:,}"
    if cfg.get("col") == "roas":
        return f"{v:.1f}x"
    if cfg.get("col") == "ctr":
        return f"{v:.2f}%"
    if cfg.get("col") == "frequency":
        return f"{v:.1f}"
    if cfg.get("col") == "leads":
        return f"{int(v):,}"
    return str(round(v, 2))

def color_cell(val, col, df):
    q33 = df[col].quantile(0.33)
    q66 = df[col].quantile(0.66)
    higher_better = KPI_CONFIG.get(
        next((k for k,v in KPI_CONFIG.items() if v["col"]==col), ""), {}
    ).get("higher_better", True)
    if higher_better:
        if val >= q66: return "🟢"
        if val <= q33: return "🔴"
        return "🟡"
    else:
        if val <= q33: return "🟢"
        if val >= q66: return "🔴"
        return "🟡"


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # Show service account email for easy sharing
    if "gcp_service_account" in st.secrets:
        email = st.secrets["gcp_service_account"].get("client_email", "")
        if email:
            st.markdown("**Share your sheet with:**")
            st.code(email, language="text")
            st.caption("Give it Editor access in Google Sheets → Share")
    else:
        st.warning("No credentials found in Secrets yet.")

    st.divider()

    sheet_url = st.text_input(
        "Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Paste the full URL of your Google Sheet here."
    )
    if sheet_url:
        if st.button("🔄 Sync from Sheet", use_container_width=True):
            with st.spinner("Connecting to Google Sheets..."):
                df_loaded = load_accounts_from_sheet(sheet_url)
            if df_loaded is not None:
                st.session_state["accounts"] = df_loaded
                st.session_state["sheet_url"] = sheet_url
                st.rerun()

    st.divider()
    st.markdown("**Required tab name:** `Accounts`")
    st.markdown("**Frequency guide:**")
    st.markdown("🟢 < 2.5 — Fresh\n\n🟡 2.5–5 — Watch it\n\n🔴 > 5 — Ad fatigue")

# ── Session state ─────────────────────────────────────────────────────────────

if "accounts" not in st.session_state:
    st.session_state["accounts"] = DEMO_ACCOUNTS.copy()
if "leads" not in st.session_state:
    st.session_state["leads"] = DEMO_LEADS.copy()

df = calc_cpe(st.session_state["accounts"])

# ── Header ────────────────────────────────────────────────────────────────────

st.title("📊 Agency Ads Dashboard")
st.caption("Meta Ads performance · all accounts · updated " + datetime.now().strftime("%b %d, %Y"))

tab1, tab2, tab3 = st.tabs(["Overview", "All accounts", "New clients"])


# ── TAB 1: Overview ───────────────────────────────────────────────────────────

with tab1:
    active = df[df["status"] == "active"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active accounts", len(active), f"{len(df)} total")
    c2.metric("Total spend/mo", f"${df['spend'].sum():,.0f}")
    c3.metric("Avg ROAS", f"{df['roas'].mean():.1f}x")
    c4.metric("Avg CPE", f"${df['cpe'].mean():.2f}")
    c5.metric("Avg Frequency", f"{df['frequency'].mean():.1f}")

    st.divider()

    kpi_choice = st.selectbox("Rank accounts by:", list(KPI_CONFIG.keys()), key="kpi_overview")
    cfg = KPI_CONFIG[kpi_choice]
    col = cfg["col"]
    ascending = not cfg["higher_better"]

    ranked = df.sort_values(col, ascending=ascending).reset_index(drop=True)
    top5   = ranked.head(5)
    worst5 = ranked.tail(5).iloc[::-1].reset_index(drop=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🏆 Top 5 accounts")
        for i, row in top5.iterrows():
            val = fmt_val(row[col], kpi_choice)
            st.markdown(f"""<div class='rank-top'>
                <strong>{row['name']}</strong> &nbsp;
                <span style='color:#28a745;font-weight:600'>{val}</span>
                <br><small style='color:#666'>{row['industry']} · {row['status']}</small>
            </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("#### ⚠️ Needs attention")
        for i, row in worst5.iterrows():
            val = fmt_val(row[col], kpi_choice)
            st.markdown(f"""<div class='rank-bot'>
                <strong>{row['name']}</strong> &nbsp;
                <span style='color:#dc3545;font-weight:600'>{val}</span>
                <br><small style='color:#666'>{row['industry']} · {row['status']}</small>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"#### {kpi_choice} — all accounts")
    bar_colors = ["#28a745" if i < 5 else "#dc3545" if i >= len(ranked)-5 else "#6c757d"
                  for i in range(len(ranked))]
    fig = go.Figure(go.Bar(
        x=ranked["name"], y=ranked[col],
        marker_color=bar_colors,
        hovertemplate="%{x}<br>" + kpi_choice + ": %{y:.2f}<extra></extra>"
    ))
    fig.update_layout(height=280, margin=dict(t=10,b=40,l=0,r=0), xaxis_tickangle=-35,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


# ── TAB 2: All accounts ───────────────────────────────────────────────────────

with tab2:
    col_h1, col_h2 = st.columns([3,1])
    with col_h1:
        st.markdown("#### All accounts")
    with col_h2:
        if st.button("➕ Add account", use_container_width=True):
            st.session_state["show_add_account"] = not st.session_state.get("show_add_account", False)

    if st.session_state.get("show_add_account", False):
        with st.form("add_account_form"):
            st.markdown("**New account**")
            r1a, r1b, r1c = st.columns(3)
            name        = r1a.text_input("Client name *")
            industry    = r1b.text_input("Industry")
            status      = r1c.selectbox("Status", ["active","paused","inactive"])
            r2a, r2b, r2c, r2d = st.columns(4)
            spend       = r2a.number_input("Spend/mo ($)", min_value=0.0, step=100.0)
            roas        = r2b.number_input("ROAS", min_value=0.0, step=0.1)
            cpl_v       = r2c.number_input("CPL ($)", min_value=0.0, step=0.5)
            leads_v     = r2d.number_input("Leads", min_value=0, step=1)
            r3a, r3b, r3c, r3d = st.columns(4)
            ctr_v       = r3a.number_input("CTR (%)", min_value=0.0, step=0.1)
            cpc_v       = r3b.number_input("CPC ($)", min_value=0.0, step=0.1)
            freq_v      = r3c.number_input("Frequency", min_value=0.0, step=0.1)
            eng_v       = r3d.number_input("Engagements", min_value=0, step=100)
            imp_v       = st.number_input("Impressions", min_value=0, step=1000)
            submitted   = st.form_submit_button("Save account")
            if submitted:
                if not name:
                    st.error("Client name is required.")
                else:
                    new_row = {"name":name,"industry":industry,"spend":spend,"roas":roas,"cpl":cpl_v,
                               "leads":leads_v,"ctr":ctr_v,"cpc":cpc_v,"frequency":freq_v,
                               "engagements":eng_v,"impressions":imp_v,"status":status}
                    st.session_state["accounts"] = pd.concat(
                        [st.session_state["accounts"], pd.DataFrame([new_row])], ignore_index=True)
                    if sheet_url:
                        save_account_to_sheet(sheet_url, new_row)
                    st.session_state["show_add_account"] = False
                    st.success(f"'{name}' added!")
                    st.rerun()

    fa, fb, fc = st.columns([2,1,1])
    search_q  = fa.text_input("Search", placeholder="Name or industry…", label_visibility="collapsed")
    flt_status= fb.selectbox("Status", ["All","active","paused","inactive"], label_visibility="collapsed")
    sort_by   = fc.selectbox("Sort by", list(KPI_CONFIG.keys()), label_visibility="collapsed")

    df_show = calc_cpe(st.session_state["accounts"]).copy()
    if search_q:
        df_show = df_show[df_show["name"].str.contains(search_q, case=False) |
                          df_show["industry"].str.contains(search_q, case=False)]
    if flt_status != "All":
        df_show = df_show[df_show["status"] == flt_status]

    sort_cfg = KPI_CONFIG[sort_by]
    df_show = df_show.sort_values(sort_cfg["col"], ascending=not sort_cfg["higher_better"]).reset_index(drop=True)

    def style_df(df_in):
        def color_roas(v):
            return "color: #28a745; font-weight:600" if v >= 4 else "color: #dc3545; font-weight:600" if v < 2.5 else "color: #e6a817"
        def color_freq(v):
            return "color: #28a745" if v < 2.5 else "color: #dc3545" if v > 5 else "color: #e6a817"
        def color_cpe(v):
            return "color: #28a745" if v <= 1 else "color: #dc3545" if v > 3 else "color: #e6a817"
        def color_cpl(v):
            return "color: #28a745" if v <= 15 else "color: #dc3545" if v > 35 else "color: #e6a817"
        return df_in.style \
            .applymap(color_roas, subset=["roas"]) \
            .applymap(color_freq, subset=["frequency"]) \
            .applymap(color_cpe,  subset=["cpe"]) \
            .applymap(color_cpl,  subset=["cpl"]) \
            .format({"spend":"${:,.0f}","roas":"{:.1f}x","cpl":"${:.2f}","ctr":"{:.2f}%",
                     "cpc":"${:.2f}","frequency":"{:.1f}","cpe":"${:.2f}",
                     "leads":"{:,.0f}","engagements":"{:,.0f}","impressions":"{:,.0f}"})

    display_cols = ["name","industry","status","spend","roas","cpl","leads","ctr","cpc","frequency","engagements","cpe","impressions"]
    existing_cols = [c for c in display_cols if c in df_show.columns]
    st.dataframe(style_df(df_show[existing_cols]), use_container_width=True, height=400)
    st.caption(f"Showing {len(df_show)} of {len(st.session_state['accounts'])} accounts")


# ── TAB 3: New clients / pipeline ─────────────────────────────────────────────

with tab3:
    col_h3, col_h4 = st.columns([3,1])
    with col_h3:
        st.markdown("#### New client pipeline")
    with col_h4:
        if st.button("➕ Add deal", use_container_width=True):
            st.session_state["show_add_lead"] = not st.session_state.get("show_add_lead", False)

    if st.session_state.get("show_add_lead", False):
        with st.form("add_lead_form"):
            st.markdown("**New deal**")
            la, lb = st.columns(2)
            l_name    = la.text_input("Business name *")
            l_contact = lb.text_input("Contact person")
            lc, ld = st.columns(2)
            l_industry= lc.text_input("Industry")
            l_budget  = ld.number_input("Est. monthly budget ($)", min_value=0, step=500)
            le, lf = st.columns(2)
            l_stage   = le.selectbox("Stage", ["prospect","proposal","signed","onboarding"])
            l_notes   = lf.text_input("Notes")
            l_submit  = st.form_submit_button("Save deal")
            if l_submit:
                if not l_name:
                    st.error("Business name is required.")
                else:
                    new_lead = {"name":l_name,"contact":l_contact,"industry":l_industry,
                                "budget":l_budget,"stage":l_stage,"notes":l_notes,
                                "date_added":datetime.now().strftime("%Y-%m-%d")}
                    st.session_state["leads"].append(new_lead)
                    if sheet_url:
                        save_lead_to_sheet(sheet_url, new_lead)
                    st.session_state["show_add_lead"] = False
                    st.success(f"'{l_name}' added to pipeline!")
                    st.rerun()

    leads_list = st.session_state["leads"]
    stage_counts = {s: sum(1 for l in leads_list if l["stage"]==s)
                    for s in ["prospect","proposal","signed","onboarding"]}
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Prospects", stage_counts["prospect"])
    m2.metric("Proposals out", stage_counts["proposal"])
    m3.metric("Signed", stage_counts["signed"])
    m4.metric("Onboarding", stage_counts["onboarding"])

    stage_order = {"onboarding":0,"signed":1,"proposal":2,"prospect":3}
    stage_labels = {"prospect":"🔵 Prospect","proposal":"🟡 Proposal sent",
                    "signed":"🟢 Signed","onboarding":"🟣 Onboarding"}
    sorted_leads = sorted(leads_list, key=lambda l: stage_order.get(l["stage"], 9))

    if not sorted_leads:
        st.info("No deals yet — add your first one above.")
    else:
        for lead in sorted_leads:
            with st.container():
                ca, cb, cc = st.columns([3,1,1])
                ca.markdown(f"**{lead['name']}**  \n{lead.get('contact','')} · {lead.get('industry','')}  \n{lead.get('notes','')}")
                cb.markdown(f"**${lead.get('budget',0):,}/mo**  \n{lead.get('date_added','')}")
                cc.markdown(stage_labels.get(lead["stage"], lead["stage"]))
                st.divider()
