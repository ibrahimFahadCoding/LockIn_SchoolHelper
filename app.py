import streamlit as st

# Custom CSS for LockIn styling
st.markdown(
    """
    <style>
    body {
        background-color: #1e1e2d;
        color: white;
    }
    .stButton>button {
        background-color: #262730;  /* Dark Blue */
        color: white;
        border-radius: 5px;
        font-size: 16px;
    }
    .stTitle {
        color: white;
    }
    .stText {
        color: white;
    }
    .stMarkdown {
        color: white;
    }
    .main-button {
        background-color: #262730;  /* Dark Blue */
        color: white;
        font-size: 18px;
        padding: 15px 40px;
    }
    </style>
    """, unsafe_allow_html=True
)


# Main page content
def app():
    st.title("Welcome to LockIn 🌟")
    st.write("At LockIn, we help you **organize your life** and **boost your productivity** with powerful AI tools.")

    # Introduction text
    st.markdown("""
        **LockIn** offers two amazing AI-powered tools to help you:
        - **AI Notes Generator**: Quickly generate and organize notes from PDF documents.
        - **AI Schedule Planner**: Plan your day effectively with a personalized schedule.
    """)

    st.subheader("🔧 Choose a Tool to Get Started:")

    # Buttons to navigate to the two apps
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📓 AI Notes Generator", key="notes"):
            # Here you can use Streamlit's session state to change page if you use multiple scripts
            st.session_state.page = "notes"

    with col2:
        if st.button("🗓️ AI Schedule Planner", key="scheduler"):
            # Set the app to navigate to the scheduler
            st.session_state.page = "scheduler"

    if 'page' not in st.session_state:
        st.session_state.page = None

    # Redirect based on button press (or custom navigation mechanism)
    if st.session_state.page == "notes":
        # This should be the entry point to your AI Notes Generator script
        st.write("Redirecting to AI Notes Generator...")
        # You could use `st.experimental_rerun()` or other methods to redirect if needed.
        # Alternatively, split your code into two files for app navigation.

    if st.session_state.page == "scheduler":
        # This should be the entry point to your AI Schedule Planner script
        st.write("Redirecting to AI Schedule Planner...")
        # You could use `st.experimental_rerun()` to switch pages in a more complex multi-page app.


if __name__ == "__main__":
    app()
