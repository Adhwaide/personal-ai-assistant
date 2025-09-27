import streamlit as st
import requests
import speech_recognition as sr
import pyttsx3
import time
from datetime import datetime

# Fast, lightweight assistant with minimal overhead
class FastAssistant:
    def __init__(self):
        self.voice_handler = self.setup_voice()
        
    def setup_voice(self):
        """Setup voice components"""
        try:
            recognizer = sr.Recognizer()
            tts_engine = pyttsx3.init()
            return {
                'recognizer': recognizer,
                'microphone': sr.Microphone(),
                'tts_engine': tts_engine
            }
        except:
            return None
    
    def quick_response(self, prompt):
        """Get quick response from AI"""
        try:
            start_time = time.time()
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'phi3.5:3.8b',
                    'prompt': f"You are a helpful AI assistant. Respond concisely to: {prompt}",
                    'stream': False,
                    'options': {
                        'temperature': 0.3,  # Lower temperature for faster responses
                        'num_predict': 150,   # Limit response length
                    }
                },
                timeout=30  # 30 second timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()['response']
                return result, response_time
            else:
                return "Sorry, I'm having trouble connecting to my AI model.", response_time
                
        except requests.exceptions.Timeout:
            return "Response took too long. Try a simpler question.", 30.0
        except Exception as e:
            return f"Error: {str(e)}", 0
    
    def listen_once(self):
        """Quick voice input"""
        if not self.voice_handler:
            return "Voice not available"
        
        try:
            recognizer = self.voice_handler['recognizer']
            microphone = self.voice_handler['microphone']
            
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            with microphone as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            return "No speech detected"
        except sr.UnknownValueError:
            return "Could not understand audio"
        except Exception as e:
            return f"Voice error: {str(e)}"
    
    def speak(self, text):
        """Quick text to speech with better error handling"""
        if not self.voice_handler:
            return False
        
        try:
            engine = self.voice_handler['tts_engine']
            # Clean text for TTS
            clean_text = text.replace("*", "").replace("#", "").replace("`", "")
            
            # Stop any current speech
            try:
                engine.stop()
            except:
                pass
            
            # Try to speak
            engine.say(clean_text)
            engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"TTS Error: {e}")
            # Try to reinitialize engine
            try:
                self.voice_handler['tts_engine'] = pyttsx3.init()
                self.voice_handler['tts_engine'].say(clean_text)
                self.voice_handler['tts_engine'].runAndWait()
                return True
            except:
                return False

# Streamlit App
st.set_page_config(
    page_title="⚡ Fast AI Assistant",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ Fast AI Assistant")
st.caption("Optimized for speed and low memory usage")

# Initialize
if 'assistant' not in st.session_state:
    st.session_state.assistant = FastAssistant()
    st.session_state.messages = []

# Performance indicator
col1, col2 = st.columns(2)
with col1:
    st.metric("Model", "phi3.5:3.8b")
with col2:
    if 'last_response_time' in st.session_state:
        st.metric("Last Response", f"{st.session_state.last_response_time:.1f}s")

# Settings
with st.expander("⚙️ Quick Settings"):
    use_voice_output = st.checkbox("🔊 Voice Responses", value=False)
    show_timing = st.checkbox("⏱️ Show Response Times", value=True)

# Chat Interface
st.subheader("💬 Chat")

# Display messages
for i, message in enumerate(st.session_state.messages[-8:]):  # Show last 8 messages only
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if show_timing and message.get("time"):
            st.caption(f"⏱️ {message['time']:.1f}s")

# Input methods
input_method = st.radio("Input Method:", ["💬 Text", "🎤 Voice"], horizontal=True)

if input_method == "💬 Text":
    # Text input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("⚡ Thinking..."):
                response, response_time = st.session_state.assistant.quick_response(prompt)
                
                st.write(response)
                if show_timing:
                    st.caption(f"⏱️ Response time: {response_time:.1f}s")
                
                # Voice output if enabled
                if use_voice_output:
                    with st.spinner("🔊 Speaking..."):
                        spoke = st.session_state.assistant.speak(response)
                        if not spoke:
                            st.warning("Voice output failed")
        
        # Store response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "time": response_time
        })
        st.session_state.last_response_time = response_time

else:
    # Voice input
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🎤 Listen", type="primary"):
            with st.spinner("🎤 Listening..."):
                voice_input = st.session_state.assistant.listen_once()
                
                if voice_input and "error" not in voice_input.lower() and voice_input != "No speech detected":
                    st.success(f"Heard: '{voice_input}'")
                    
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": voice_input})
                    
                    # Get AI response
                    with st.spinner("⚡ Thinking..."):
                        response, response_time = st.session_state.assistant.quick_response(voice_input)
                        
                        # Store response
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response,
                            "time": response_time
                        })
                        st.session_state.last_response_time = response_time
                        
                        # Auto voice output for voice input
                        if st.session_state.assistant.speak(response):
                            st.success("🔊 Response spoken!")
                        else:
                            st.warning("Voice output failed")
                        
                        st.rerun()
                else:
                    st.error(voice_input)
    
    with col2:
        st.info("Click 'Listen' and speak your question clearly")

# Quick actions
st.subheader("⚡ Quick Actions")
quick_col1, quick_col2, quick_col3 = st.columns(3)

with quick_col1:
    if st.button("👋 Say Hello"):
        with st.spinner("⚡ Responding..."):
            response, response_time = st.session_state.assistant.quick_response("Hello!")
            st.success(f"Response: {response} (⏱️ {response_time:.1f}s)")

with quick_col2:
    if st.button("🕐 What time?"):
        current_time = datetime.now().strftime("%I:%M %p")
        st.success(f"Current time: {current_time}")

with quick_col3:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Performance tips
with st.expander("💡 Performance Tips"):
    st.markdown("""
    **For faster responses:**
    - Close other browser tabs
    - Use shorter questions
    - Turn off voice responses if not needed
    - Restart if responses become slow
    
    **Target response times:**
    - Simple questions: 5-15 seconds
    - Complex questions: 15-30 seconds
    - If >30 seconds: system needs optimization
    """)

# System check
with st.expander("🔧 System Check"):
    if st.button("Test AI Speed"):
        with st.spinner("Testing..."):
            test_response, test_time = st.session_state.assistant.quick_response("Say hello")
            if test_time < 10:
                st.success(f"✅ AI is fast! ({test_time:.1f}s)")
            elif test_time < 20:
                st.warning(f"🟡 AI is okay ({test_time:.1f}s)")
            else:
                st.error(f"🔴 AI is slow ({test_time:.1f}s) - check system resources")
    
    if st.button("Test Voice"):
        if st.session_state.assistant.voice_handler:
            if st.session_state.assistant.speak("Voice test"):
                st.success("✅ Voice working!")
            else:
                st.error("❌ Voice not working")
        else:
            st.error("❌ Voice system not available")