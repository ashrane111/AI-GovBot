import streamlit as st
import aiohttp
import asyncio
import os
import sys
import json
import hashlib
import base64
import sqlite3
from typing import Dict, List, Tuple
from contextlib import closing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define config file path
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'frontend_config.json')

# Define SQLite database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_credentials.db')

# Define custom CSS for better styling
def set_custom_style():
    st.markdown("""
    <style>
        /* Main app styling */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #1E3A8A;
            color: white;
            border-radius: 6px;
            padding: 0.25rem 1rem;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #2563EB;
            color: white;
        }
        
        /* Form fields */
        .stTextInput > div > div > input {
            border-radius: 6px;
        }
        
        /* Chat message styling */
        .stChatMessage {
            border-radius: 10px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f1f5f9;
        }
        
        /* Success messages */
        .stSuccess {
            background-color: #d1fae5;
            color: #065f46;
            padding: 0.75rem;
            border-radius: 6px;
        }
        
        /* Error messages */
        .stError {
            background-color: #fee2e2;
            color: #b91c1c;
            padding: 0.75rem;
            border-radius: 6px;
        }
        
        /* Info messages */
        .stInfo {
            background-color: #e0f2fe;
            color: #0369a1;
            padding: 0.75rem;
            border-radius: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

# Default admin credentials
DEFAULT_USERS = {
    "admin": {
        "username": "admin",
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    }
}

# Initialize SQLite database
def initialize_db():
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            # Create users table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """)
            
            # Create chats table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
            """)
            
            # Create messages table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
            )
            """)
            
            conn.commit()
            # Insert default admin user if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("admin",))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                               ("admin", DEFAULT_USERS["admin"]["password"], DEFAULT_USERS["admin"]["role"]))
                conn.commit()

# Load user credentials from SQLite
def load_credentials() -> Dict:
    users = {}
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT username, password, role FROM users")
            for row in cursor.fetchall():
                users[row[0]] = {"username": row[0], "password": row[1], "role": row[2]}
    return users

# Add a new user to SQLite
def add_user(username: str, password: str, role: str) -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                               (username, hashlib.sha256(password.encode()).hexdigest(), role))
                conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Delete a user from SQLite
def delete_user(username: str) -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

BACKEND_BASE_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_BASE_URL}/answer_query"

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

# Authentication functions
def verify_password(username: str, password: str) -> bool:
    """Verify the password against stored hash"""
    users = load_credentials()
    if username in users:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return users[username]["password"] == hashed_password
    return False

