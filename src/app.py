import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
import re

from iol_client import IOLClient
from market_data import MarketData
from portfolio_manager import PortfolioManager
from auth_manager import AuthManager

# Load environment
load_dotenv()

# Page Config MUST be the first Streamlit command
st.set_page_config(page_title="Investment Assistant", layout="wide", page_icon="💰")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Clean header */
    .stApp header {
        background-color: transparent;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    
    /* Hero metric container */
    .hero-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .hero-metric h1 {
        font-size: 2.5rem;
        margin: 0;
    }
    .hero-metric p {
        font-size: 1rem;
        opacity: 0.8;
        margin: 0;
    }
    
    /* Gain/Loss badges */
    .gain-positive {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .gain-negative {
        background-color: #ef4444;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    
    /* Reduce sidebar width */
    [data-testid="stSidebar"] {
        min-width: 200px;
        max-width: 260px;
    }
    
    /* Cards for sections */
    .section-card {
        background: #f8f9fa;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .section-card {
            background: #1e1e2e;
        }
    }
    
    /* AI Response Container */
    .ai-response {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .ai-response h1, .ai-response h2, .ai-response h3 {
        color: #1e293b;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .ai-response h1 { font-size: 1.5rem; }
    .ai-response h2 { font-size: 1.25rem; }
    .ai-response h3 { font-size: 1.1rem; }
    .ai-response ul, .ai-response ol {
        margin-left: 1.5rem;
    }
    .ai-response li {
        margin-bottom: 0.5rem;
    }
    @media (prefers-color-scheme: dark) {
        .ai-response {
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border-color: #334155;
        }
        .ai-response h1, .ai-response h2, .ai-response h3 {
            color: #e2e8f0;
        }
    }
    
    /* History card */
    .history-card {
        border-left: 3px solid #667eea;
        padding-left: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def clean_ai_response(text):
    """Cleans AI response for better display in Streamlit."""
    text = re.sub(r'\$(\d[\d,\.]*[kKmM]?)\$', r'$\1', text) 
    text = re.sub(r'\$([A-Z]{2,})\$', r'\1', text) 
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def run_app(username, full_name, gemini_key, iol_user, iol_pass):
    st.title(f"💰 Personal Investment Assistant")
    st.caption(f"Logged in as: {full_name}")

    # Initialize Classes
    market = MarketData()
    pm = PortfolioManager()
    
    st.sidebar.header("Settings")
    use_simulation = st.sidebar.toggle("🧪 Simulation Mode", value=(not iol_user))
    
    # --- TABS LAYOUT ---
    tab_dashboard, tab_analyst = st.tabs(["📊 Dashboard", "🤖 AI Strategist"])

    # ============================
    # TAB 1: DASHBOARD
    # ============================
    with tab_dashboard:
        portfolio_data = [] 

        if use_simulation:
            st.caption("🧪 Running in Simulation Mode")
            portfolio_data = [
                {"Symbol": "SPY.BA", "Description": "S&P 500 ETF CEDEAR", "Quantity": 10, "Last Price": 52250.0, "Total Value": 522500.0, "Daily Var %": 0.5},
                {"Symbol": "GGAL.BA", "Description": "Grupo Financiero Galicia", "Quantity": 100, "Last Price": 8125.0, "Total Value": 812500.0, "Daily Var %": -1.2},
                {"Symbol": "MELI.BA", "Description": "MercadoLibre CEDEAR", "Quantity": 5, "Last Price": 26700.0, "Total Value": 133500.0, "Daily Var %": 2.1},
            ]
        else:
            try:
                # Use passed credentials
                iol = IOLClient(iol_user, iol_pass)
                iol.authenticate()
                raw_portfolio = iol.get_portfolio()
                
                if raw_portfolio and 'activos' in raw_portfolio:
                     for asset in raw_portfolio['activos']:
                         symbol = asset.get('titulo', {}).get('simbolo', 'N/A')
                         desc = asset.get('titulo', {}).get('descripcion', '')
                         qty = asset.get('cantidad', 0)
                         last_price = asset.get('ultimoPrecio', 0.0)
                         total_val = asset.get('valorizado', 0.0)
                         daily_var = asset.get('variacionDiaria', 0.0)
                         
                         portfolio_data.append({
                             "Symbol": symbol,
                             "Description": desc,
                             "Quantity": qty,
                             "Last Price": last_price,
                             "Total Value": total_val,
                             "Daily Var %": daily_var
                         })
            except Exception as e:
                st.error(f"Failed to connect to IOL: {e}")
                # Fallback to empty if error?
        
        # --- Display ---
        if portfolio_data:
            df_portfolio = pd.DataFrame(portfolio_data)
            total_value = df_portfolio["Total Value"].sum()
            
            # Save Snapshot (Multi-tenancy: Pass user_id)
            pm.save_daily_snapshot(total_value, portfolio_data, user_id=username)
            
            # Historical Gains (Multi-tenancy: Pass user_id)
            gains = pm.calculate_gains(total_value, user_id=username)
            portfolio_data_enriched = pm.calculate_asset_gains(portfolio_data, user_id=username)
            df_portfolio = pd.DataFrame(portfolio_data_enriched)
            
            # === HERO METRIC ===
            st.markdown(f"""
            <div class="hero-metric">
                <p>Total Portfolio Value</p>
                <h1>${total_value:,.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
            
            # === RETURN METRICS ===
            col_d, col_w, col_m = st.columns(3)
            
            if 'daily' in gains:
                col_d.metric("Daily", f"${gains['daily'][0]:,.0f}", f"{gains['daily'][1]:.2f}%")
            else:
                col_d.metric("Daily", "–", "0.0%")
                
            if 'weekly' in gains:
                col_w.metric("Weekly", f"${gains['weekly'][0]:,.0f}", f"{gains['weekly'][1]:.2f}%")
            else:
                col_w.metric("Weekly", "–", "0.0%")
                
            if 'monthly' in gains:
                col_m.metric("Monthly", f"${gains['monthly'][0]:,.0f}", f"{gains['monthly'][1]:.2f}%")
            else:
                col_m.metric("Monthly", "–", "0.0%")

            st.divider()
            
            # === CHARTS ===
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.caption("📈 Performance History (90 days)")
                history_df = pm.get_history(days=90, user_id=username)
                if not history_df.empty:
                    fig_hist = px.area(history_df, x='date', y='total_value', color_discrete_sequence=["#667eea"])
                    fig_hist.update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=10, b=0), height=250)
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No history yet.")
            
            with col_chart2:
                st.caption("🥧 Asset Allocation")
                fig_alloc = px.pie(df_portfolio, values='Total Value', names='Symbol', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_alloc.update_layout(showlegend=True, margin=dict(l=0, r=0, t=10, b=0), height=250)
                fig_alloc.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig_alloc, use_container_width=True)

            st.divider()
            
            # === HOLDINGS TABLE ===
            st.subheader("📋 Current Holdings")
            cols_holdings = ["Symbol", "Description", "Quantity", "Last Price", "Total Value", "Daily Var %"]
            available_cols_h = [c for c in cols_holdings if c in df_portfolio.columns]
            
            st.dataframe(
                df_portfolio[available_cols_h],
                column_config={
                    "Last Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Total Value": st.column_config.NumberColumn(format="$%.2f"),
                    "Daily Var %": st.column_config.NumberColumn(format="%.2f%%"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # === GAINS TABLE ===
            with st.expander("📊 Performance & Gains by Asset"):
                cols_gains = ["Symbol", "Daily Gain", "Weekly Gain", "Monthly Gain"]
                available_cols_g = [c for c in cols_gains if c in df_portfolio.columns]
                
                if len(available_cols_g) > 1:
                    st.dataframe(
                        df_portfolio[available_cols_g],
                        column_config={
                            "Daily Gain": st.column_config.NumberColumn(format="$%.2f"),
                            "Weekly Gain": st.column_config.NumberColumn(format="$%.2f"),
                            "Monthly Gain": st.column_config.NumberColumn(format="$%.2f"),
                        },
                        hide_index=True,
                        use_container_width=True
                    )

        else:
            st.warning("No assets found.")

    # ============================
    # TAB 2: AI STRATEGIST
    # ============================
    with tab_analyst:
        st.subheader("🤖 AI Financial Advisor")
        
        selected_model = None
        reasoning_mode = True
        
        if gemini_key:
            from ai_analyst import AIAnalyst
            analyst = AIAnalyst(gemini_key)
            
            col_cfg1, col_cfg2 = st.columns([1, 1])
            with col_cfg1:
                reasoning_mode = st.toggle("🧠 Enable Reasoning", value=True)
            with col_cfg2:
                available_models = analyst.list_models()
                # ... same model filtering logic ...
                if reasoning_mode:
                    filtered = [m for m in available_models if "thinking" in m or "gemini-3" in m]
                    if not filtered: filtered = [m for m in available_models if "pro" in m]
                else:
                    filtered = [m for m in available_models if "flash" in m and "thinking" not in m]
                    if not filtered: filtered = available_models
                
                if filtered:
                    selected_model = st.selectbox("Model", filtered, index=0, label_visibility="collapsed")

            st.divider()

            # ... Risk Profile Logic ...
            st.caption("📊 Selecciona tu perfil de riesgo:")
            risk_profiles = {
                "🛡️ Conservador": {"label": "Conservador", "prompt_modifier": "Conservador - Prioriza preservación..."},
                "🔵 Moderado-Bajo": {"label": "Moderado-Bajo", "prompt_modifier": "Moderado-Bajo..."},
                "⚖️ Moderado": {"label": "Moderado", "prompt_modifier": "Moderado..."},
                "🔶 Moderado-Alto": {"label": "Moderado-Alto", "prompt_modifier": "Moderado-Alto..."},
                "🔥 Agresivo": {"label": "Agresivo", "prompt_modifier": "Agresivo..."}
            }
            selected_profile = st.radio("Perfil", list(risk_profiles.keys()), index=2, horizontal=True, label_visibility="collapsed")
            
            st.divider()
            investment_amount = st.number_input("💵 Amount to Invest (ARS)", min_value=0.0, value=100000.0, step=10000.0)
            
            default_prompt = analyst.default_prompt

            with st.expander("⚙️ Customize Instructions", expanded=False):
                custom_prompt = st.text_area("Instructions:", value=default_prompt, height=200)

            use_grounding = st.toggle("🌐 Enable Internet Search", value=True)

            if st.button("🚀 Generate Investment Analysis", type="primary", use_container_width=True):
                 with st.spinner(f"Analyzing with {selected_model}..."):
                    market_context = market.get_global_context()
                    news = market.get_market_news()
                    portfolio_val = sum(item.get('Total Value', 0) for item in portfolio_data)
                    
                    risk_modifier = risk_profiles[selected_profile].get('prompt_modifier', '')
                    final_prompt = f"**PERFIL DE RIESGO:** {risk_modifier}\n\n{custom_prompt}"
                    
                    analysis_text, used_model = analyst.analyze_portfolio(
                        portfolio_data, investment_amount, market_context, news_headlines=news,
                        model_name=selected_model, reasoning_enabled=reasoning_mode,
                        prompt_template=final_prompt, use_grounding=use_grounding
                    )
                    
                    if "models/" in used_model: used_model = used_model.replace("models/", "")
                    cleaned_text = clean_ai_response(analysis_text)
                    
                    # SAVE ANALYSIS with user_id!
                    pm.save_analysis(used_model, investment_amount, portfolio_val, cleaned_text, user_id=username)
                    
                    st.success(f"Generated with {used_model}")
                    st.markdown(f'<div class="ai-response">{cleaned_text}</div>', unsafe_allow_html=True)
        else:
            st.warning("Needs API Key")

        # --- HISTORY ---
        st.divider()
        with st.expander("📚 Previous Analyses"):
            # Get history for user
            history_df = pm.get_analyses(limit=5, user_id=username)
            if history_df.empty:
                st.info("No analyses yet.")
            else:
                for _, row in history_df.iterrows():
                     with st.container():
                        st.caption(f"📅 {row['timestamp']} | 🤖 {row['model']} | 💵 ${row['investment_amount']:,.0f}")
                        preview = row['response'][:200] + "..."
                        st.markdown(f'<div class="history-card">{preview}</div>', unsafe_allow_html=True)
                        if st.button("View Full", key=f"v_{row['id']}"):
                            st.markdown(row['response'])
                        st.divider()


def main():
    # Authentication
    auth_manager = AuthManager()
    authenticator = auth_manager.get_authenticator()

    try:
        authenticator.login()
    except Exception as e:
        st.error(f"Error loading login: {e}")

    if st.session_state["authentication_status"]:
        username = st.session_state["username"]
        name = st.session_state["name"]
        
        # Logout & Settings Sidebar
        with st.sidebar:
            st.write(f"👤 **{name}**")
            authenticator.logout('Logout', 'main')
            
            with st.expander("🔐 API Credentials"):
                # Load current keys
                keys = auth_manager.get_user_keys(username)
                
                new_gemini = st.text_input("Gemini API Key", value=keys.get("gemini") or "", type="password")
                new_iol_u = st.text_input("IOL Username", value=keys.get("iol_user") or "", type="password")
                new_iol_p = st.text_input("IOL Password", value=keys.get("iol_pass") or "", type="password")
                
                if st.button("Save Credentials"):
                    auth_manager.update_user_keys(username, new_gemini, new_iol_u, new_iol_p)
                    st.success("Saved!")
                    st.rerun()

        # Get credentials for the session
        keys = auth_manager.get_user_keys(username)
        gemini_key = keys.get("gemini") or os.getenv("GEMINI_API_KEY") # Fallback to global if using admin
        iol_u = keys.get("iol_user")
        iol_p = keys.get("iol_pass")
        
        # If user is admin and no personal keys, fallback to env
        if username == "admin":
             if not iol_u: iol_u = os.getenv("IOL_USERNAME")
             if not iol_p: iol_p = os.getenv("IOL_PASSWORD")

        run_app(username, name, gemini_key, iol_u, iol_p)

    elif st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.info("Please login to continue.")
        
        # Registration Section
        st.divider()
        with st.expander("📝 Create New Account", expanded=False):
            st.subheader("Register")
            
            with st.form("registration_form"):
                new_username = st.text_input("Username*", placeholder="username")
                new_name = st.text_input("Full Name*", placeholder="John Doe")
                new_email = st.text_input("Email*", placeholder="user@example.com")
                new_password = st.text_input("Password*", type="password", placeholder="Enter a secure password")
                new_password_confirm = st.text_input("Confirm Password*", type="password", placeholder="Re-enter password")
                
                submit_button = st.form_submit_button("Create Account", type="primary")
                
                if submit_button:
                    # Validation
                    if not all([new_username, new_name, new_email, new_password, new_password_confirm]):
                        st.error("All fields are required")
                    elif new_password != new_password_confirm:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        # Try to register
                        success, message = auth_manager.register_user(
                            new_username, new_name, new_email, new_password
                        )
                        
                        if success:
                            st.success(f"✅ {message}! You can now log in.")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")

if __name__ == "__main__":
    main()
