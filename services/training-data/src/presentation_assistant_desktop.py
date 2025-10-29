#!/usr/bin/env python3
"""
AI Presentation Assistant - System Audio Capture
Captures audio from WhatsApp, Google Meet, Zoom, etc.
Works with BlackHole on macOS
"""

import os
import sys
import threading
import wave
import tempfile
from datetime import datetime
from collections import deque
import anthropic
import speech_recognition as sr


class Colors:
    """Terminal colors"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class SystemAudioAssistant:
    """Captures system audio from applications"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        
        self.conversation_history = deque(maxlen=10)
        self.context = "general presentation"
        
        # Try to import soundcard
        try:
            import soundcard as sc
            self.sc = sc
            self.has_soundcard = True
        except ImportError:
            self.has_soundcard = False
    
    def print_header(self):
        """Print application header"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("=" * 80)
        print("🎤 AI PRESENTATION ASSISTANT - System Audio Capture")
        print("=" * 80)
        print(f"{Colors.END}")
        print(f"{Colors.YELLOW}💡 Captures audio from WhatsApp, Google Meet, Zoom, etc.{Colors.END}")
        print(f"{Colors.YELLOW}💡 Requires BlackHole setup on macOS{Colors.END}")
        print()
    
    def check_blackhole(self):
        """Check if BlackHole is installed"""
        if not self.has_soundcard:
            print(f"{Colors.RED}⚠️  soundcard library not installed{Colors.END}")
            print("\nInstall it with: pip install soundcard")
            return False
            
        # List available audio devices
        print(f"{Colors.CYAN}Available audio input devices:{Colors.END}")
        try:
            mics = self.sc.all_microphones(include_loopback=True)
            for i, mic in enumerate(mics):
                print(f"  {i}. {mic.name}")
            
            # Check if BlackHole exists
            blackhole_found = any('blackhole' in mic.name.lower() for mic in mics)
            
            if not blackhole_found:
                print(f"\n{Colors.YELLOW}⚠️  BlackHole not found!{Colors.END}")
                print("\nSetup Instructions:")
                print("1. Install BlackHole: brew install blackhole-2ch")
                print("2. Open 'Audio MIDI Setup' app")
                print("3. Create 'Multi-Output Device' with BlackHole + Speakers")
                print("4. Set Multi-Output as system output")
                print("5. Restart this app")
                print("\nDetailed guide: https://github.com/ExistentialAudio/BlackHole/wiki/Multi-Output-Device")
                return False
            
            return True
            
        except Exception as e:
            print(f"{Colors.RED}Error listing devices: {e}{Colors.END}")
            return False
    
    def setup(self):
        """Setup and get context"""
        self.print_header()
        
        # Check for BlackHole
        if not self.check_blackhole():
            print(f"\n{Colors.RED}Cannot continue without proper audio setup.{Colors.END}")
            sys.exit(1)
        
        print(f"\n{Colors.BOLD}Setup:{Colors.END}")
        context_input = input(f"Enter presentation topic (press Enter for 'general presentation'): ").strip()
        if context_input:
            self.context = context_input
        
        print(f"\n{Colors.GREEN}✓ Topic set: {self.context}{Colors.END}")
        
        # Check API key
        if not self.client:
            print(f"\n{Colors.YELLOW}⚠️  No API key found (transcription only mode){Colors.END}")
            print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        
        # Select audio device
        mics = self.sc.all_microphones(include_loopback=True)
        print(f"\n{Colors.BOLD}Select audio input device:{Colors.END}")
        
        # Auto-select BlackHole if found
        blackhole_idx = None
        for i, mic in enumerate(mics):
            if 'blackhole' in mic.name.lower():
                blackhole_idx = i
                break
        
        if blackhole_idx is not None:
            device_idx = blackhole_idx
            print(f"Auto-selected: {mics[device_idx].name}")
        else:
            device_input = input(f"Enter device number (or press Enter for default): ").strip()
            device_idx = int(device_input) if device_input else 0
        
        self.selected_mic = mics[device_idx]
        print(f"{Colors.GREEN}✓ Using: {self.selected_mic.name}{Colors.END}")
        
        input("\nPress Enter to start listening...")
    
    def detect_question(self, text):
        """Detect if text is a question"""
        text_lower = text.lower()
        
        if '?' in text:
            return True
        
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 
                         'can you', 'could you', 'would you', 'is it', 'are you']
        
        for word in question_words:
            if text_lower.startswith(word) or f" {word} " in text_lower:
                return True
        
        return False
    
    def print_transcript(self, text, is_question):
        """Print transcript with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_question:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}👤 CLIENT [{timestamp}]{Colors.END}")
            print(f"{Colors.YELLOW}{text}{Colors.END}")
        else:
            print(f"\n{Colors.BLUE}{Colors.BOLD}🎤 YOU [{timestamp}]{Colors.END}")
            print(f"{Colors.BLUE}{text}{Colors.END}")
    
    def get_ai_suggestion(self, question_text):
        """Get AI suggestion for a question"""
        if not self.client:
            return
        
        print(f"\n{Colors.CYAN}🤔 Generating AI suggestion...{Colors.END}")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{Colors.GREEN}{'=' * 80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}💡 AI SUGGESTION [{timestamp}]{Colors.END}")
        print(f"{Colors.GREEN}{'-' * 80}{Colors.END}")
        
        try:
            history_text = "\n".join([
                f"{item['speaker']}: {item['text']}"
                for item in self.conversation_history
            ])
            
            prompt = f"""You are an AI presentation assistant helping during a client call.

MEETING TOPIC: {self.context}

CLIENT QUESTION/COMMENT:
{question_text}

CONVERSATION HISTORY:
{history_text}

TASK: Provide clear, actionable guidance for responding.

FORMAT:

**What They Said:**
[Brief summary in 1 sentence]

**Your Response:**
• [First key point to mention]
• [Second key point to mention]
• [Third key point to mention]

**Key Takeaway:**
[One sentence main message]

Keep it SHORT, CLEAR, and ACTIONABLE."""

            with self.client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    print(text, end='', flush=True)
            
            print()
            print(f"{Colors.GREEN}{'=' * 80}{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.RED}⚠️  AI Error: {str(e)}{Colors.END}")
            print(f"{Colors.GREEN}{'=' * 80}{Colors.END}")
    
    def process_audio_chunk(self, audio_data, sample_rate):
        """Process audio chunk and transcribe"""
        try:
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_filename = tmp_file.name
                
                # Write WAV file
                with wave.open(tmp_filename, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data.tobytes())
            
            # Recognize using speech_recognition
            with sr.AudioFile(tmp_filename) as source:
                audio = self.recognizer.record(source)
                
            try:
                text = self.recognizer.recognize_google(audio)
                
                # Detect if it's a question
                is_question = self.detect_question(text)
                
                # Print transcript
                self.print_transcript(text, is_question)
                
                # Add to history
                speaker = "👤 Client" if is_question else "🎤 You"
                self.conversation_history.append({
                    'speaker': speaker,
                    'text': text,
                    'is_question': is_question
                })
                
                # Trigger AI if it's a question
                if is_question:
                    threading.Thread(target=self.get_ai_suggestion, args=(text,), daemon=True).start()
                
            except sr.UnknownValueError:
                pass  # Speech not understood
            except sr.RequestError as e:
                print(f"{Colors.RED}⚠️  Recognition error: {str(e)}{Colors.END}")
            
            # Clean up temp file
            os.unlink(tmp_filename)
            
        except Exception as e:
            print(f"{Colors.RED}⚠️  Processing error: {str(e)}{Colors.END}")
    
    def listen_loop(self):
        """Continuous listening loop for system audio"""
        try:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ LISTENING to system audio...{Colors.END}")
            print(f"{Colors.YELLOW}(Press Ctrl+C to stop){Colors.END}\n")
            
            import numpy as np
            
            # Recording parameters
            sample_rate = 16000
            chunk_duration = 3  # Process every 3 seconds
            
            with self.selected_mic.recorder(samplerate=sample_rate) as mic:
                while self.is_listening:
                    # Record chunk
                    data = mic.record(numframes=sample_rate * chunk_duration)
                    
                    # Convert to 16-bit PCM
                    audio_data = (data[:, 0] * 32767).astype('<h')
                    
                    # Check if there's actual audio (not silence)
                    if np.abs(audio_data).mean() > 100:  # Noise threshold
                        threading.Thread(
                            target=self.process_audio_chunk, 
                            args=(audio_data, sample_rate), 
                            daemon=True
                        ).start()
                        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Stopping...{Colors.END}")
            self.is_listening = False
        except Exception as e:
            print(f"{Colors.RED}⚠️  Error: {str(e)}{Colors.END}")
            self.is_listening = False
    
    def start(self):
        """Start the assistant"""
        try:
            self.is_listening = True
            self.listen_loop()
            
        except Exception as e:
            print(f"{Colors.RED}⚠️  Error: {str(e)}{Colors.END}")
            sys.exit(1)
    
    def run(self):
        """Main run method"""
        self.setup()
        self.start()


def main():
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    # Create and run assistant
    assistant = SystemAudioAssistant(api_key)
    assistant.run()


if __name__ == '__main__':
    main()