def login_form():
    """Display the login form and handle authentication"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Function to get base64 encoded image
        def get_img_as_base64(file_path):
            with open(file_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
                
        # Path to the logo image - Fix the path to point to assets at the project root
        logo_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets/images/logo_no_name.png'))
        
        # Get base64 encoded image if file exists
        logo_base64 = ""
        try:
            logo_base64 = get_img_as_base64(logo_path)
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="H.A.R.V.E.Y Logo" style="height:60px; margin-bottom:10px;"><br>'
            st.markdown(f"<div style='text-align: center;'>{logo_html}</div>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center; font-size:2.2rem; color:#1E3A8A; margin-top:0;'>H.A.R.V.E.Y</h1>", unsafe_allow_html=True)
        except Exception as e:
            # Fallback to emoji if image not found
            print(f"Error loading logo: {e}")
            st.title("⚖️ H.A.R.V.E.Y")
            
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>AI Government Assistant</h3>", unsafe_allow_html=True)
        
        # Create tabs for login and signup with better styling
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "Login"
        
        # Check if we should switch to login tab after successful signup
        if "switch_to_login" in st.session_state and st.session_state.switch_to_login:
            st.session_state.active_tab = "Login"
            st.session_state.switch_to_login = False
        
        # Use the saved active tab
        tab1, tab2 = st.tabs(["🔑 Login", "✏️ Sign Up"])
        
        with tab1:
            # Add some space at the top
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            
            # Display a nicer login form
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                # Add some space before the button
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                
                # Center the login button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    elif verify_password(username, password):
                        # Add a spinner for a better transition experience
                        with st.spinner("Logging in..."):
                            # Small delay for better UX
                            import time
                            time.sleep(0.5)
                            
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            # Add a success message that will be shown after rerun
                            st.session_state.login_message = f"Welcome, {username}!"
                            st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            # Add info about default credentials in a nicer way
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            st.info("Default credentials: admin / admin123")
        
        with tab2:
            # Update session state when user clicks on Sign Up tab
            st.session_state.active_tab = "Sign Up"
            signup_form()

def signup_form():
    """Display the signup form and handle new user registration"""
    # Add some space at the top
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    with st.form("signup_form", clear_on_submit=True):
        st.subheader("Create a New Account")
        
        new_username = st.text_input("Choose a Username", placeholder="Enter desired username")
        new_password = st.text_input("Choose a Password", type="password", placeholder="Enter secure password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        
        # Add some space before the button
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        
        # Center the signup button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit_signup = st.form_submit_button("Sign Up", use_container_width=True)
        
        if submit_signup:
            if not new_username or not new_password:
                st.error("Please provide both username and password")
                return
                
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return
                
            users = load_credentials()
            if new_username in users:
                st.error("Username already exists. Please choose a different one.")
                return
                
            # Add the new user with default role as 'user'
            if add_user(new_username, new_password, "user"):
                try:
                    with st.spinner("Creating your account..."):
                        # Small delay for better UX
                        import time
                        time.sleep(0.5)
                        
                        st.success("Account created successfully! Redirecting to login...")
                        
                        # Set a session state to switch tabs
                        st.session_state.switch_to_login = True
                        
                        # Small delay before redirect
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error creating account: {e}")
            else:
                st.error("Error: Username already exists.")

def show_login_message():
    """Show login success message and clear it after display"""
    if "login_message" in st.session_state:
        st.success(st.session_state.login_message)
        del st.session_state.login_message

def logout():
    """Handle user logout"""
    if st.sidebar.button("Logout"):
        # Clear all session state except messages to preserve chat history
        for key in list(st.session_state.keys()):
            if key != "messages":
                del st.session_state[key]
        st.rerun()

def user_management():
    """Handle user management for admin users"""
    users = load_credentials()
    
    # Create tabs for user listing and adding users
    tab1, tab2 = st.tabs(["Current Users", "Add New User"])
    
    with tab1:
        # Display existing users in a more structured way
        if users:
            # Create a header row
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.markdown("**Username**")
            col2.markdown("**Role**")
            col3.markdown("**Actions**")
            
            # Add a separator
            st.markdown("<hr style='margin: 5px 0; padding: 0'>", unsafe_allow_html=True)
            
            # List all users
            for username, user_data in users.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(username)
                col2.write(user_data.get("role", "user"))
                
                # Don't allow deleting the admin user who is currently logged in
                if username != st.session_state.username:
                    if col3.button("🗑️", key=f"delete_{username}", help="Delete this user"):
                        if delete_user(username):
                            st.success(f"User {username} deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error deleting user {username}.")
        else:
            st.info("No users found.")
    
    with tab2:
        # Form for adding new users
        with st.form("add_user_form"):
            st.subheader("Add New User")
            new_username = st.text_input("Username", placeholder="Enter username")
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
            new_role = st.selectbox("Role", ["user", "admin"])
            
            # Center the add user button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit_user = st.form_submit_button("Add User", use_container_width=True)
            
            if submit_user:
                if not new_username or not new_password:
                    st.error("Please provide both username and password.")
                    return
                    
                if add_user(new_username, new_password, new_role):
                    with st.spinner("Adding user..."):
                        st.success(f"User {new_username} added successfully!")
                        # Small delay for feedback
                        import time
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("Error: Username already exists.")

# Chat history management functions
def create_new_chat(username, title=None):
    """Create a new chat for the user and return the chat_id"""
    if not title:
        # Generate a title based on timestamp
        import datetime
        title = f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "INSERT INTO chats (username, title) VALUES (?, ?)",
                    (username, title)
                )
                chat_id = cursor.lastrowid
                conn.commit()
                return chat_id
    except Exception as e:
        st.error(f"Error creating new chat: {e}")
        return None

def get_user_chats(username):
    """Get all chats for a user"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "SELECT chat_id, title, created_at FROM chats WHERE username = ? ORDER BY created_at DESC",
                    (username,)
                )
                return cursor.fetchall()
    except Exception as e:
        st.error(f"Error retrieving user chats: {e}")
        return []

def get_chat_messages(chat_id):
    """Get all messages for a specific chat"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp",
                    (chat_id,)
                )
                messages = []
                for role, content in cursor.fetchall():
                    messages.append({"role": role, "content": content})
                return messages
    except Exception as e:
        st.error(f"Error retrieving chat messages: {e}")
        return []

def save_message(chat_id, role, content):
    """Save a new message to the database"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                    (chat_id, role, content)
                )
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

