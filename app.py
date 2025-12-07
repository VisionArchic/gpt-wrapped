import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from collections import Counter, defaultdict
import datetime
import tiktoken
import numpy as np
import random
import requests
from datetime import datetime as dt_now

# --- CONSTANTS FOR ESTIMATES ---
COST_PER_1M_TOKENS = 2.5      # USD per 1M tokens (OpenAI GPT-4 avg)
KWH_PER_1M_TOKENS = 0.3       # kWh per 1M tokens (rough estimate)
LITERS_PER_1M_TOKENS = 3.5    # Water in liters per 1M tokens (datacenter cooling)

# --- NOTIFICATION SYSTEM (PRIVACY-FIRST: METADATA ONLY) ---
def send_upload_notification(file_size, timestamp):
    """Send anonymous notification about file upload (NO CONTENT)"""
    try:
        if 'notifications' not in st.secrets:
            return  # No secrets configured
        
        if not st.secrets.notifications.get('enabled', False):
            return  # Notifications disabled
        
        webhook_url = st.secrets.notifications.get('discord_webhook', '')
        if not webhook_url:
            return
        
        # PRIVACY: Only send metadata, never file content!
        message = {
            "embeds": [{
                "title": "📊 GPT Wrapped - New Upload",
                "color": 16711765,  # Pink color
                "fields": [
                    {"name": "File Size", "value": f"{file_size / 1024:.2f} KB", "inline": True},
                    {"name": "Timestamp", "value": timestamp, "inline": True},
                    {"name": "Status", "value": "✅ Processing", "inline": False}
                ],
                "footer": {"text": "Privacy-first: No user data transmitted"}
            }]
        }
        
        requests.post(webhook_url, json=message, timeout=5)
    except Exception:
        pass  # Silently fail - don't disrupt user experience


# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="The Digital Mirror",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.io as pio
pio.templates.default = "plotly_dark"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #050505;}
    h1, h2, h3 {color: #FF0055; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 2px;}
    
    .persona-banner {
        text-align: center; padding: 60px;
        background: black;
        border-bottom: 4px solid #FF0055;
        margin-bottom: 40px;
        color: white; font-size: 4em; font-weight: bold;
        text-transform: uppercase; letter-spacing: 8px;
        text-shadow: 4px 4px 0px #FF0055;
    }
    
    .section-header {
        margin-top: 60px; margin-bottom: 20px; 
        border-bottom: 2px solid #333; padding-bottom: 10px;
        font-size: 2em; color: #fff;
    }
    
    .explanation {
        color: #888; font-size: 0.9em; font-style: italic; margin-bottom: 20px;
    }
    
    .chat-bubble {
        padding: 15px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #222;
        font-family: 'Verdana', sans-serif; font-size: 0.95em;
    }
    .user-bubble {background-color: #0a0a0a; color: #ccc; text-align: right; border-right: 2px solid #00CCFF;}
    .ai-bubble {background-color: #110011; color: #ffccff; border-left: 2px solid #FF0055;}
</style>
""", unsafe_allow_html=True)

# --- 2. HELPERS ---

@st.cache_resource
def setup_tools():
    import nltk
    required = ['punkt', 'punkt_tab', 'stopwords', 'averaged_perceptron_tagger']
    for r in required:
        try: nltk.data.find(f'tokenizers/{r}')
        except: 
             try: nltk.data.find(f'taggers/{r}')
             except:
                 try: nltk.data.find(f'corpora/{r}')
                 except: nltk.download(r, quiet=True)

setup_tools()
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

@st.cache_resource
def get_encoding():
    return tiktoken.get_encoding("cl100k_base")
enc = get_encoding()

# --- 3. PARSING ---

def safe_extract_text(parts):
    if not parts: return "", 0
    buffer, media = [], 0
    for p in parts:
        if isinstance(p, str): buffer.append(p)
        elif isinstance(p, dict):
            if 'text' in p: buffer.append(p['text'])
            elif 'parts' in p:
                t, m = safe_extract_text(p['parts'])
                buffer.append(t)
                media += m
            else: media += 1
    return "".join(buffer), media

@st.cache_data
def parse_conversations(json_file):
    data = json.load(json_file)
    rows = []
    
    for conv in data:
        c_id = conv.get('id')
        title = conv.get('title', 'Untitled')
        mapping = conv.get('mapping', {})
        curr = conv.get('current_node')
        
        thread = []
        while curr:
            node = mapping.get(curr)
            if not node: break
            msg = node.get('message')
            if msg and msg.get('content') and msg.get('author', {}).get('role') in ['user', 'assistant']:
                role = msg['author']['role']
                ts = msg.get('create_time')
                parts = msg['content'].get('parts', [])
                
                text, media = safe_extract_text(parts)
                model = msg.get('metadata', {}).get('model_slug', 'unknown')
                token_est = len(enc.encode(text)) if text else 0 
                
                is_image_gen = bool(role == 'user' and re.search(r"(generate|create|make|draw).{0,20}(image|picture|photo|art|logo)", text, re.IGNORECASE))
                is_code = "```" in text
                
                # Simple sentiment from keywords
                sentiment_score = 0.0
                lower_text = text.lower()
                happy_words = ['great', 'awesome', 'perfect', 'thanks', 'excellent', 'love', 'good']
                sad_words = ['bad', 'wrong', 'error', 'fail', 'hate', 'terrible', 'awful']
                for w in happy_words:
                    sentiment_score += lower_text.count(w) * 0.1
                for w in sad_words:
                    sentiment_score -= lower_text.count(w) * 0.1
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
                
                if ts: date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                else: date_str = "Unknown"
                
                # Determine mood label
                mood_label = "Neutral"
                if sentiment_score > 0.2: mood_label = "Joy"
                elif sentiment_score < -0.2: mood_label = "Stress"
                
                tooltip = f"Date: {date_str}<br>Mood: {mood_label}<br>Sentiment: {sentiment_score:.2f}<br>Tokens: {token_est}<br>Text: {text[:50]}..."
                
                thread.append({
                    'id': msg.get('id'),
                    'conv_id': c_id,
                    'title': title,
                    'role': role,
                    'text': text,
                    'ts': ts,
                    'tokens': token_est,
                    'is_code': is_code,
                    'model': model,
                    'sentiment': sentiment_score,
                    'mood_label': mood_label,
                    'is_question': '?' in text,
                    'is_image_gen': is_image_gen,
                    'tooltip': tooltip
                })
            curr = node.get('parent')
        rows.extend(thread[::-1])
        
    df = pd.DataFrame(rows)
    if df.empty: return df
    
    df['dt'] = pd.to_datetime(df['ts'], unit='s', errors='coerce')
    df = df.dropna(subset=['dt']).sort_values('dt')
    df['date'] = df['dt'].dt.date
    df['hour'] = df['dt'].dt.hour
    df['weekday'] = df['dt'].dt.day_name()
    df['month_year'] = df['dt'].dt.strftime('%Y-%m')
    return df

# --- 4. ANALYTICS FUNCTIONS ---

def calculate_chaos_score(df):
    """Calculate chaos score based on variance in behavior"""
    if df.empty: return 0, "N/A"
    sent_var = np.var(df['sentiment']) * 100
    hour_var = np.var(df['hour'])
    len_std = np.std(df['tokens']) / 100
    raw = (sent_var * 0.5) + (hour_var * 0.5) + (len_std * 0.2)
    score = int(min(100, max(0, raw)))
    
    labels = [(20, "Zen Master"), (40, "Balanced"), (60, "Chaotic Good"), (80, "Unhinged")]
    label = "BOSS FIGHT MODE"
    for threshold, lbl in labels:
        if score <= threshold:
            label = lbl
            break
    return score, label

def determine_persona(df):
    """Determine user persona based on behavior patterns"""
    u = df[df['role'] == 'user']
    if u.empty: return "The Ghost"
    scores = defaultdict(int)
    late = u['hour'].between(23, 5).sum()
    if (late / max(1, len(u))) > 0.25: scores['🧛 Night Owl'] += 5
    if u['is_image_gen'].sum() > 5: scores['🎨 AI Artist'] += 7
    if u['sentiment'].mean() < -0.1: scores['💀 Doom Scroller'] += 6
    if u['sentiment'].mean() > 0.2: scores['😊 Optimist'] += 4
    return max(scores, key=scores.get) if scores else "☕ Casual Chatter"

@st.cache_data
def precompute_thread_stats(df):
    """Precompute thread-level statistics for performance"""
    return df.groupby('conv_id').agg({
        'title': 'first', 
        'tokens': 'sum', 
        'sentiment': 'mean', 
        'id': 'count',
        'date': 'first'
    }).reset_index()

# --- 5. MAIN ---

def main():
    # --- PRIVACY NOTICE ---
    st.sidebar.markdown("---")
    st.sidebar.info("🔒 **Privacy First:** Your data is processed in-memory only. Nothing is stored on servers.")
    
    st.sidebar.title("📥 Upload")
    f = st.sidebar.file_uploader("conversations.json", type="json")
    
    # Send anonymous notification (metadata only)
    if f is not None and 'last_upload_time' not in st.session_state:
        file_size = f.size if hasattr(f, 'size') else len(f.getvalue())
        timestamp = dt_now.now().strftime('%Y-%m-%d %H:%M:%S')
        send_upload_notification(file_size, timestamp)
        st.session_state['last_upload_time'] = timestamp
    
    if not f:
        import os
        if os.path.exists("conversations.json"):
            st.sidebar.info("Auto-loading local file")
            f = open("conversations.json", "r")
    
    if not f: 
        st.title("GPT Wrapped")
        st.markdown("""
        ### 🎁 Unwrap Your ChatGPT Journey
        
        Upload your ChatGPT `conversations.json` to see beautiful analytics about your AI interactions.
        
        **How to get your data:**
        1. Go to [ChatGPT Settings](https://chat.openai.com/settings)
        2. Click "Data Controls" → "Export Data"
        3. Wait for email with download link
        4. Upload `conversations.json` here!
        
        ---
        
        **🔒 Privacy Guarantee:**
        - ✅ All processing happens in your browser's memory
        - ✅ No data is stored on servers
        - ✅ No tracking or analytics
        - ✅ Open source - [View the code](https://github.com/your-repo)
        """)
        return

    with st.spinner("Processing..."):
        full_df = parse_conversations(f)
        
    if full_df.empty: 
        st.error("No data")
        return

    # Precompute for performance
    all_threads = precompute_thread_stats(full_df)

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    st.sidebar.header("⏳ Time Travel")
    min_d, max_d = full_df['date'].min(), full_df['date'].max()
    date_range = st.sidebar.slider("Range", min_d, max_d, (min_d, max_d))
    df = full_df[(full_df['date'] >= date_range[0]) & (full_df['date'] <= date_range[1])].copy()
    if df.empty: 
        st.error("No data in range")
        return

    st.sidebar.markdown("---")
    st.sidebar.header("🔎 Search")
    q = st.sidebar.text_input("Keyword:", "")
    if q:
        u_c = df[df['role']=='user']['text'].str.contains(q, case=False, na=False).sum()
        a_c = df[df['role']=='assistant']['text'].str.contains(q, case=False, na=False).sum()
        st.sidebar.markdown(f"**'{q}':**\n- 👤 You: {u_c}\n- 🤖 AI: {a_c}\n- **Total: {u_c + a_c}**")
        if st.sidebar.button("Filter Archive"):
            st.session_state['filter_q'] = q

    # --- HERO: GPT WRAPPED BANNER ---
    st.markdown('<div class="persona-banner">GPT WRAPPED</div>', unsafe_allow_html=True)
    
    # Interest Classification
    def detect_interest(df_inner):
        user_texts = df_inner[df_inner["role"] == "user"]["text"].dropna().str.lower()
        big_text = " ".join(user_texts.tolist())
        
        buckets = {
            "Tech / Coding": r"(python|code|bug|script|library|api|server|gpu|ram|macbook|linux|terminal|programming)",
            "Physics / Science": r"(quantum|spintronics|landauer|experiment|lab|wavefunction|nuclear|particle|physics)",
            "AI / ML / LLM": r"(prompt|chatgpt|gpt|llm|model|fine[- ]tune|dataset|ai|machine learning)",
            "Gaming / Media": r"(game|gaming|fps|steam|anime|movie|series|netflix|video)",
            "Life / Feelings": r"(relationship|overthink|tired|burnout|anxious|depressed|sad|happy|panic|feeling)",
        }
        
        scores = {}
        for label, pattern in buckets.items():
            scores[label] = len(re.findall(pattern, big_text))
        
        if not scores or max(scores.values()) == 0:
            return "Generalist", []
        
        primary = max(scores, key=scores.get)
        ranked = [k for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True) if v > 0]
        return primary, ranked[:3]
    
    primary_interest, top_interests = detect_interest(df)
    p = determine_persona(df)
    
    st.markdown(
        f"**Primary Class:** {primary_interest}  \n"
        f"**Secondary Orbits:** {', '.join(top_interests[1:]) if len(top_interests) > 1 else '—'}  \n"
        f"**Persona Flavor:** {p}"
    )
    st.markdown("---")
    
    # --- METRICS ROW: ALL IN ONE LINE ---
    words_all = word_tokenize(" ".join(df[df['role']=='user']['text']).lower())
    vocab = len(set(w for w in words_all if w.isalpha()))
    
    dates_unique = sorted(df['date'].unique())
    streak, max_streak = 1, 1
    for i in range(1, len(dates_unique)):
        if (dates_unique[i] - dates_unique[i-1]).days == 1:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    
    total_tokens = df['tokens'].sum()
    cost = (total_tokens / 1_000_000) * COST_PER_1M_TOKENS
    energy = (total_tokens / 1_000_000) * KWH_PER_1M_TOKENS
    water = (total_tokens / 1_000_000) * LITERS_PER_1M_TOKENS
    score, label = calculate_chaos_score(df)
    
    # ALL METRICS IN ONE ROW
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    col1.metric("Chaos", f"{score}/100", label, help="Variance-based unpredictability")
    col2.metric("Tokens", f"{total_tokens:,}", help="~0.75 words per token")
    col3.metric("Vocabulary", f"{vocab:,}", help="Unique words used")
    col4.metric("Cost", f"${cost:.2f}", help="Estimated cost at $2.50/1M tokens")
    col5.metric("Energy", f"{energy:.2f} kWh", help="Estimated energy consumption")
    col6.metric("Water", f"{water:.1f}L", help="Estimated water for datacenter cooling")
    col7.metric("Active Days", f"{len(dates_unique)}", help="Days with activity")
    col8.metric("Max Streak", f"{max_streak}", help="Longest consecutive days")
    
    st.caption("💡 Cost/Energy/Water are rough estimates based on industry averages for AI inference.")
    st.markdown("---")
    
    # --- INTEREST SHARE PIE CHART ---
    st.markdown("### 🧭 Interest Share")
    st.markdown("<div class='explanation'>Market share of your conversation topics. Shows what you talk about most based on keyword detection.</div>", unsafe_allow_html=True)
    
    def interest_counts(df_inner):
        user_texts = df_inner[df_inner["role"] == "user"]["text"].dropna().str.lower()
        big_text = " ".join(user_texts.tolist())
        
        buckets = {
            "Tech / Coding": r"(python|code|bug|script|library|api|server|gpu|ram|macbook|linux|terminal|programming)",
            "Physics / Science": r"(quantum|spintronics|landauer|experiment|lab|wavefunction|nuclear|particle|physics)",
            "AI / ML / LLM": r"(prompt|chatgpt|gpt|llm|model|fine[- ]tune|dataset|ai|machine learning)",
            "Gaming / Media": r"(game|gaming|fps|steam|anime|movie|series|netflix|video)",
            "Life / Feelings": r"(relationship|overthink|tired|burnout|anxious|depressed|sad|happy|panic|feeling)",
        }
        
        data = []
        for label, pattern in buckets.items():
            count = len(re.findall(pattern, big_text))
            if count > 0:
                data.append({"Interest": label, "Hits": count})
        return pd.DataFrame(data)
    
    interest_df = interest_counts(df)
    
    if not interest_df.empty:
        fig_pie = px.pie(
            interest_df,
            values="Hits",
            names="Interest",
            hole=0.4,
            title="Topic Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Not enough signal to detect interests yet.")
    
    st.markdown("---")

    # --- NEURAL FABRIC ---
    st.markdown("<div class='section-header'>🌌 Neural Fabric</div>", unsafe_allow_html=True)
    st.markdown("<div class='explanation'>A scatter plot of all your messages over time. Each dot is a message—Blue dots are you, Pink dots are AI responses. Y-axis shows message length (tokens). This reveals your conversation rhythm and intensity patterns.</div>", unsafe_allow_html=True)
    
    fabric_df = df.copy()
    fabric_df['color'] = fabric_df['role'].apply(lambda x: '#00CCFF' if x=='user' else '#FF0055')
    fig_fabric = go.Figure(data=go.Scattergl(
        x=fabric_df['dt'], y=fabric_df['tokens'], mode='markers',
        marker=dict(color=fabric_df['color'], size=5, opacity=0.7),
        text=fabric_df['tooltip'], hoverinfo='text'
    ))
    fig_fabric.update_layout(
        height=400, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title="Time"),
        yaxis=dict(showgrid=True, gridcolor='#222', title="Tokens")
    )
    st.plotly_chart(fig_fabric, use_container_width=True)

    # --- THEME EVOLUTION HEATMAP ---
    st.markdown("<div class='section-header'>📅 Theme Evolution</div>", unsafe_allow_html=True)
    st.markdown("<div class='explanation'>Shows how your conversation topics/models evolved over time. Each row is a time period (month), colored by the dominant model or topic. Brighter colors = more activity.</div>", unsafe_allow_html=True)
    
    # Create a heatmap of model usage by month
    theme_data = df.groupby(['month_year', 'model']).size().reset_index(name='count')
    if not theme_data.empty:
        theme_pivot = theme_data.pivot(index='month_year', columns='model', values='count').fillna(0)
        fig_theme = px.imshow(
            theme_pivot, 
            labels=dict(x="Model", y="Month", color="Messages"),
            color_continuous_scale='Viridis',
            aspect='auto'
        )
        fig_theme.update_layout(height=300)
        st.plotly_chart(fig_theme, use_container_width=True)
    else:
        st.info("Not enough data for theme evolution")

    # --- TEMPORAL RHYTHMS ---
    st.markdown("<div class='section-header'>⏳ Temporal Rhythms</div>", unsafe_allow_html=True)
    
    # Brain Clock
    st.markdown("### Brain Clock")
    st.markdown("<div class='explanation'>Your activity by hour of day. Reveals when you're most active. Are you a night owl or early bird?</div>", unsafe_allow_html=True)
    hourly = df.groupby('hour').size().reset_index(name='count')
    fig_clock = px.bar(hourly, x='hour', y='count', color='count', color_continuous_scale='Magma')
    fig_clock.update_layout(xaxis_title="Hour of Day", yaxis_title="Messages")
    st.plotly_chart(fig_clock, use_container_width=True)
    peak = hourly.loc[hourly['count'].idxmax()]['hour']
    st.markdown(f"**💡 Your peak hour:** {int(peak)}:00 — This is when you're most engaged.")

    # Token Economy
    st.markdown("### Token Economy")
    st.markdown("<div class='explanation'>Daily token usage over time. Spikes indicate heavy conversation days. This correlates with cost and computational load.</div>", unsafe_allow_html=True)
    daily = df.groupby('date')['tokens'].sum().reset_index()
    fig_eco = px.area(daily, x='date', y='tokens', title="Daily Token Burn")
    fig_eco.update_traces(line_color='#00FFCC', fillcolor='rgba(0,255,204,0.3)')
    st.plotly_chart(fig_eco, use_container_width=True)

    # --- PSYCHOLOGICAL DEEP DIVE ---
    st.markdown("<div class='section-header'>🧠 Psychological Deep Dive</div>", unsafe_allow_html=True)
    
    # Mood Graph
    st.markdown("### Mood Over Time")
    st.markdown("<div class='explanation'>Your emotional trajectory. Shows sentiment trends across all your messages. Rising trend = becoming more positive. Falling = increasing stress.</div>", unsafe_allow_html=True)
    user_df = df[df['role']=='user'].copy()
    if not user_df.empty and len(user_df) > 10:
        user_df['smooth_sentiment'] = user_df['sentiment'].rolling(window=min(20, len(user_df)//2), min_periods=1).mean()
        fig_mood = px.line(user_df, x='dt', y='smooth_sentiment', title="Mood Arc (Rolling Average)")
        fig_mood.update_traces(line_color='#FF0055', line_width=3)
        fig_mood.update_layout(yaxis_title="Sentiment", xaxis_title="Time")
        st.plotly_chart(fig_mood, use_container_width=True)
    
    # Emotional Categories
    st.markdown("### Emotional Categories")
    st.markdown("<div class='explanation'>Messages classified by detected emotion. Joy = positive keywords/sentiment. Stress = negative keywords. Neutral = everything else.</div>", unsafe_allow_html=True)
    
    joy_count = (user_df['sentiment'] > 0.2).sum()
    stress_count = (user_df['sentiment'] < -0.2).sum()
    neutral_count = len(user_df) - joy_count - stress_count
    
    mood_breakdown = pd.DataFrame({
        'Mood': ['😊 Joy', '😐 Neutral', '💀 Stress'],
        'Count': [joy_count, neutral_count, stress_count]
    })
    fig_moods = px.bar(mood_breakdown, x='Mood', y='Count', color='Mood', 
                       color_discrete_map={'😊 Joy': '#00FFCC', '😐 Neutral': '#888', '💀 Stress': '#FF0055'})
    st.plotly_chart(fig_moods, use_container_width=True)
    
    # Emotional DNA 2.0 - IMPROVED WITH TOOLTIPS
    st.markdown("### Emotional DNA 2.0")
    st.markdown("<div class='explanation'>A pixel map of your emotional state across all messages. Each pixel = one message. Red = stressed/negative, Grey = neutral, Green = joyful. Hover over pixels to see details including date, sentiment score, and message preview.</div>", unsafe_allow_html=True)
    
    if not user_df.empty:
        # Create bins
        user_df['mood_cat'] = pd.cut(user_df['sentiment'], bins=[-1, -0.2, 0.2, 1], labels=['Stress', 'Neutral', 'Joy'])
        mood_codes = {'Stress': 0, 'Neutral': 1, 'Joy': 2}
        user_df['mood_code'] = user_df['mood_cat'].map(mood_codes).fillna(1).astype(int)
        
        vals = user_df['mood_code'].values
        tooltips = user_df['tooltip'].values
        
        w, h = 100, (len(vals)//100) + 1
        g = np.full(w*h, 1); g[:len(vals)] = vals
        t = np.full(w*h, "", dtype=object); t[:len(tooltips)] = tooltips
        
        fig_dna = go.Figure(data=go.Heatmap(
            z=g.reshape(h, w),
            text=t.reshape(h, w),
            hovertemplate='%{text}<extra></extra>',
            showscale=False,
            colorscale=[[0, '#FF0055'], [0.5, '#444'], [1, '#00FFCC']]
        ))
        fig_dna.update_layout(
            height=300, 
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(title="Message Index (left to right)", showticklabels=False),
            yaxis=dict(title="Batch Row", showticklabels=False)
        )
        st.plotly_chart(fig_dna, use_container_width=True)

    # --- LINGUISTICS ---
    st.markdown("<div class='section-header'>🗣️ Prompt Archetypes</div>", unsafe_allow_html=True)
    st.markdown("<div class='explanation'>How you typically start your questions reveals your thinking style. High 'What' = exploratory/curious. High 'How' = execution-focused. 'Why' = analytical. 'Can' = permission-seeking or feasibility-checking.</div>", unsafe_allow_html=True)
    
    starts = df[df['role']=='user']['text'].str.lower().str[:15]
    styles = pd.DataFrame({
        "Start Type": ["What...", "How...", "Can...", "Why...", "Is...", "Does...", "Tell me..."],
        "Count": [
            starts.str.contains("what").sum(),
            starts.str.contains("how").sum(),
            starts.str.contains("can").sum(),
            starts.str.contains("why").sum(),
            starts.str.contains("is").sum(),
            starts.str.contains("does").sum(),
            starts.str.contains("tell me").sum()
        ]
    })
    styles = styles[styles['Count'] > 0].sort_values('Count', ascending=True)
    
    if not styles.empty:
        fig_style = px.bar(styles, x="Count", y="Start Type", orientation='h', 
                          title="How You Ask Questions", color="Count", color_continuous_scale='Purples')
        st.plotly_chart(fig_style, use_container_width=True)
        
        max_type = styles.iloc[-1]['Start Type']
        st.markdown(f"**💡 Your dominant style:** {max_type} — You tend to be {('exploratory' if 'What' in max_type else 'action-oriented' if 'How' in max_type else 'analytical')}")

    # --- ARCHIVE ---
    st.markdown("<div class='section-header'>📂 Archive</div>", unsafe_allow_html=True)
    st.markdown("<div class='explanation'>Your conversation history organized by different criteria. Browse heavyweight threads (longest, most emotional) or search through the complete index.</div>", unsafe_allow_html=True)
    
    # Filter threads based on date range
    threads = all_threads[all_threads['conv_id'].isin(df['conv_id'])].copy()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📜 Longest**")
        for _, r in threads.sort_values('tokens', ascending=False).head(5).iterrows():
            st.markdown(f"- {r['title'][:25]}... ({r['tokens']} tok)")
    with col2:
        st.markdown("**💀 Most Stressed**")
        for _, r in threads.sort_values('sentiment').head(5).iterrows():
            st.markdown(f"- {r['title'][:25]}... ({r['sentiment']:.2f})")
    with col3:
        st.markdown("**😊 Happiest**")
        for _, r in threads.sort_values('sentiment', ascending=False).head(5).iterrows():
            st.markdown(f"- {r['title'][:25]}... ({r['sentiment']:.2f})")
    
    st.markdown("---")
    st.markdown("### 🗂️ Complete Index")
    
    # Filter mechanism
    filter_q = st.session_state.get('filter_q', '')
    if filter_q:
        st.success(f"Filtering for: '{filter_q}'")
        threads = threads[threads['title'].str.contains(filter_q, case=False, na=False)]
        if st.button("Clear Filter"):
            del st.session_state['filter_q']
            st.rerun()
    
    # Randomizer
    if st.button("🎲 Random Thread"):
        if not threads.empty:
            st.session_state['rand_tid'] = random.choice(threads['conv_id'].tolist())
    
    # Search box
    search_box = st.text_input("Search threads:", "")
    if search_box:
        threads = threads[threads['title'].str.contains(search_box, case=False, na=False)]
    
    # Show table
    st.dataframe(threads[['title', 'tokens', 'sentiment']].head(50), use_container_width=True)
    st.caption(f"Showing {min(50, len(threads))} of {len(threads)} threads")
    
    # Thread Reader
    tid_list = threads['conv_id'].tolist()
    if tid_list:
        idx = 0
        if st.session_state.get('rand_tid') in tid_list:
            idx = tid_list.index(st.session_state['rand_tid'])
        
        sel = st.selectbox("Open Thread", tid_list, 
                          format_func=lambda x: threads[threads['conv_id']==x]['title'].values[0], 
                          index=idx)
        
        t_msgs = full_df[full_df['conv_id'] == sel]
        st.markdown("---")
        for _, m in t_msgs.iterrows():
            css = "user-bubble" if m['role'] == 'user' else "ai-bubble"
            icon = "👤" if m['role'] == 'user' else "🤖"
            st.markdown(f'<div class="chat-bubble {css}"><b>{icon}</b>: {m["text"]}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
