import os
import json
import sqlite3
import chromadb
from datetime import datetime
import requests
import streamlit as st
from typing import List, Dict
import hashlib
import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import base64
from io import BytesIO
import wave

class VoiceHandler:
    """Handles voice input and output"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        # Try to find a pleasant voice
        for voice in voices:
            if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        self.tts_engine.setProperty('rate', 180)  # Speed
        self.tts_engine.setProperty('volume', 0.9)  # Volume
    
    def listen_once(self, timeout=5, phrase_timeout=1):
        """Listen for a single voice input"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_timeout)
            
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Speech recognition error: {e}"
    
    def speak(self, text):
        """Convert text to speech"""
        try:
            # Clean text for better TTS
            clean_text = text.replace("*", "").replace("#", "")
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
        except Exception as e:
            st.error(f"TTS Error: {e}")
    
    def start_continuous_listening(self):
        """Start continuous listening in background"""
        def listen_worker():
            while self.is_listening:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        text = self.recognizer.recognize_google(audio)
                        self.audio_queue.put(text)
                except:
                    pass
                time.sleep(0.1)
        
        if not self.is_listening:
            self.is_listening = True
            thread = threading.Thread(target=listen_worker, daemon=True)
            thread.start()
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
    
    def get_audio_input(self):
        """Get audio input from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

class PersonalAssistant:
    def __init__(self, name="ARIA", data_dir="./assistant_data"):
        self.name = name
        self.data_dir = data_dir
        self.setup_directories()
        self.setup_database()
        self.setup_memory()
        self.user_profile = self.load_user_profile()
        self.voice_handler = VoiceHandler()
        
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/conversations", exist_ok=True)
        os.makedirs(f"{self.data_dir}/memory", exist_ok=True)
        os.makedirs(f"{self.data_dir}/images", exist_ok=True)
        os.makedirs(f"{self.data_dir}/audio", exist_ok=True)
        
    def setup_database(self):
        """Initialize SQLite database for conversations"""
        self.db_path = f"{self.data_dir}/conversations.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                assistant_response TEXT,
                context_used TEXT,
                mood TEXT,
                topics TEXT,
                input_method TEXT,
                output_method TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def setup_memory(self):
        """Initialize ChromaDB for semantic memory"""
        self.chroma_client = chromadb.PersistentClient(path=f"{self.data_dir}/memory")
        try:
            self.memory_collection = self.chroma_client.get_collection("memories")
        except:
            self.memory_collection = self.chroma_client.create_collection("memories")
    
    def load_user_profile(self) -> Dict:
        """Load or create user profile"""
        profile_path = f"{self.data_dir}/user_profile.json"
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                return json.load(f)
        else:
            default_profile = {
                "name": "",
                "interests": [],
                "communication_style": "friendly",
                "preferred_topics": [],
                "voice_enabled": True,
                "voice_response": True,
                "learning_patterns": {},
                "created_at": datetime.now().isoformat()
            }
            self.save_user_profile(default_profile)
            return default_profile
    
    def save_user_profile(self, profile: Dict):
        """Save user profile to file"""
        profile_path = f"{self.data_dir}/user_profile.json"
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def ollama_request(self, prompt: str, model: str = "llama3.2:3b") -> str:
        """Send request to Ollama API"""
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'top_p': 0.9,
                    }
                }
            )
            if response.status_code == 200:
                return response.json()['response']
            else:
                return "I'm having trouble connecting to my language model. Please check if Ollama is running."
        except Exception as e:
            return f"Connection error: {str(e)}. Please ensure Ollama is installed and running."
    
    def add_to_memory(self, text: str, metadata: Dict = None):
        """Add conversation to semantic memory"""
        if metadata is None:
            metadata = {}
        
        memory_id = hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()
        
        self.memory_collection.add(
            documents=[text],
            metadatas=[{**metadata, "timestamp": datetime.now().isoformat()}],
            ids=[memory_id]
        )
    
    def search_memory(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search semantic memory for relevant information"""
        try:
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except:
            return {"documents": [[]], "metadatas": [[]]}
    
    def analyze_user_input(self, user_input: str) -> Dict:
        """Analyze user input for learning purposes"""
        analysis_prompt = f"""
        Analyze this user message and extract:
        1. Main topics mentioned
        2. Emotional tone (happy, sad, excited, neutral, etc.)
        3. Any personal preferences revealed
        4. Communication style indicators
        
        User message: "{user_input}"
        
        Respond in JSON format:
        {{
            "topics": ["topic1", "topic2"],
            "mood": "mood_description",
            "preferences": ["preference1", "preference2"],
            "style_indicators": ["indicator1", "indicator2"]
        }}
        """
        
        response = self.ollama_request(analysis_prompt)
        try:
            return json.loads(response)
        except:
            return {"topics": [], "mood": "neutral", "preferences": [], "style_indicators": []}
    
    def update_user_profile(self, analysis: Dict):
        """Update user profile based on conversation analysis"""
        if analysis.get("topics"):
            for topic in analysis["topics"]:
                if topic not in self.user_profile["interests"]:
                    self.user_profile["interests"].append(topic)
        
        for topic in analysis.get("topics", []):
            if topic not in self.user_profile["preferred_topics"]:
                self.user_profile["preferred_topics"] = {}
            self.user_profile["preferred_topics"][topic] = self.user_profile["preferred_topics"].get(topic, 0) + 1
        
        self.save_user_profile(self.user_profile)
    
    def generate_response(self, user_input: str, input_method: str = "text") -> tuple[str, str]:
        """Generate response using context and memory"""
        analysis = self.analyze_user_input(user_input)
        relevant_memories = self.search_memory(user_input)
        
        context = ""
        if relevant_memories["documents"][0]:
            context = f"Relevant past conversations:\n"
            for doc in relevant_memories["documents"][0][:2]:
                context += f"- {doc}\n"
        
        # Adapt response style based on input method
        style_note = ""
        if input_method == "voice":
            style_note = "Keep response conversational and natural for voice interaction. Avoid complex formatting."
        
        personality_prompt = f"""
        You are {self.name}, a personal AI assistant. Your personality:
        - Friendly and helpful
        - Remember past conversations  
        - Learn about the user's preferences
        - Be curious and engaging
        {style_note}
        
        User Profile:
        - Name: {self.user_profile.get('name', 'User')}
        - Interests: {', '.join(self.user_profile['interests'][:5])}
        - Communication style: {self.user_profile['communication_style']}
        
        {context}
        
        Current user message ({input_method}): "{user_input}"
        
        Respond naturally as their personal assistant:
        """
        
        response = self.ollama_request(personality_prompt)
        
        # Determine output method
        output_method = "text"
        if self.user_profile.get("voice_response", True) and input_method == "voice":
            output_method = "voice"
            # Speak the response
            threading.Thread(target=self.voice_handler.speak, args=(response,), daemon=True).start()
        
        # Store conversation
        self.store_conversation(user_input, response, analysis, input_method, output_method)
        
        # Add to memory
        self.add_to_memory(f"User: {user_input}\nAssistant: {response}")
        
        # Update user profile
        self.update_user_profile(analysis)
        
        return response, output_method
    
    def store_conversation(self, user_input: str, response: str, analysis: Dict, input_method: str, output_method: str):
        """Store conversation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (timestamp, user_input, assistant_response, context_used, mood, topics, input_method, output_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user_input,
            response,
            "",
            analysis.get("mood", "neutral"),
            json.dumps(analysis.get("topics", [])),
            input_method,
            output_method
        ))
        
        conn.commit()
        conn.close()

def mobile_interface():
    """Mobile-optimized interface"""
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Mobile-specific CSS
    st.markdown("""
    <style>
    .main > div {
        padding: 1rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
    }
    .voice-button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
    }
    .chat-container {
        height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 Personal AI Assistant")
    
    # Initialize assistant
    if 'assistant' not in st.session_state:
        st.session_state.assistant = PersonalAssistant()
        st.session_state.messages = []
        st.session_state.voice_mode = False
        st.session_state.listening = False
    
    # Voice controls
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🎤 Voice", help="Toggle voice mode"):
            st.session_state.voice_mode = not st.session_state.voice_mode
    
    with col2:
        voice_enabled = st.session_state.assistant.user_profile.get("voice_response", True)
        if st.button(f"🔊 {'On' if voice_enabled else 'Off'}", help="Toggle voice responses"):
            st.session_state.assistant.user_profile["voice_response"] = not voice_enabled
            st.session_state.assistant.save_user_profile(st.session_state.assistant.user_profile)
    
    with col3:
        if st.button("🗑️ Clear", help="Clear chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Status indicator
    if st.session_state.voice_mode:
        st.info("🎤 Voice mode active - Speak your message")
    
    # Chat display
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages[-10:]:  # Show last 10 messages on mobile
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message.get("method"):
                    st.caption(f"Via: {message['method']}")
    
    # Input methods
    if st.session_state.voice_mode:
        # Voice input
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🎤 Listen", key="listen_btn"):
                with st.spinner("Listening..."):
                    voice_input = st.session_state.assistant.voice_handler.listen_once(timeout=10)
                    if voice_input and voice_input != "Could not understand audio":
                        process_input(voice_input, "voice")
        
        st.write("Or type your message:")
        text_input = st.text_input("Type here...", key="text_backup")
        if text_input:
            process_input(text_input, "text")
    
    else:
        # Text input
        if prompt := st.chat_input("What would you like to talk about?"):
            process_input(prompt, "text")

def process_input(user_input: str, input_method: str):
    """Process user input and generate response"""
    # Add user message
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "method": input_method
    })
    
    # Generate response
    with st.spinner("Thinking..."):
        response, output_method = st.session_state.assistant.generate_response(user_input, input_method)
    
    # Add assistant response
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "method": output_method
    })
    
    st.rerun()

