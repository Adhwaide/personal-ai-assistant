import pyttsx3
import json
import os

def test_voice_system():
    """Test and debug voice system"""
    
    print("🔧 Testing Voice System...")
    
    # Test 1: Basic TTS
    print("\n1. Testing Text-to-Speech...")
    try:
        engine = pyttsx3.init()
        
        # Show available voices
        voices = engine.getProperty('voices')
        print(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name} ({voice.id})")
        
        # Test speaking
        engine.say("Voice test successful!")
        engine.runAndWait()
        print("✅ TTS working!")
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return False
    
    # Test 2: Check user profile
    print("\n2. Checking user profile...")
    profile_path = "./assistant_data/user_profile.json"
    
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            voice_enabled = profile.get("voice_response", True)
            print(f"Voice responses in profile: {voice_enabled}")
            
            if not voice_enabled:
                print("⚠️  Voice responses are DISABLED in your profile!")
                print("   This is why you only get text responses.")
                
                # Fix it
                profile["voice_response"] = True
                with open(profile_path, 'w') as f:
                    json.dump(profile, f, indent=2)
                print("✅ Fixed! Voice responses now enabled.")
            else:
                print("✅ Voice responses are enabled in profile")
    else:
        print("⚠️  No user profile found")
    
    # Test 3: Check conversation history
    print("\n3. Checking recent conversations...")
    import sqlite3
    db_path = "./assistant_data/conversations.db"
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get last 5 conversations
        try:
            cursor.execute("""
                SELECT user_input, input_method, output_method 
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            
            conversations = cursor.fetchall()
            print(f"Last {len(conversations)} conversations:")
            
            for i, (user_input, input_method, output_method) in enumerate(conversations):
                print(f"  {i+1}. '{user_input[:30]}...' | Input: {input_method} | Output: {output_method}")
            
        except Exception as e:
            print(f"Error reading conversations: {e}")
        
        conn.close()
    else:
        print("⚠️  No conversation database found")
    
    print("\n" + "="*50)
    print("DIAGNOSIS:")
    print("="*50)
    
    # Check if voice responses should work
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            if profile.get("voice_response", True):
                print("✅ Voice responses SHOULD work")
                print("💡 If they don't, the issue is in the code logic")
            else:
                print("❌ Voice responses are DISABLED")
                print("💡 Enable them in the sidebar settings")
    
    return True

def fix_voice_responses():
    """Force enable voice responses"""
    print("\n🔧 Force enabling voice responses...")
    
    profile_path = "./assistant_data/user_profile.json"
    os.makedirs("./assistant_data", exist_ok=True)
    
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
    else:
        profile = {}
    
    profile["voice_response"] = True
    
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print("✅ Voice responses force-enabled!")
    print("🚀 Restart your assistant and try again")

if __name__ == "__main__":
    print("Voice System Debugger")
    print("=" * 30)
    
    choice = input("\n1. Test voice system\n2. Force enable voice responses\nChoose (1 or 2): ")
    
    if choice == "1":
        test_voice_system()
    elif choice == "2":
        fix_voice_responses()
    else:
        print("Invalid choice")