import streamlit as st
import requests
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Campus Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Chat Interface ---
st.markdown("""
<style>
    .chat-row {
        display: flex;
        margin-bottom: 10px;
    }
    .user-row {
        justify-content: flex-end;
    }
    .assistant-row {
        justify-content: flex-start;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 10px;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.5;
    }
    .user-bubble {
        background-color: #FF4B4B;
        color: white;
        border-bottom-right-radius: 2px;
    }
    .assistant-bubble {
        background-color: #F0F2F6;
        color: black;
        border-bottom-left-radius: 2px;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://127.0.0.1:8000"

# --- Sidebar Configuration ---
with st.sidebar:
    st.title("Settings")
    
    st.markdown("### API Configuration")
    api_base = st.text_input(
        "API base URL", 
        value=st.session_state.api_url,
        help="Enter the base URL of your FastAPI backend (e.g., http://127.0.0.1:8000)"
    )
    
    # Update session state if changed
    if api_base != st.session_state.api_url:
        st.session_state.api_url = api_base.strip().rstrip("/")

    # Health Check Button
    if st.button("Recheck API"):
        try:
            # Explicitly call the root endpoint for health check (GET request)
            health_url = f"{st.session_state.api_url}/"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                st.success("Backend API is reachable.")
            else:
                st.error(f"API returned status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect. Is the backend running?")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### How it works:")
    st.info(
        """
        - **Retrieves** top passages from your Chroma index.
        - **Reranks** them for relevance.
        - **Generates** a grounded answer using Llama-3 via OpenRouter.
        """
    )

# --- Main Chat Interface ---
st.title("🎓 Campus Chatbot")
st.markdown("Ask anything about campus pages, brochures, or syllabi.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask a campus question..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Prepare payload
            payload = {"text": prompt}
            chat_endpoint = f"{st.session_state.api_url}/chat"
            
            with st.spinner("Thinking..."):
                # Send POST request to backend
                response = requests.post(chat_endpoint, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer received.")
                    
                    # Simulate streaming effect
                    for chunk in answer.split():
                        full_response += chunk + " "
                        time.sleep(0.02)
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    
                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    message_placeholder.error(error_msg)
        
        except requests.exceptions.ConnectionError:
            message_placeholder.error("❌ Could not connect to backend. Ensure FastAPI is running.")
        except Exception as e:
            message_placeholder.error(f"❌ An error occurred: {str(e)}")
