"""
Wine Recommendation Engine - Streamlit UI
Run with: streamlit run wine-recommender/ui/streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add wine-recommender directory to path for imports
wine_rec_dir = Path(__file__).parent.parent
sys.path.insert(0, str(wine_rec_dir))

from models import UserPreferences
from agents import get_wine_recommendations
from utils import STREAMLIT_WELCOME, STREAMLIT_EXAMPLES

# Page config
st.set_page_config(
    page_title="Wine Recommendation Engine",
    page_icon="🍷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Reuse styling from existing wine chatbot
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Clash+Display:wght@300;400;500;600&family=General+Sans:wght@300;400;500&display=swap');

    .stApp {
        background: linear-gradient(180deg, #faf8f5 0%, #f5f0ea 100%);
        color: #2a2a2a;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 800px !important;
    }

    h1 {
        font-family: 'Clash Display', sans-serif !important;
        font-weight: 500 !important;
        font-size: 3rem !important;
        color: #8b4513 !important;
        text-align: center !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
    }

    .subtitle {
        font-family: 'General Sans', sans-serif;
        font-weight: 400;
        font-size: 0.95rem;
        color: #a67c52;
        text-align: center;
        margin-bottom: 2.5rem;
        letter-spacing: 0.02em;
    }

    /* Wine card styling */
    .wine-card {
        background: white;
        border: 1px solid #e8dfd5;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(139, 69, 19, 0.06);
    }

    .wine-name {
        font-family: 'Clash Display', sans-serif;
        font-size: 1.4rem;
        font-weight: 500;
        color: #8b4513;
        margin-bottom: 0.3rem;
    }

    .wine-producer {
        font-family: 'General Sans', sans-serif;
        font-size: 0.95rem;
        color: #a67c52;
        margin-bottom: 1rem;
    }

    .wine-price {
        font-family: 'General Sans', sans-serif;
        font-size: 1.2rem;
        font-weight: 500;
        color: #2a2a2a;
        margin-bottom: 1rem;
    }

    .wine-explanation {
        font-family: 'General Sans', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #4a4a4a;
        margin-bottom: 1rem;
        padding: 1rem;
        background: #fff9f5;
        border-radius: 8px;
        border-left: 3px solid #d4a574;
    }

    .wine-details {
        font-family: 'General Sans', sans-serif;
        font-size: 0.85rem;
        color: #666;
        line-height: 1.5;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #8b4513 0%, #a0522d 100%);
        color: white;
        font-family: 'General Sans', sans-serif;
        font-weight: 500;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
    }

    /* Text input styling */
    .stTextArea > div > div > textarea {
        font-family: 'General Sans', sans-serif;
        border-radius: 12px;
        border: 2px solid #e8dfd5;
    }

    .stTextArea > div > div > textarea:focus {
        border-color: #d4a574;
    }
</style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown("<h1>🍷 Wine Recommender</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI-Powered Sommelier • Powered by WSET Level 3 Knowledge</div>", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.markdown("### Settings")
    debug_mode = st.checkbox("Debug Mode", value=False, help="Show detailed agent outputs")
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This recommendation engine uses:
    - **Agent 1**: WSET knowledge to interpret preferences
    - **Agent 2**: Vector similarity search for wine matching

    All wines linked to Wine.com.
    """)

# Main interface
st.markdown("### Tell us what you're looking for")

# Example buttons
st.markdown("**Quick examples:**")
cols = st.columns(3)
for i, example in enumerate(STREAMLIT_EXAMPLES[:3]):
    if cols[i].button(example, key=f"ex_{i}", use_container_width=True):
        st.session_state.user_description = example

# User input form
with st.form("wine_preferences"):
    description = st.text_area(
        "Describe your wine preferences or occasion",
        value=st.session_state.get("user_description", ""),
        placeholder="e.g., Bold red wine for a steak dinner",
        height=100
    )

    col1, col2 = st.columns(2)
    with col1:
        budget_min = st.number_input("Min Budget ($)", min_value=5, max_value=500, value=10)
    with col2:
        budget_max = st.number_input("Max Budget ($)", min_value=5, max_value=500, value=100)

    col3, col4 = st.columns(2)
    with col3:
        wine_type = st.selectbox(
            "Wine Type (Optional)",
            ["Any", "Red", "White", "Rosé", "Sparkling"]
        )
    with col4:
        food_pairing = st.text_input(
            "Food Pairing (Optional)",
            placeholder="e.g., steak, seafood"
        )

    submit = st.form_submit_button("🔍 Find Wines", use_container_width=True)

# Process recommendations
if submit:
    if not description:
        st.error("Please describe your wine preferences")
    elif budget_min >= budget_max:
        st.error("Max budget must be greater than min budget")
    else:
        # Build UserPreferences
        user_prefs = UserPreferences(
            description=description,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
            food_pairing=food_pairing if food_pairing else None,
            wine_type_pref=wine_type.lower() if wine_type != "Any" else None
        )

        # Show loading spinner
        with st.spinner("🍷 Finding perfect wines for you..."):
            try:
                # Get recommendations
                recommendations = get_wine_recommendations(
                    user_prefs,
                    top_n=3,
                    verbose=debug_mode
                )

                if not recommendations:
                    st.warning("No wines found matching your criteria. Try adjusting your budget or preferences.")
                else:
                    st.success(f"Found {len(recommendations)} perfect wines for you!")
                    st.markdown("---")

                    # Display each wine recommendation
                    for i, rec in enumerate(recommendations, 1):
                        wine = rec.wine

                        # Wine card
                        st.markdown(f"### Recommendation {i}", unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class='wine-card'>
                            <div class='wine-name'>{wine.name}</div>
                            <div class='wine-producer'>{wine.producer} • {wine.region}, {wine.country}</div>
                            <div class='wine-price'>${wine.price_usd:.2f}</div>
                            <div class='wine-explanation'>{rec.explanation}</div>
                            <div class='wine-details'>
                                <strong>{wine.varietal}</strong> • {wine.body.capitalize()} Body • {wine.wine_type.capitalize()}<br>
                                <strong>Characteristics:</strong> {", ".join(wine.characteristics)}<br>
                                <strong>Flavor Notes:</strong> {", ".join(wine.flavor_notes)}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Buy button
                        st.markdown(f"[🛒 View on Wine.com]({wine.wine_com_url})", unsafe_allow_html=True)

                        if debug_mode:
                            st.markdown(f"**Relevance Score:** {rec.relevance_score:.3f}")

                        st.markdown("")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                if debug_mode:
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #a67c52; font-size: 0.85rem; font-family: "General Sans", sans-serif;'>
    Built with WSET Level 3 knowledge • Powered by OpenAI & Pinecone
</div>
""", unsafe_allow_html=True)
