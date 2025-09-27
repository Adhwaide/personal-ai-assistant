import time
import requests
import psutil
import json

def check_system_performance():
    """Check system resources and AI model performance"""
    
    print("🔧 System Performance Check")
    print("=" * 40)
    
    # Check system resources
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"💻 CPU Usage: {cpu_usage}%")
    print(f"🧠 RAM Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)")
    print(f"💾 Available RAM: {memory.available // (1024**3)}GB")
    
    # Check if system is under stress
    if cpu_usage > 80:
        print("⚠️  HIGH CPU USAGE - This will slow down AI responses")
    if memory.percent > 85:
        print("⚠️  HIGH MEMORY USAGE - AI model might use slow swap memory")
    
    # Check Ollama models
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"\n🤖 Available AI Models: {len(models)}")
            
            for model in models:
                name = model['name']
                size_gb = model['size'] / (1024**3)
                print(f"  • {name}: {size_gb:.1f}GB")
                
                # Recommend based on size and system
                if '3b' in name.lower():
                    print(f"    ✅ RECOMMENDED for your system")
                elif '7b' in name.lower():
                    if memory.available < 6 * (1024**3):  # Less than 6GB available
                        print(f"    ⚠️  May be too large for your system")
                    else:
                        print(f"    🟡 Should work but slower")
                elif any(x in name.lower() for x in ['13b', '30b', '70b']):
                    print(f"    ❌ TOO LARGE for your system")
    except:
        print("❌ Cannot connect to Ollama")
        return
    
    # Test AI response speed
    print(f"\n⏱️  Testing AI Response Speed...")
    test_models = ['phi3.5:3.8b', 'llama3.2:3b']
    
    for model in test_models:
        try:
            print(f"Testing {model}...")
            start_time = time.time()
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': model,
                    'prompt': 'Say hello in one sentence.',
                    'stream': False
                },
                timeout=60
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                print(f"  ✅ {model}: {response_time:.1f} seconds")
                if response_time < 10:
                    print(f"    🚀 FAST - Great for your system!")
                elif response_time < 30:
                    print(f"    🟡 OKAY - Acceptable speed")
                else:
                    print(f"    🐌 SLOW - Consider switching models")
            else:
                print(f"  ❌ {model}: Failed to respond")
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ {model}: TIMEOUT (>60 seconds) - Too slow!")
        except Exception as e:
            print(f"  ❌ {model}: Not available")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 40)
    
    if memory.available < 4 * (1024**3):  # Less than 4GB available
        print("🔴 LOW MEMORY:")
        print("  • Close other applications")
        print("  • Use phi3.5:3.8b model (smaller, faster)")
        print("  • Turn OFF continuous listening")
    elif memory.available < 6 * (1024**3):  # 4-6GB available
        print("🟡 MODERATE MEMORY:")
        print("  • llama3.2:3b should work")
        print("  • Use continuous listening sparingly")
        print("  • Close unnecessary browser tabs")
    else:
        print("🟢 GOOD MEMORY:")
        print("  • llama3.2:3b or llama3.2:7b should work")
        print("  • All features should work smoothly")
    
    if cpu_usage > 70:
        print("\n🔴 HIGH CPU USAGE:")
        print("  • Close other applications")
        print("  • Turn OFF continuous listening")
        print("  • Consider restarting your computer")

def optimize_assistant_settings():
    """Generate optimized settings for the assistant"""
    
    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count()
    
    print(f"\n⚙️ OPTIMIZED SETTINGS:")
    print("=" * 40)
    
    # Model recommendation
    if memory.available < 4 * (1024**3):
        recommended_model = "phi3.5:3.8b"
        print(f"🤖 Recommended Model: {recommended_model}")
        print("   Reason: Lightweight, fast on your system")
    else:
        recommended_model = "llama3.2:3b"
        print(f"🤖 Recommended Model: {recommended_model}")
        print("   Reason: Good balance of capability and speed")
    
    # Voice settings
    print(f"\n🎤 Voice Settings:")
    if memory.available < 3 * (1024**3) or psutil.cpu_percent() > 80:
        print("  • Continuous Listening: OFF")
        print("  • Voice Responses: Use sparingly")
        print("  • Reason: Preserve system resources")
    else:
        print("  • Continuous Listening: Use when needed")
        print("  • Voice Responses: Can be enabled")
        print("  • Reason: System can handle voice processing")
    
    # General settings
    print(f"\n⚡ Performance Tips:")
    print("  • Close unnecessary browser tabs")
    print("  • Use text input for complex questions")
    print("  • Use voice input for simple queries")
    print("  • Restart assistant if it becomes slow")
    
    return recommended_model

if __name__ == "__main__":
    check_system_performance()
    recommended_model = optimize_assistant_settings()
    
    print(f"\n🚀 TO APPLY RECOMMENDATIONS:")
    print("=" * 40)
    print(f"1. Install faster model:")
    print(f"   ollama pull {recommended_model}")
    print(f"2. Update your assistant code to use: {recommended_model}")
    print(f"3. Adjust voice settings based on recommendations above")