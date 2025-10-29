"""
Professional theme system for Streamlit UI

Provides:
- Dark mode (default)
- Light mode
- Blue mode
- Custom CSS styling
"""

# Theme definitions
THEMES = {
    "dark": {
        "name": "🌙 Dark Mode",
        "primary_color": "#6366f1",
        "background_color": "#0f172a",
        "secondary_background_color": "#1e293b",
        "text_color": "#f1f5f9",
        "secondary_text_color": "#cbd5e1",
        "accent_color": "#8b5cf6",
        "success_color": "#10b981",
        "warning_color": "#f59e0b",
        "error_color": "#ef4444",
        "border_color": "#334155",
        "card_background": "#1e293b",
        "hover_color": "#334155",
    },
    "light": {
        "name": "☀️ Light Mode",
        "primary_color": "#4f46e5",
        "background_color": "#ffffff",
        "secondary_background_color": "#f8fafc",
        "text_color": "#0f172a",
        "secondary_text_color": "#475569",
        "accent_color": "#7c3aed",
        "success_color": "#059669",
        "warning_color": "#d97706",
        "error_color": "#dc2626",
        "border_color": "#e2e8f0",
        "card_background": "#f8fafc",
        "hover_color": "#e2e8f0",
    },
    "blue": {
        "name": "🌊 Blue Mode",
        "primary_color": "#0ea5e9",
        "background_color": "#0c4a6e",
        "secondary_background_color": "#075985",
        "text_color": "#f0f9ff",
        "secondary_text_color": "#bae6fd",
        "accent_color": "#06b6d4",
        "success_color": "#14b8a6",
        "warning_color": "#f59e0b",
        "error_color": "#f43f5e",
        "border_color": "#0369a1",
        "card_background": "#075985",
        "hover_color": "#0369a1",
    }
}


def get_theme_css(theme_name: str = "dark") -> str:
    """
    Generate CSS for the selected theme.
    
    Args:
        theme_name: Theme name (dark, light, blue)
        
    Returns:
        CSS string
    """
    theme = THEMES.get(theme_name, THEMES["dark"])
    
    css = f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
    :root {{
        --primary-color: {theme['primary_color']};
        --background-color: {theme['background_color']};
        --secondary-bg: {theme['secondary_background_color']};
        --text-color: {theme['text_color']};
        --secondary-text: {theme['secondary_text_color']};
        --accent-color: {theme['accent_color']};
        --success-color: {theme['success_color']};
        --warning-color: {theme['warning_color']};
        --error-color: {theme['error_color']};
        --border-color: {theme['border_color']};
        --card-bg: {theme['card_background']};
        --hover-color: {theme['hover_color']};
    }}
    
    /* Global styles */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    
    /* Main app background */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: var(--secondary-bg);
        border-right: 1px solid var(--border-color);
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-color);
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-color);
        font-weight: 600;
        letter-spacing: -0.02em;
    }}
    
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Cards and containers */
    .element-container {{
        color: var(--text-color);
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Text inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: var(--card-bg);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }}
    
    /* Select boxes */
    .stSelectbox > div > div {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }}

    /* File uploader */
    .stFileUploader {{
        background-color: var(--card-bg);
        border: 2px dashed var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.3s ease;
    }}

    .stFileUploader:hover {{
        border-color: var(--primary-color);
        background-color: var(--hover-color);
    }}

    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: var(--primary-color);
        font-size: 2rem;
        font-weight: 700;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--secondary-text);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-color);
        font-weight: 500;
    }}

    .streamlit-expanderHeader:hover {{
        background-color: var(--hover-color);
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: var(--secondary-bg);
        border-radius: 8px;
        padding: 0.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: 6px;
        color: var(--secondary-text);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--hover-color);
        color: var(--text-color);
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white !important;
    }}

    /* Success/Info/Warning/Error boxes */
    .stSuccess {{
        background-color: var(--success-color);
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stInfo {{
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stWarning {{
        background-color: var(--warning-color);
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stError {{
        background-color: var(--error-color);
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }}

    /* Dataframe */
    .stDataFrame {{
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }}

    /* Spinner */
    .stSpinner > div {{
        border-top-color: var(--primary-color) !important;
    }}

    /* Custom card class */
    .custom-card {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }}

    .custom-card:hover {{
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }}

    /* Chat message styling */
    .chat-message {{
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        animation: fadeIn 0.3s ease;
    }}

    .chat-message.user {{
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        margin-left: 2rem;
    }}

    .chat-message.assistant {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        margin-right: 2rem;
    }}

    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--secondary-bg);
    }}

    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-color);
    }}
    </style>
    """

    return css