def desktop_interface():
    """Desktop interface with full features"""
    st.set_page_config(
        page_title="Personal AI Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Your Personal AI Assistant")
    
    # Initialize assistant
    if 'assistant' not in st.session_state:
        st.session_state.assistant = PersonalAssistant()
        st.session_state.messages = []
        st.session_state.continuous_listening = False
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # User profile
        user_name = st.text_input(
            "Your name:", 
            value=st.session_state.assistant.user_profile.get("name", "")
        )
        
        if user_name != st.session_state.assistant.user_profile.get("name", ""):
            st.session_state.assistant.user_profile["name"] = user_name
            st.session_state.assistant.save_user_profile(st.session_state.assistant.user_profile)
        
        # Voice settings
        st.subheader("🎤 Voice Settings")
        
        voice_response = st.checkbox(
            "Enable voice responses", 
            value=st.session_state.assistant.user_profile.get("voice_response", True)
        )
        st.session_state.assistant.user_profile["voice_response"] = voice_response
        
        # Continuous listening
        if st.button("🎤 Start Continuous Listening"):
            if not st.session_state.continuous_listening:
                st.session_state.assistant.voice_handler.start_continuous_listening()
                st.session_state.continuous_listening = True
                st.success("Continuous listening started!")
        
        if st.button("⏹️ Stop Continuous Listening"):
            if st.session_state.continuous_listening:
                st.session_state.assistant.voice_handler.stop_continuous_listening()
                st.session_state.continuous_listening = False
                st.info("Continuous listening stopped")
        
        # Quick voice input
        if st.button("🎤 Quick Voice Input"):
            with st.spinner("Listening..."):
                voice_input = st.session_state.assistant.voice_handler.listen_once(timeout=10)
                if voice_input and voice_input != "Could not understand audio":
                    st.session_state.temp_voice_input = voice_input
                    st.rerun()
        
        # User interests
        st.subheader("Your Interests")
        interests = st.session_state.assistant.user_profile.get("interests", [])
        if interests:
            for interest in interests[:10]:
                st.write(f"• {interest}")
        else:
            st.write("Start chatting to build your interest profile!")
        
        # Statistics
        st.subheader("Statistics")
        conn = sqlite3.connect(st.session_state.assistant.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE input_method = 'voice'")
        voice_conversations = cursor.fetchone()[0]
        conn.close()
        
        st.write(f"Total conversations: {total_conversations}")
        st.write(f"Voice conversations: {voice_conversations}")
        
        if st.button("Clear All Data"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Chat")
        
        # Check for continuous listening input
        if st.session_state.continuous_listening:
            audio_input = st.session_state.assistant.voice_handler.get_audio_input()
            if audio_input:
                process_input(audio_input, "voice")
        
        # Check for temporary voice input
        if hasattr(st.session_state, 'temp_voice_input'):
            voice_text = st.session_state.temp_voice_input
            del st.session_state.temp_voice_input
            process_input(voice_text, "voice")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("method"):
                    st.caption(f"Input: {message['method']}")
        
        # Chat input
        if prompt := st.chat_input("What would you like to talk about?"):
            process_input(prompt, "text")
    
    with col2:
        st.subheader("Voice Controls")
        
        if st.session_state.continuous_listening:
            st.success("🔴 Listening...")
        else:
            st.info("⚪ Not listening")
        
        # Quick actions
        if st.button("📱 Mobile View"):
            st.session_state.mobile_mode = True
            st.rerun()

def main():
    """Main application entry point"""
    # Detect mobile vs desktop
    if 'mobile_mode' not in st.session_state:
        # Simple mobile detection based on viewport
        st.session_state.mobile_mode = False
    
    if st.session_state.get('mobile_mode', False):
        mobile_interface()
        
        # Switch back to desktop
        if st.button("🖥️ Desktop View"):
            st.session_state.mobile_mode = False
            st.rerun()
    else:
        desktop_interface()

if __name__ == "__main__":
    main()