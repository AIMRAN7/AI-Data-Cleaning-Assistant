"""
AI Data Cleaning Assistant Pro
A professional AI-powered Streamlit app for automated data cleaning with chatbot assistance.

Author: Abdullah Imran
Date: October 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import warnings
import os
warnings.filterwarnings('ignore')

# Import custom utilities
from utils.data_analyzer import DataAnalyzer
from utils.data_cleaner import DataCleaner
from utils.ai_assistant import AIAssistant
# Guard DB import so app can run without sqlalchemy installed
try:
    from utils.db_io import read_from_database  # type: ignore
    _DB_AVAILABLE = True
except Exception:
    read_from_database = None  # type: ignore
    _DB_AVAILABLE = False
from utils.report import generate_executive_pdf
from utils.recipe_export import to_python as recipe_to_python, to_sql as recipe_to_sql
from plugins.registry import get_rules
from plugins.registry import get_db_connectors
from utils.diff_ops import create_manual_edit_ops
from utils.audit import save_ui_auth, load_ui_auth, write_audit

# Try to import streamlit-aggrid for spreadsheet features
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# Page configuration with increased limits
st.set_page_config(
    page_title="AI Data Cleaning Assistant Pro",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Increase max upload size to 500MB
try:
    st.set_option('server.maxUploadSize', 500)
except:
    pass  # Fallback if option not available

# Advanced Custom CSS for professional styling
st.markdown("""
<style>
    /* Main Header with Gradient */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeInDown 1s ease-in;
    }
    
    /* Animated Subheaders */
    .sub-header {
        font-size: 1.5rem;
        color: #667eea;
        margin-top: 2rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
        animation: slideInLeft 0.5s ease-out;
    }
    
    /* Enhanced Metric Cards with Hover Effects */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    
    /* Success Box with Icon */
    .success-box {
        padding: 1.5rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        color: #155724;
        box-shadow: 0 4px 6px rgba(40, 167, 69, 0.2);
        animation: bounceIn 0.5s ease-out;
    }
    
    /* Warning Box */
    .warning-box {
        padding: 1.5rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border: 2px solid #ffc107;
        color: #856404;
        box-shadow: 0 4px 6px rgba(255, 193, 7, 0.2);
    }
    
    /* Info Box */
    .info-box {
        padding: 1.5rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        color: #0c5460;
        box-shadow: 0 4px 6px rgba(23, 162, 184, 0.2);
    }
    
    /* Quality Score Badge */
    .quality-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 2rem;
        font-weight: bold;
        font-size: 1.2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.4);
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes bounceIn {
        0% {
            opacity: 0;
            transform: scale(0.3);
        }
        50% {
            opacity: 1;
            transform: scale(1.05);
        }
        70% {
            transform: scale(0.9);
        }
        100% {
            transform: scale(1);
        }
    }
    
    /* Button Enhancements */
    .stButton > button {
        border-radius: 2rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    /* Progress Bar Styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Data Frame Styling */
    .dataframe {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 0.5rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df_original' not in st.session_state:
    st.session_state.df_original = None
if 'df_cleaned' not in st.session_state:
    st.session_state.df_cleaned = None
if 'cleaning_applied' not in st.session_state:
    st.session_state.cleaning_applied = False
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = {}
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = AIAssistant()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'spreadsheet_mode' not in st.session_state:
    st.session_state.spreadsheet_mode = False
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = None
if 'cleaning_log' not in st.session_state:
    st.session_state.cleaning_log = []
# Undo/redo stacks for Safe Preview & Undo
if 'history' not in st.session_state:
    st.session_state.history = []  # stack of prior dataframes
if 'future' not in st.session_state:
    st.session_state.future = []


def load_data(uploaded_file):
    """Load data from uploaded file."""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        elif file_extension == 'json':
            df = pd.read_json(uploaded_file)
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def display_data_overview(df):
    """Display comprehensive data overview with AI insights."""
    st.markdown('<p class="sub-header">Data Overview & AI Insights</p>', unsafe_allow_html=True)
    
    # Create analyzer instance for AI features
    analyzer = DataAnalyzer(df)
    
    # AI Natural Language Summary
    st.markdown("### AI Summary")
    summary = analyzer.generate_natural_language_summary()
    st.markdown(f'<div class="info-box">{summary}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quality Score Badge
    quality_score = analyzer.get_data_quality_score()
    score_color = "#28a745" if quality_score >= 90 else "#ffc107" if quality_score >= 70 else "#dc3545"
    st.markdown(
        f'<div style="text-align: center; margin: 1rem 0;">'
        f'<span class="quality-badge" style="background: {score_color};">Quality Score: {quality_score:.1f}/100</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # Enhanced metrics in columns with icons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", f"{df.shape[0]:,}", help="Number of records in your dataset")
    with col2:
        st.metric("Total Columns", df.shape[1], help="Number of features/variables")
    with col3:
        missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
        delta_color = "inverse" if missing_pct > 0 else "normal"
        st.metric("Missing Data", f"{missing_pct:.2f}%", delta=None, delta_color=delta_color, help="Percentage of missing values")
    with col4:
        duplicate_count = df.duplicated().sum()
        st.metric("Duplicates", duplicate_count, delta=None, delta_color="inverse" if duplicate_count > 0 else "normal", help="Number of duplicate rows")
    
    st.markdown("---")
    
    # Pattern Detection
    patterns = analyzer.detect_patterns()
    if patterns:
        st.markdown("### Data Patterns Detected")
        pattern_cols = st.columns(len(patterns) if len(patterns) <= 4 else 4)
        for idx, (col, pattern) in enumerate(patterns.items()):
            with pattern_cols[idx % 4]:
                st.info(f"**{col}**: {pattern}")
    
    # Dataset preview with better formatting
    st.markdown("#### Dataset Preview (First 10 Rows)")
    st.dataframe(
        df.head(10),
        use_container_width=True,
        height=400
    )
    
    # Column information in expandable section
    with st.expander("**Detailed Column Information**", expanded=False):
        col_info = analyzer.get_column_info()
        st.dataframe(col_info, use_container_width=True)
        
        # Column-specific suggestions
        st.markdown("#### Column-Specific Recommendations")
        selected_col = st.selectbox("Select a column for smart suggestions:", df.columns.tolist())
        if selected_col:
            col_suggestions = analyzer.suggest_column_operations(selected_col)
            if col_suggestions:
                for sug in col_suggestions:
                    st.markdown(f"- {sug}")
            else:
                st.success(f"Column '{selected_col}' looks good!")


def display_ai_suggestions(df):
    """Display AI-powered cleaning suggestions with enhanced UX."""
    st.markdown('<p class="sub-header">AI-Powered Cleaning Suggestions</p>', unsafe_allow_html=True)
    
    analyzer = DataAnalyzer(df)
    suggestions = analyzer.generate_suggestions()

    # Merge plugin rules
    try:
        for rule in get_rules():
            for idx, plugin_sug in enumerate(rule(df)):
                key = plugin_sug.get('key') or f"Plugin Suggestion {idx+1}"
                suggestions[key] = plugin_sug
    except Exception as e:
        st.warning(f"Plugin rules error: {e}")
    
    if not suggestions:
        st.markdown(
            '<div class="success-box">'
            '<h3>Excellent News!</h3>'
            '<p>Your dataset appears to be clean and ready for analysis. No cleaning suggestions needed.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        return {}
    
    # Summary card
    st.markdown(
        f'<div class="warning-box">'
        f'<h4>{len(suggestions)} Issues Found</h4>'
        f'<p>Our AI has identified several areas for improvement. Review and apply suggestions below.</p>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Categorize suggestions
    critical_suggestions = {}
    moderate_suggestions = {}
    minor_suggestions = {}
    
    for key, sug in suggestions.items():
        sug_type = sug.get('type')
        if sug_type == 'duplicates':
            critical_suggestions[key] = sug
        elif sug_type in ['missing_numeric', 'missing_categorical']:
            moderate_suggestions[key] = sug
        else:
            minor_suggestions[key] = sug
    
    # Display by priority with icons and colors
    if critical_suggestions:
        st.markdown("### Critical Issues (High Priority)")
        for idx, (key, suggestion) in enumerate(critical_suggestions.items(), 1):
            with st.expander(f"**{idx}. {key}** - Requires Immediate Attention", expanded=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Issue:** {suggestion['issue']}")
                    st.markdown(f"**Recommendation:** {suggestion['action']}")
                    if 'details' in suggestion:
                        st.info(suggestion['details'])
                with col2:
                    st.metric("Priority", "High", delta="Critical")
    
    if moderate_suggestions:
        st.markdown("### Moderate Issues (Medium Priority)")
        for idx, (key, suggestion) in enumerate(moderate_suggestions.items(), 1):
            with st.expander(f"**{idx}. {key}** - Should Be Fixed", expanded=True):
                st.markdown(f"**Issue:** {suggestion['issue']}")
                st.markdown(f"**Recommendation:** {suggestion['action']}")
                if 'details' in suggestion:
                    st.info(suggestion['details'])
    
    if minor_suggestions:
        st.markdown("### Minor Issues (Low Priority)")
        for idx, (key, suggestion) in enumerate(minor_suggestions.items(), 1):
            with st.expander(f"**{idx}. {key}** - Optional Improvement"):
                st.markdown(f"**Issue:** {suggestion['issue']}")
                st.markdown(f"**Recommendation:** {suggestion['action']}")
                if 'details' in suggestion:
                    st.info(suggestion['details'])
    
    return suggestions


def apply_cleaning(df, suggestions):
    """Apply all cleaning suggestions to the dataset."""
    try:
        cleaner = DataCleaner(df.copy())
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(suggestions)
        
        for idx, (key, suggestion) in enumerate(suggestions.items()):
            status_text.text(f"Applying: {key}...")
            
            action_type = suggestion.get('type')
            
            if action_type == 'missing_numeric':
                column = suggestion['column']
                cleaner.fill_missing_numeric(column, method='mean')
            
            elif action_type == 'missing_categorical':
                column = suggestion['column']
                cleaner.fill_missing_categorical(column)
            
            elif action_type == 'duplicates':
                cleaner.remove_duplicates()
            
            elif action_type == 'outliers':
                column = suggestion['column']
                cleaner.remove_outliers(column)
            
            elif action_type == 'data_type':
                column = suggestion['column']
                target_type = suggestion.get('target_type', 'numeric')
                cleaner.convert_data_type(column, target_type)
                # Optimize: if became float but has no fraction, use Int64
                cleaner.convert_float_to_int_if_possible(column)

            elif action_type == 'whitespace':
                column = suggestion['column']
                cleaner.trim_whitespace([column])

            elif action_type == 'text_case':
                column = suggestion['column']
                cleaner.standardize_text_case([column], case='lower')

            elif action_type == 'datetime_parse':
                column = suggestion['column']
                cleaner.parse_datetime(column)

            elif action_type == 'constant_column':
                column = suggestion['column']
                cleaner.remove_columns([column])

            elif action_type == 'boolean_text':
                column = suggestion['column']
                cleaner.convert_boolean_text(column)

            elif action_type == 'percentage_string':
                column = suggestion['column']
                cleaner.convert_percentage_strings(column)
            
            progress_bar.progress((idx + 1) / max(total_steps, 1))
        
        # Save log to session for user review
        st.session_state.cleaning_log = cleaner.get_cleaning_log()
        # Save operations for recipe export
        if hasattr(cleaner, 'get_operations'):
            st.session_state.last_operations = cleaner.get_operations()

        status_text.text("All cleaning operations completed!")
        progress_bar.empty()
        status_text.empty()
        
        return cleaner.df
    
    except Exception as e:
        st.error(f"Error during cleaning: {str(e)}")
        return df


def display_visualizations(df, title="Data Visualizations"):
    """Display comprehensive data visualizations."""
    st.markdown(f'<p class="sub-header">{title}</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Missing Values", "Column Distributions", "Data Types", "Correlation"])
    
    with tab1:
        # Missing values heatmap
        st.markdown("#### Missing Values Heatmap")
        missing_data = df.isnull()
        
        if missing_data.sum().sum() > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(missing_data, cbar=True, cmap='YlOrRd', ax=ax)
            plt.title("Missing Values Pattern")
            plt.tight_layout()
            st.pyplot(fig)
            
            # Missing values bar chart
            st.markdown("#### Missing Values by Column")
            missing_counts = df.isnull().sum()
            missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=False)
            
            if len(missing_counts) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                missing_counts.plot(kind='bar', ax=ax, color='coral')
                ax.set_xlabel('Column')
                ax.set_ylabel('Missing Count')
                ax.set_title('Missing Values Count by Column')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.success("No missing values in the dataset!")
    
    with tab2:
        # Column distributions
        st.markdown("#### Column Distributions")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_col = st.selectbox("Select a numeric column:", numeric_cols)
            
            if selected_col:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histogram
                    fig, ax = plt.subplots(figsize=(8, 6))
                    df[selected_col].hist(bins=30, ax=ax, color='skyblue', edgecolor='black')
                    ax.set_xlabel(selected_col)
                    ax.set_ylabel('Frequency')
                    ax.set_title(f'Distribution of {selected_col}')
                    plt.tight_layout()
                    st.pyplot(fig)
                
                with col2:
                    # Box plot
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.boxplot(y=df[selected_col], ax=ax, color='lightgreen')
                    ax.set_ylabel(selected_col)
                    ax.set_title(f'Box Plot of {selected_col}')
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Statistics
                st.markdown(f"**Statistics for {selected_col}:**")
                stats_df = df[selected_col].describe().to_frame().T
                st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No numeric columns available for distribution plots.")
    
    with tab3:
        # Data types breakdown
        st.markdown("#### Data Types Breakdown")
        
        dtype_counts = df.dtypes.value_counts()
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(dtype_counts.values, labels=dtype_counts.index.astype(str), autopct='%1.1f%%', startangle=90)
        ax.set_title('Data Types Distribution')
        plt.tight_layout()
        st.pyplot(fig)
        
        # Detailed breakdown
        st.markdown("**Columns by Data Type:**")
        for dtype in df.dtypes.unique():
            cols = df.select_dtypes(include=[dtype]).columns.tolist()
            st.markdown(f"- **{dtype}**: {', '.join(cols)}")

    with tab4:
        # Correlation heatmap for numeric columns
        st.markdown("#### Correlation Heatmap (numeric columns)")
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] >= 2:
            corr = numeric_df.corr(numeric_only=True)
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr, annot=False, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Correlation Heatmap')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Not enough numeric columns to compute correlations.")


def export_data(df, filename="cleaned_data"):
    """Provide export options for cleaned data."""
    st.markdown('<p class="sub-header">Export Cleaned Data</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"{filename}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export as Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        
        st.download_button(
            label="Download as Excel",
            data=buffer.getvalue(),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


def display_ai_chatbot(df):
    """Display AI-powered chatbot interface."""
    st.markdown('<p class="sub-header">AI Assistant Chat</p>', unsafe_allow_html=True)
    
    ai_assistant = st.session_state.ai_assistant
    
    # AI Provider Selection
    with st.expander("AI Provider Settings", expanded=not ai_assistant.is_available()):
        st.markdown("### Choose Your AI Provider")
        
        col1, col2 = st.columns(2)
        
        with col1:
            provider = st.selectbox(
                "AI Provider",
                ["gemini", "ollama", "openai", "claude"],
                format_func=lambda x: {
                    "gemini": "Google Gemini (FREE)",
                    "ollama": "Ollama (FREE Local)",
                    "openai": "OpenAI GPT (Paid)",
                    "claude": "Anthropic Claude (Paid)"
                }[x],
                key="ai_provider_select"
            )
        
        with col2:
            if provider in ["gemini", "openai", "claude"]:
                api_key_label = {
                    "gemini": "Google API Key",
                    "openai": "OpenAI API Key",
                    "claude": "Anthropic API Key"
                }[provider]
                
                api_key = st.text_input(api_key_label, type="password", key=f"{provider}_key")
            else:
                st.info("Ollama runs locally - no API key needed!")
                api_key = None
        
        # Instructions
        if provider == "gemini":
            st.success("**FREE TIER AVAILABLE!**")
            st.markdown("""
            **Get your FREE API key:**
            1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Click "Create API Key"
            3. Paste it above
            
            **Free tier:** 60 requests/minute - perfect for data cleaning!
            """)
        elif provider == "ollama":
            st.success("**100% FREE - Runs on your computer!**")
            st.markdown("""
            **Setup Ollama:**
            1. Download from [ollama.ai](https://ollama.ai)
            2. Install and run `ollama serve`
            3. Run `ollama pull llama2`
            
            **No internet needed after download!**
            """)
        elif provider == "openai":
            st.info("Requires paid API credits")
            st.markdown("Get your API key from [platform.openai.com](https://platform.openai.com/api-keys)")
        elif provider == "claude":
            st.info("Requires paid API credits")
            st.markdown("Get your API key from [console.anthropic.com](https://console.anthropic.com/)")
        
        if st.button("Connect AI Provider", type="primary"):
            if provider == "ollama" or api_key:
                try:
                    st.session_state.ai_assistant = AIAssistant(provider=provider, api_key=api_key)
                    if st.session_state.ai_assistant.is_available():
                        st.success(f"Connected to {provider.upper()}!")
                        st.rerun()
                    else:
                        st.error(f"Could not connect to {provider}. Check your setup.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter an API key")
    
    # Status indicator
    if ai_assistant.is_available():
        provider_name = {
            "gemini": "Google Gemini (FREE)",
            "ollama": "Ollama Local (FREE)",
            "openai": "OpenAI GPT",
            "claude": "Anthropic Claude"
        }.get(ai_assistant.provider, "AI")
        st.success(f"AI Assistant active: **{provider_name}**")
    else:
        st.warning("AI not configured - using rule-based responses")
    
    # Chat interface
    st.markdown("### Ask about your data")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="info-box"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box"><strong>AI Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([5, 1])
    with col1:
        user_question = st.text_input(
            "Your question",
            placeholder="E.g., How should I handle missing values?",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col2:
        ask_button = st.button("Ask", type="primary", use_container_width=True)
    
    if ask_button and user_question and df is not None:
        # Get AI response
        with st.spinner("Thinking..."):
            response = ai_assistant.get_data_insights(df, user_question)
        
        # Add to history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Quick action buttons
    if df is not None:
        st.markdown("#### Quick Questions")
        quick_cols = st.columns(3)
        with quick_cols[0]:
            if st.button("Dataset Summary", use_container_width=True):
                analyzer = DataAnalyzer(df)
                summary = analyzer.generate_natural_language_summary()
                st.session_state.chat_history.append({"role": "user", "content": "Give me a dataset summary"})
                st.session_state.chat_history.append({"role": "assistant", "content": summary})
                st.rerun()
        
        with quick_cols[1]:
            if st.button("Missing Values", use_container_width=True):
                response = ai_assistant.get_data_insights(df, "Tell me about missing values in my data")
                st.session_state.chat_history.append({"role": "user", "content": "Tell me about missing values"})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
        
        with quick_cols[2]:
            if st.button("Best Practices", use_container_width=True):
                response = ai_assistant.get_data_insights(df, "What are the best practices for cleaning this data?")
                st.session_state.chat_history.append({"role": "user", "content": "Best practices for cleaning?"})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            ai_assistant.clear_history()
            st.rerun()


def display_spreadsheet_editor(df):
    """Display interactive spreadsheet-like data editor."""
    st.markdown('<p class="sub-header">Spreadsheet Editor</p>', unsafe_allow_html=True)
    
    if not AGGRID_AVAILABLE:
        st.warning("Install streamlit-aggrid for enhanced spreadsheet features: `pip install streamlit-aggrid`")
        st.markdown("### Basic Data Editor")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",  # Allow adding/deleting rows
            height=500
        )
        st.session_state.edited_df = edited_df
        return edited_df
    
    # Advanced AgGrid editor
    st.markdown("### Interactive Spreadsheet (Click cells to edit)")
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    
    gridOptions = gb.build()
    
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        height=500,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False
    )
    
    edited_df = grid_response['data']
    selected_rows = grid_response['selected_rows']
    
    # Store edited data
    st.session_state.edited_df = edited_df
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Add Column"):
            new_col_name = f"NewColumn_{len(edited_df.columns) + 1}"
            edited_df[new_col_name] = ""
            st.session_state.edited_df = edited_df
            st.rerun()
    
    with col2:
        if st.button("Delete Selected Rows") and selected_rows is not None and len(selected_rows) > 0:
            indices_to_drop = [row['_selectedRowNodeInfo']['nodeRowIndex'] for row in selected_rows]
            edited_df = edited_df.drop(edited_df.index[indices_to_drop]).reset_index(drop=True)
            st.session_state.edited_df = edited_df
            st.success(f"Deleted {len(indices_to_drop)} rows")
            st.rerun()
    
    with col3:
        if st.button("Save Changes"):
            st.session_state.df_cleaned = edited_df
            st.success("Changes saved to cleaned dataset!")
    
    with col4:
        if st.button("Reset to Original"):
            st.session_state.edited_df = st.session_state.df_original.copy()
            st.rerun()
    
    # Show statistics
    if selected_rows is not None and len(selected_rows) > 0:
        st.info(f"{len(selected_rows)} row(s) selected")
    
    return edited_df


def main():
    """Main application function."""
    # Header
    st.markdown('<p class="main-header">AI Data Cleaning Assistant Pro</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 1.2rem;">'
        'AI-Powered Data Cleaning with Chatbot & Spreadsheet Editor - Upload up to 500MB'
        '</p>',
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=100)
        st.markdown("### Upload Your Dataset")
        st.caption("Maximum file size: 500MB")

        # Minimal auth layer
        with st.expander("Authentication (optional)"):
            enable_auth = st.checkbox("Enable auth in UI", value=False)
            if enable_auth:
                existing = load_ui_auth() or {"token": "", "role": "viewer"}
                default_role = ["viewer", "editor", "admin"].index(existing.get("role", "viewer")) if existing else 0
                token = st.text_input("Bearer token", type="password")
                role = st.selectbox("Role", ["viewer", "editor", "admin"], index=default_role)
                st.session_state.ui_auth = {"enabled": True, "token": token, "role": role}
                if st.button("Save auth settings"):
                    try:
                        save_ui_auth(token, role)
                        st.success("Auth settings saved locally.")
                    except Exception as e:
                        st.error(f"Failed to save auth settings: {e}")
            else:
                st.session_state.ui_auth = {"enabled": False}

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'xls', 'json'],
            help="Supported formats: CSV, Excel, JSON (up to 500MB)"
        )

        # Database loader (MVP)
        with st.expander("Load from Database (SQLAlchemy URL)"):
            st.caption("Postgres/MySQL/others via SQLAlchemy drivers")
            if not _DB_AVAILABLE:
                st.warning("Database features are unavailable. Install with: pip install sqlalchemy psycopg2-binary (Postgres) or pip install sqlalchemy pymysql (MySQL)")
            db_url = st.text_input("Connection URL", placeholder="postgresql+psycopg2://user:pass@host:5432/db")
            db_table = st.text_input("Table name (optional if using query)")
            db_query = st.text_area("Custom SQL query (optional)")
            db_limit = st.number_input("Limit (optional)", min_value=0, value=0, step=1000, help="0 = no limit")
            # Plugin connectors render here
            connectors = get_db_connectors()
            if connectors:
                st.markdown("#### Plugin Connectors")
                for c in connectors:
                    with st.expander(f"{c['name']}"):
                        try:
                            df_plugin = c["render"]()
                            if df_plugin is not None:
                                st.session_state.df_original = df_plugin
                                st.session_state.df_cleaned = df_plugin.copy()
                                st.session_state.cleaning_applied = False
                                st.success(f"Loaded {df_plugin.shape[0]:,} rows x {df_plugin.shape[1]} cols via {c['name']}")
                        except Exception as e:
                            st.error(f"Connector '{c['name']}' error: {e}")
            if st.button("Load from DB"):
                if not _DB_AVAILABLE:
                    st.error("SQLAlchemy not installed. Install it to enable database loading.")
                elif not db_url:
                    st.error("Please enter a connection URL")
                else:
                    try:
                        with st.spinner("Querying database..."):
                            df_db = read_from_database(
                                connection_url=db_url,
                                table=db_table or None,
                                query=db_query or None,
                                limit=None if db_limit == 0 else int(db_limit)
                            )
                        st.session_state.df_original = df_db
                        st.session_state.df_cleaned = df_db.copy()
                        st.session_state.cleaning_applied = False
                        st.success(f"Loaded {df_db.shape[0]:,} rows x {df_db.shape[1]} cols from database")
                        auth = st.session_state.get('ui_auth', {"enabled": False, "role": "viewer"})
                        write_audit(auth.get("role", "viewer"), "load_db", {"rows": int(df_db.shape[0]), "cols": int(df_db.shape[1])})
                    except Exception as e:
                        st.error(f"DB load failed: {e}")

        st.markdown("---")
        st.markdown("### Features")
        st.success(
            """
            **AI-Powered:**
            - Chat assistant integration
            - Natural language insights
            - Smart recommendations

            **Spreadsheet Editor:**
            - Click-to-edit cells
            - Add/delete rows
            - Live data editing

            **Advanced Analytics:**
            - Quality scoring
            - Pattern detection
            - Correlation analysis

            **Large Files:**
            - Up to 500MB upload
            - Fast processing
            """
        )
        
        st.markdown("---")
        st.markdown("**Developer:** Abdullah Imran")
        st.markdown("**Version:** 2.0.0 Pro")
    
    # Main content
    if uploaded_file is not None or st.session_state.get('df_original') is not None:
        # Auth guard
        ui_auth = st.session_state.get('ui_auth', {"enabled": False})
        if ui_auth.get("enabled") and not ui_auth.get("token"):
            st.warning("Authentication enabled. Please provide a token to continue.")
            return
        
        # Load data
        if st.session_state.df_original is None:
            with st.spinner("Loading your dataset..."):
                st.session_state.df_original = load_data(uploaded_file)
                st.session_state.df_cleaned = st.session_state.df_original.copy()
                st.session_state.cleaning_applied = False
                # Audit file upload
                try:
                    auth = st.session_state.get('ui_auth', {"enabled": False, "role": "viewer"})
                    write_audit(auth.get("role", "viewer"), "upload_file", {"name": getattr(uploaded_file, 'name', 'unknown'), "rows": int(st.session_state.df_original.shape[0]), "cols": int(st.session_state.df_original.shape[1])})
                except Exception:
                    pass
                
        if st.session_state.df_original is not None:
            # Create tabs for different features
            tab1, tab2, tab3, tab4 = st.tabs([
                "Data Analysis & Cleaning",
                "AI Assistant Chat",
                "Spreadsheet Editor",
                "Visualizations"
            ])
            
            with tab1:
                # Display overview
                display_data_overview(st.session_state.df_original)
                
                st.markdown("---")
                
                # Get and display suggestions
                suggestions = display_ai_suggestions(st.session_state.df_original)
                st.session_state.suggestions = suggestions
                
                # Safe preview: show a one-click preview result before committing
                if suggestions:
                    st.markdown("---")

                    preview_col1, preview_col2, preview_col3 = st.columns([1,2,1])
                    with preview_col2:
                        if st.button("Preview Apply All", use_container_width=True):
                            with st.spinner("Previewing changes..."):
                                preview_df = apply_cleaning(st.session_state.df_original, suggestions)
                            # store preview in session but do not commit
                            st.session_state._preview_df = preview_df
                            st.session_state.last_operations = st.session_state.get('cleaner_last_ops', [])
                            st.success("Preview ready below. Use Commit/Undo to apply or discard.")
                    # show preview table if exists
                    if hasattr(st.session_state, '_preview_df') and st.session_state._preview_df is not None:
                        st.markdown("#### Preview (not yet saved)")
                        st.dataframe(st.session_state._preview_df.head(10), use_container_width=True)
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Commit Preview", type="primary"):
                                # push current cleaned/original onto history for undo
                                base_df = st.session_state.df_cleaned if st.session_state.cleaning_applied else st.session_state.df_original
                                st.session_state.history.append(base_df.copy())
                                st.session_state.df_cleaned = st.session_state._preview_df
                                st.session_state.cleaning_applied = True
                                # keep last ops for recipe export if available
                                st.session_state.future = []  # clear redo stack
                                del st.session_state._preview_df
                                st.success("Changes committed. You can Undo/Redo below.")
                        with c2:
                            if st.button("Discard Preview"):
                                del st.session_state._preview_df
                                st.info("Preview discarded.")
                    
                    # Apply cleaning button (direct commit)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("Apply All Suggestions", use_container_width=True, type="primary"):
                            with st.spinner("Applying cleaning operations..."):
                                # push original to history for undo
                                st.session_state.history.append(st.session_state.df_original.copy())
                                st.session_state.df_cleaned = apply_cleaning(
                                    st.session_state.df_original,
                                    suggestions
                                )
                                st.session_state.cleaning_applied = True
                                # after apply, capture operations from cleaner via a side channel
                                # apply_cleaning uses a local cleaner; expose ops via session_state
                                # We will store last_operations inside apply_cleaning via session update below
                                st.session_state.future = []
                                auth = st.session_state.get('ui_auth', {"enabled": False, "role": "editor"})
                                write_audit(auth.get("role", "editor"), "apply_cleaning", {"ops": len(st.session_state.get('cleaning_log', []))})
                            st.balloons()
                            st.success("All cleaning operations completed successfully!")

                # Undo/Redo controls
                if st.session_state.cleaning_applied or st.session_state.history:
                    ucol1, ucol2, ucol3 = st.columns(3)
                    with ucol1:
                        if st.button("Undo") and st.session_state.history:
                            current = st.session_state.df_cleaned if st.session_state.cleaning_applied else st.session_state.df_original
                            st.session_state.future.append(current.copy())
                            prev = st.session_state.history.pop()
                            st.session_state.df_cleaned = prev
                            st.session_state.cleaning_applied = True
                            st.success("Undone last change.")
                    with ucol2:
                        if st.button("Redo") and st.session_state.future:
                            current = st.session_state.df_cleaned
                            st.session_state.history.append(current.copy())
                            nxt = st.session_state.future.pop()
                            st.session_state.df_cleaned = nxt
                            st.session_state.cleaning_applied = True
                            st.success("Redone last change.")
                    with ucol3:
                        if st.button("Reset to Original"):
                            st.session_state.history.append((st.session_state.df_cleaned if st.session_state.cleaning_applied else st.session_state.df_original).copy())
                            st.session_state.df_cleaned = st.session_state.df_original.copy()
                            st.session_state.cleaning_applied = False
                            st.session_state.future = []
                            st.success("Reset complete.")
                
                # Show cleaned data if cleaning was applied
                if st.session_state.cleaning_applied:
                    st.markdown("---")
                    st.markdown('<p class="sub-header">Cleaned Dataset</p>', unsafe_allow_html=True)
                    
                    # Comparison metrics
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Before Cleaning:**")
                        before_missing = st.session_state.df_original.isnull().sum().sum()
                        before_dupes = st.session_state.df_original.duplicated().sum()
                        st.metric("Missing Values", before_missing)
                        st.metric("Duplicates", before_dupes)
                    
                    with col2:
                        st.markdown("**After Cleaning:**")
                        after_missing = st.session_state.df_cleaned.isnull().sum().sum()
                        after_dupes = st.session_state.df_cleaned.duplicated().sum()
                        st.metric("Missing Values", after_missing, delta=-(before_missing - after_missing))
                        st.metric("Duplicates", after_dupes, delta=-(before_dupes - after_dupes))
                    
                    # Show cleaned data preview
                    st.markdown("#### Preview of Cleaned Data")
                    st.dataframe(st.session_state.df_cleaned.head(10), use_container_width=True)
                    
                    # Cleaning operation log
                    with st.expander("Cleaning Operation Log", expanded=True):
                        if st.session_state.cleaning_log:
                            for entry in st.session_state.cleaning_log:
                                st.markdown(f"- {entry}")
                            log_text = "\n".join(st.session_state.cleaning_log).encode('utf-8')
                            st.download_button(
                                label="Download Cleaning Log",
                                data=log_text,
                                file_name="cleaning_log.txt",
                                mime="text/plain"
                            )
                        else:
                            st.info("No cleaning operations recorded.")
                    
                    # Export options
                    st.markdown("---")
                    export_data(st.session_state.df_cleaned, filename="cleaned_data")

                    # Executive PDF report
                    with st.expander("Executive PDF Summary"):
                        analyzer = DataAnalyzer(st.session_state.df_original)
                        summary = analyzer.generate_natural_language_summary()
                        quality = analyzer.get_data_quality_score()
                        pdf_bytes = generate_executive_pdf(
                            df_original=st.session_state.df_original,
                            df_cleaned=st.session_state.df_cleaned,
                            suggestions=st.session_state.suggestions or {},
                            summary_text=summary,
                            quality_score=quality,
                        )
                        st.download_button(
                            label="Download Executive PDF",
                            data=pdf_bytes,
                            file_name="data_cleaning_summary.pdf",
                            mime="application/pdf"
                        )

                    # Recipe export (Python / SQL)
                    with st.expander("Export Cleaning Recipe (Python / SQL)", expanded=False):
                        # Include manual edit ops if present
                        ops = st.session_state.get('last_operations', [])
                        if ops:
                            engine = st.selectbox("SQL Engine", ["generic", "postgres", "mysql", "snowflake", "bigquery"], index=1)
                            py_script = recipe_to_python(ops, input_var='df')
                            sql_script = recipe_to_sql(ops, table='your_table', engine=engine)
                            st.download_button("Download Python Recipe", py_script.encode('utf-8'), "cleaning_recipe.py", "text/x-python-script")
                            st.download_button("Download SQL Recipe (template)", sql_script.encode('utf-8'), "cleaning_recipe.sql", "text/plain")
                            # Save recipe to file action
                            save_path = st.text_input("Save Python recipe to path", value="recipe_output.py")
                            if st.button("Save recipe to file"):
                                try:
                                    with open(save_path, "w", encoding="utf-8") as f:
                                        f.write(py_script)
                                    # Audit recipe save
                                    auth = st.session_state.get('ui_auth', {"enabled": False, "role": "editor"})
                                    write_audit(auth.get("role", "editor"), "save_recipe", {"path": save_path, "ops": len(ops)})
                                    st.success(f"Saved recipe to {save_path}")
                                except Exception as e:
                                    st.error(f"Failed to save recipe: {e}")
                        else:
                            st.info("Apply suggestions or save manual edits to generate a recipe.")
            
            with tab2:
                # AI Assistant Chat
                df_to_analyze = st.session_state.df_cleaned if st.session_state.cleaning_applied else st.session_state.df_original
                display_ai_chatbot(df_to_analyze)
            
            with tab3:
                # Spreadsheet Editor
                st.info("Tip: Click any cell to edit. Changes are saved when you click 'Save Changes'.")
                df_to_edit = st.session_state.df_cleaned if st.session_state.cleaning_applied else st.session_state.df_original
                edited_df = display_spreadsheet_editor(df_to_edit)
                # If user saved edits, reconstruct manual ops for recipe export
                if st.session_state.cleaning_applied and edited_df is not None and st.session_state.df_cleaned is not None:
                    try:
                        manu_ops = create_manual_edit_ops(st.session_state.df_cleaned, edited_df)
                        if manu_ops:
                            # merge into last_operations
                            prev_ops = st.session_state.get('last_operations', [])
                            st.session_state.last_operations = prev_ops + manu_ops
                    except Exception as e:
                        st.caption(f"Recipe diff note: {e}")
            
            with tab4:
                # Visualizations
                if st.session_state.cleaning_applied:
                    display_visualizations(st.session_state.df_cleaned, title="Visualizations (Cleaned Data)")
                else:
                    display_visualizations(st.session_state.df_original, title="Visualizations (Original Data)")
    
    else:
        # Welcome screen
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(
                """
                ### Getting Started
                
                1. **Upload** your dataset (up to 500MB!) using the sidebar
                2. **Review** AI-powered data analysis and suggestions
                3. **Chat** with AI assistant for personalized guidance
                4. **Edit** your data in spreadsheet mode
                5. **Visualize** with advanced analytics
                6. **Download** your cleaned dataset
                
                ---
                
                ### Supported Formats
                - CSV (`.csv`) - up to 500MB
                - Excel (`.xlsx`, `.xls`) - up to 500MB  
                - JSON (`.json`) - up to 500MB
                
                ---
                
                ### Pro Features

                **AI Assistant Chat**
                - Ask questions in natural language
                - Get personalized data insights
                - ChatGPT-powered responses
                - Best practices recommendations
                
                **Spreadsheet Editor**
                - Click to edit any cell
                - Add/delete rows dynamically
                - Real-time data manipulation
                - Excel-like interface
                
                **Advanced Analytics**
                - Correlation heatmaps
                - Pattern detection (emails, URLs, phones)
                - Quality scoring algorithm
                - Statistical deep-dive
                
                ---
                
                ### Use Cases
                - Academic research projects

                - Business intelligence preparation

                - Machine learning preprocessing

                - Large dataset cleaning

                - Interactive data exploration
                """
            )
