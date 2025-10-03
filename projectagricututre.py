from openaikey import open_ai_key
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# --- Agriculture Knowledge Base ---
agri_data = {
    "Wheat": {
        "season": "Rabi (October-March)",
        "soil": "Loamy soil with good drainage",
        "water": "Moderate irrigation; avoid waterlogging",
        "sowing": "Mid-Oct to Nov; seed rate 100-125 kg/ha",
        "fertilizer": "NPK 120:60:40 kg/ha",
        "harvesting": "March-April when grains are hard and golden",
        "common_issues": "Rust disease, waterlogging, lodging"
    },
    "Rice": {
        "season": "Kharif (June-October) or Rabi in some regions",
        "soil": "Clayey soil with high water retention",
        "water": "Requires standing water in early stages; good drainage later",
        "sowing": "Nursery raising and transplanting after 20-25 days",
        "fertilizer": "Urea, DAP, MOP based on soil test",
        "harvesting": "Oct-Nov when panicles turn golden, grains hard",
        "common_issues": "Blast disease, brown planthopper, sheath blight"
    },
    "Maize": {
        "season": "Both Kharif and Rabi; prefers warm conditions",
        "soil": "Well-drained loam or silty loam",
        "water": "Critical irrigation at tasseling and grain filling",
        "sowing": "June-July (Kharif), seed rate ~20 kg/ha",
        "fertilizer": "NPK 120:60:40 kg/ha; zinc if deficient",
        "harvesting": "Cob dries and husk turns brown; Nov-Dec",
        "common_issues": "Fall armyworm, stem borer, nitrogen deficiency"
    },
    "Sugarcane": {
        "season": "Planting: Feb-April (spring) or Sept-Oct (autumn)",
        "soil": "Fertile loam with good drainage and moisture retention",
        "water": "High water requirement; regular irrigation",
        "sowing": "Setts (2-3 bud pieces) in furrows; proper spacing",
        "fertilizer": "High N requirement; split doses with micronutrients",
        "harvesting": "10-12 months after planting; when brix is optimal",
        "common_issues": "Red rot, smut, borers"
    },
    "Government Schemes": {
        "PM-KISAN": "₹6,000/year direct benefit to eligible farmers (in installments).",
        "Soil Health Card": "Soil nutrient profile with fertilizer recommendations.",
        "Kisan Credit Card": "Working capital loans for agriculture at subsidized rates."
    },
    "Best Practices": {
        "Soil testing": "Test soil every 2-3 years to optimize fertilizer use.",
        "IPM": "Integrated Pest Management—monitor, use traps, bio-control, targeted sprays.",
        "Water management": "Use mulching/drip to reduce water loss and weeds.",
        "Seed quality": "Use certified, high-germination seeds suited to local climate."
    }
}

# --- Helpers to format data for the LLM ---
def format_agri_info(data: dict) -> str:
    formatted = ""
    for item, details in data.items():
        formatted += f"\n\n*{item}*\n"
        if isinstance(details, dict):
            for key, value in details.items():
                formatted += f"- {key.capitalize()}: {value}\n"
        else:
            formatted += f"- Info: {details}\n"
    return formatted

agri_info_text = format_agri_info(agri_data)

# --- LangChain Chat Model ---
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=open_ai_key)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Smart Agriculture Assistant", layout="centered")
st.title("🌾 Smart Agriculture Assistant")
st.markdown("##### Practical guidance on crops, farming practices, and schemes")

# --- Welcome & Examples ---
st.markdown("""
👋 *Welcome!*  
Ask about crop seasons, soil, fertilizer, common issues, or government schemes.  
You can also compare two crops by typing:  
Compare Wheat and Rice
""")

st.markdown("💡 *Try asking:*")
st.markdown("- Best season to grow wheat?")
st.markdown("- Fertilizer for rice?")
st.markdown("- Common issues in maize")
st.markdown("- Tell me about PM-KISAN")
st.markdown("- Compare Wheat and Sugarcane")

st.divider()

# --- Initialize Session State ---
if "messages" not in st.session_state:
    system_prompt = (
        "You are a helpful assistant for farmers and agriculture students. "
        "Use only the following knowledge base to answer questions about crops, seasons, soil, irrigation, fertilizer, sowing, harvesting, common issues, best practices, and government schemes:\n"
        f"{agri_info_text}\n"
        "Rules:\n"
        "- If information is not present above, say 'That information is not available.'\n"
        "- Be concise, practical, and use simple language.\n"
        "- If the user asks to compare two crops, present a clear, side-by-side comparison of available attributes.\n"
    )
    st.session_state.messages = [SystemMessage(content=system_prompt)]

# --- Utilities ---
def normalize_name_map(keys):
    return {k.lower(): k for k in keys}

def compare_items(name1: str, name2: str):
    name_map = normalize_name_map(agri_data.keys())
    k1 = name_map.get(name1.lower())
    k2 = name_map.get(name2.lower())
    if not k1 or not k2:
        return "❌ One or both crop names were not found. Please check the names."

    d1 = agri_data[k1] if isinstance(agri_data[k1], dict) else {}
    d2 = agri_data[k2] if isinstance(agri_data[k2], dict) else {}

    if not d1 or not d2:
        return "❌ Comparison is only supported for crop entries."

    keys = sorted(set(d1.keys()).union(set(d2.keys())))
    md = f"### 📊 Comparison: {k1} vs {k2}\n"
    for key in keys:
        v1 = d1.get(key, "N/A")
        v2 = d2.get(key, "N/A")
        md += f"- *{key.capitalize()}*: {k1} → {v1} | {k2} → {v2}\n"
    return md

def render_item_details(title: str, details: dict):
    st.subheader(title)
    for key, val in details.items():
        st.markdown(f"- *{key.capitalize()}:* {val}")

# --- Browse Section (optional helper for users) ---
# Show a dropdown to browse crop details quickly
crop_like_items = [k for k, v in agri_data.items() if isinstance(v, dict) and ("season" in v or "soil" in v)]
selected = st.selectbox("📂 Browse a crop", ["— Select —"] + sorted(crop_like_items))
if selected != "— Select —":
    render_item_details(selected, agri_data[selected])
    st.divider()

# --- Chat Input ---
user_input = st.text_input("💬 Your Question", key="user_input")

# --- On User Submit ---
if user_input:
    low = user_input.lower().strip()

    # Handle comparison patterns: "compare A and B" or "compare A vs B"
    if low.startswith("compare"):
        temp = low.replace("compare", "").strip()
        if " and " in temp:
            p1, p2 = temp.split(" and ", 1)
        elif " vs " in temp:
            p1, p2 = temp.split(" vs ", 1)
        else:
            p1, p2 = None, None

        if p1 and p2:
            c1 = p1.strip()
            c2 = p2.strip()
            st.markdown(compare_items(c1, c2))
        else:
            st.warning("⚠ Please use: Compare [Crop 1] and [Crop 2]")
    else:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.spinner("Thinking..."):
            response = llm(st.session_state.messages)
        st.session_state.messages.append(response)

# --- Display Chat History ---
for msg in st.session_state.messages[1:]:
    if isinstance(msg, HumanMessage):
        st.markdown(f"🧑 You:** {msg.content}")
    else:
        st.markdown(f"🤖 Bot:** {msg.content}")