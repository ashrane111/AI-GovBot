import streamlit as st
import aiohttp
import asyncio
import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main.config_loader import ConfigLoader

# Define config file path
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'frontend_config.json')

# Load configuration
def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            chat_api = config.get("CHAT_API", {})
            endpoint = chat_api.get("endpoint", "http://localhost:8000")
            chat_response_route = chat_api.get("chat_response_route", "/answer_query/")
            return {
                "chat_endpoint": endpoint + chat_response_route,
            }
    except FileNotFoundError:
        # Create a default config if it doesn't exist
        default_config = {
            "CHAT_API": {
                "endpoint": "http://localhost:8000",
                "chat_response_route": "/answer_query/"
            }
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=4)
        return {
            "chat_endpoint": default_config["CHAT_API"]["endpoint"] + default_config["CHAT_API"]["chat_response_route"],
        }
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {
            "chat_endpoint": "http://localhost:8000/answer_query/",
        }

# Function to call the API
async def query_api(messages, api_url):
    payload = {"messages": messages}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    st.error(f"API Error: Status {response.status}")
                    return None
        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
            return None

def main():
    # Get configuration
    config = load_config()

    # Set page configuration
    st.set_page_config(
        page_title="Government AI Assistant",
        page_icon="🏛️",
        layout="centered"
    )

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Set up the page
    st.title("🏛️ H.A.R.V.E.Y")
    st.subheader("Ask questions about AI Government Laws and Policies")

    # API endpoint from config
    API_URL = config["chat_endpoint"]

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user input
    user_query = st.chat_input("Ask a question about AI laws...")

    if user_query:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Show thinking indicator
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            # Run the async API call
            response = asyncio.run(query_api(st.session_state.messages, API_URL))
            
            if response and response["res"] == "success":
                # Extract answer content
                answer_content = response["answer"]["content"]
                
                # Update the assistant's message
                message_placeholder.markdown(answer_content)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": answer_content})
            else:
                message_placeholder.markdown("Sorry, I couldn't process your request.")

    # Sidebar controls
    st.sidebar.header("Options")

    # Add a button to clear the conversation
    if st.sidebar.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    # Add some helpful context
    with st.sidebar.expander("About"):
        st.write("""
        This AI assistant can answer questions about government policies, 
        programs, and services. It uses a retrieval-augmented generation 
        system to provide accurate and up-to-date information.
        """)

if __name__ == "__main__":
    main()