def update_chat_title(chat_id, new_title):
    """Update the title of a chat"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "UPDATE chats SET title = ? WHERE chat_id = ?",
                    (new_title, chat_id)
                )
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Error updating chat title: {e}")
        return False

def delete_chat(chat_id):
    """Delete a chat and all its messages"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                # Delete messages first (foreign key constraint)
                cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
                # Then delete the chat
                cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Error deleting chat: {e}")
        return False

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Government AI Assistant",
        page_icon="⚖️",
        layout="centered"
    )

    # Apply custom styling
    set_custom_style()

    # Initialize SQLite database
    initialize_db()

    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Check if user is logged in
    if not st.session_state.logged_in:
        login_form()
        return
    
    # Show success message if just logged in
    show_login_message()

    # Function to get base64 encoded image
    def get_img_as_base64(file_path):
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
            
    # Path to the logo image - Fix the path to point to assets at the project root
    logo_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets/images/logo_no_name.png'))
    
    # Get base64 encoded image if file exists
    logo_base64 = ""
    try:
        logo_base64 = get_img_as_base64(logo_path)
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="H.A.R.V.E.Y Logo" style="height:70px; margin-right:10px; vertical-align:middle;">'
    except Exception as e:
        # Fallback to emoji if image not found
        print(f"Error loading logo in main: {e}")
        logo_html = '⚖️'

    # Set up the page with improved title styling
    st.markdown(f"""
    <div style='text-align: center;'>
        <div>
            {logo_html}
            <span style='font-size:2.5rem; font-weight:600; color:#1E3A8A; vertical-align:middle;'>H.A.R.V.E.Y</span>
        </div>
        <h3 style='color:#4B5563; font-weight:500; margin-top:5px;'>Your AI Government Policy Assistant</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a subtle separator
    st.markdown("<hr style='margin: 10px 0 30px 0; border: none; height: 1px; background-color: #f0f0f0;'>", unsafe_allow_html=True)

    # API endpoint from config
    API_URL = CHAT_ENDPOINT

    # Initialize chat_id if not in session state
    if "active_chat_id" not in st.session_state:
        # Check if user has existing chats
        user_chats = get_user_chats(st.session_state.username)
        if user_chats:
            # Use the most recent chat
            st.session_state.active_chat_id = user_chats[0][0]
            # Load messages from this chat
            st.session_state.messages = get_chat_messages(st.session_state.active_chat_id)
        else:
            # Create a new chat
            new_chat_id = create_new_chat(st.session_state.username)
            st.session_state.active_chat_id = new_chat_id
            st.session_state.messages = []

    # Sidebar configuration
    with st.sidebar:
        # User profile section with avatar
        st.markdown(f"""
        <div style='background-color: #e0f2fe; border-radius: 10px; padding: 15px; margin-bottom: 20px;'>
            <div style='display: flex; align-items: center;'>
                <div style='background-color: #1E3A8A; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 20px;'>
                    {st.session_state.username[0].upper()}
                </div>
                <div>
                    <div style='font-weight: bold;'>{st.session_state.username}</div>
                    <div style='font-size: 12px; color: #666;'>{load_credentials()[st.session_state.username].get("role", "user")}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat history section
        st.subheader("💬 Chat History")
        
        # New Chat button
        if st.button("➕ New Chat", key="new_chat"):
            # Create new chat in database
            new_chat_id = create_new_chat(st.session_state.username)
            if new_chat_id:
                st.session_state.active_chat_id = new_chat_id
                st.session_state.messages = []
                st.rerun()
        
        # List existing chats
        user_chats = get_user_chats(st.session_state.username)
        if user_chats:
            st.write("Select a conversation:")
            
            # Add scrollable container for chat history
            with st.container(height=300, border=False):
                for chat_id, title, created_at in user_chats:
                    # Format the chat item
                    col1, col2 = st.columns([4, 1])
                    # Highlight active chat
                    is_active = chat_id == st.session_state.active_chat_id
                    bg_color = "#dbeafe" if is_active else "transparent"
                    
                    # Create a clickable chat item
                    with col1:
                        chat_button = st.button(
                            title,
                            key=f"chat_{chat_id}",
                            use_container_width=True,
                            help=f"Created on: {created_at}"
                        )
                        if chat_button:
                            st.session_state.active_chat_id = chat_id
                            st.session_state.messages = get_chat_messages(chat_id)
                            st.rerun()
                    
                    # Delete button for this chat
                    with col2:
                        delete_btn = st.button("🗑️", key=f"del_{chat_id}", help="Delete this chat")
                        if delete_btn:
                            if delete_chat(chat_id):
                                # If the deleted chat was active, set active_chat_id to None
                                if chat_id == st.session_state.active_chat_id:
                                    if len(user_chats) > 1:
                                        # Find another chat to set as active
                                        for other_chat in user_chats:
                                            if other_chat[0] != chat_id:
                                                st.session_state.active_chat_id = other_chat[0]
                                                st.session_state.messages = get_chat_messages(other_chat[0])
                                                break
                                    else:
                                        # This was the only chat, create a new one
                                        new_chat_id = create_new_chat(st.session_state.username)
                                        st.session_state.active_chat_id = new_chat_id
                                        st.session_state.messages = []
                                st.rerun()
        else:
            st.info("No conversations yet. Start chatting to create one!")
        
        # Add a cleaner divider
        st.markdown("<hr style='margin: 20px 0; border: none; height: 1px; background-color: #e5e7eb;'>", unsafe_allow_html=True)
        
        # Options section with icons
        st.subheader("⚙️ Options")
        
        # Logout button with icon
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Add user management section for admin users
        users = load_credentials()
        if st.session_state.username in users and users[st.session_state.username].get("role") == "admin":
            st.markdown("<hr style='margin: 20px 0; border: none; height: 1px; background-color: #e5e7eb;'>", unsafe_allow_html=True)
            with st.expander("👥 User Management"):
                user_management()
        
        # About section with more details
        with st.expander("ℹ️ About H.A.R.V.E.Y"):
            st.markdown("""
            **H.A.R.V.E.Y** (Helpful AI Representative for Various Executive Yields) is an AI assistant specialized in government policies, laws, and regulations.
            
            This assistant can answer questions about:
            - Government policies and programs
            - AI governance and regulations
            - Legal frameworks and compliance
            - Public services information
            
            Powered by a retrieval-augmented generation system to provide accurate and up-to-date information.
            """)

    # Container for the chat interface with better styling
    chat_container = st.container()
    with chat_container:
        # Display current chat title if available
        if "active_chat_id" in st.session_state:
            current_chat = next((chat for chat in get_user_chats(st.session_state.username) 
                               if chat[0] == st.session_state.active_chat_id), None)
            # if current_chat:
            #     st.subheader(f"Chat: {current_chat[1]}")
        
        # Create a container for the chat messages with a styled background
        st.markdown("""
        <div style='background-color: #f9fafb; border-radius: 10px; padding: 10px; margin-bottom: 20px;'>
        """, unsafe_allow_html=True)
        
        # Display chat history with improved styling
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="🧑‍💼" if message["role"] == "user" else "🤖"):
                st.markdown(message["content"])
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Get user input with a more descriptive placeholder
    user_query = st.chat_input("Ask H.A.R.V.E.Y about government policies and AI laws...")

    if user_query:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Save message to database
        save_message(st.session_state.active_chat_id, "user", user_query)
        
        # If this is the first message in a chat, update the chat title
        current_chat = next((chat for chat in get_user_chats(st.session_state.username) 
                           if chat[0] == st.session_state.active_chat_id), None)
        if current_chat and current_chat[1].startswith("Chat ") and len(st.session_state.messages) == 1:
            # Use first few words of the query as the chat title
            words = user_query.split()
            new_title = " ".join(words[:4])
            if len(words) > 4:
                new_title += "..."
            update_chat_title(st.session_state.active_chat_id, new_title)
        
        # Display user message
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(user_query)
        
        # Show thinking indicator with a more engaging message
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            
            # More engaging "thinking" message
            import time
            thinking_dots = ["Thinking", "Thinking.", "Thinking..", "Thinking..."]
            for dots in thinking_dots * 2:
                message_placeholder.markdown(f"*{dots}*")
                time.sleep(0.2)
            
            # Run the async API call
            response = asyncio.run(query_api(st.session_state.messages, API_URL))
            
            if response and response["res"] == "success":
                # Extract answer content
                answer_content = response["answer"]["content"]
                
                # Update the assistant's message with a fade-in effect
                message_placeholder.markdown(answer_content)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": answer_content})
                
                # Save assistant message to database
                save_message(st.session_state.active_chat_id, "assistant", answer_content)
            else:
                error_message = "I apologize, but I couldn't process your request at the moment. Please try again later or rephrase your question."
                message_placeholder.markdown(error_message)
                
                # Add error response to history
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                
                # Save error message to database
                save_message(st.session_state.active_chat_id, "assistant", error_message)

if __name__ == "__main__":
    main()