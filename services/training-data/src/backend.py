#!/usr/bin/env python3
"""
AI Presentation Assistant - Backend Server
Run this to enable AI suggestions in your presentation assistant
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store API key (you'll set this via environment variable or the /set-key endpoint)
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

@app.route('/set-key', methods=['POST'])
def set_key():
    """Set the API key"""
    global API_KEY
    data = request.json
    API_KEY = data.get('api_key', '')
    return jsonify({'success': True, 'message': 'API key set successfully'})

@app.route('/suggest', methods=['POST'])
def get_suggestion():
    """Get AI suggestion from Claude with streaming"""
    if not API_KEY:
        return jsonify({'error': 'API key not set'}), 400
    
    data = request.json
    context = data.get('context', 'general presentation')
    recent_transcript = data.get('recent_transcript', '')
    full_context = data.get('full_context', '')
    
    def generate():
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=API_KEY)
            
            # Use streaming
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""You are an AI presentation assistant helping a presenter respond to audience questions.

PRESENTATION TOPIC: {context}

RECENT CONVERSATION:
{recent_transcript}

TASK: Analyze what was just said and provide clear, actionable guidance.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

**What They Asked:**
[Brief summary in 1 sentence]

**Your Response:**
• [First key point to mention]
• [Second key point to mention]
• [Third key point to mention]

**Key Takeaway:**
[One sentence main message]

Keep it SHORT, CLEAR, and ACTIONABLE. The presenter needs quick guidance."""
                }]
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {text}\n\n"
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error details: {error_details}")
            yield f"data: ERROR: {str(e)}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/suggest-no-stream', methods=['POST'])
def get_suggestion_no_stream():
    """Get AI suggestion from Claude without streaming (fallback)"""
    if not API_KEY:
        return jsonify({'error': 'API key not set'}), 400
    
    data = request.json
    context = data.get('context', 'general presentation')
    recent_transcript = data.get('recent_transcript', '')
    full_context = data.get('full_context', '')
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=API_KEY)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""You are an AI presentation assistant helping a presenter respond to audience questions.

PRESENTATION TOPIC: {context}

RECENT CONVERSATION:
{recent_transcript}

TASK: Analyze what was just said and provide clear, actionable guidance.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

**What They Asked:**
[Brief summary in 1 sentence]

**Your Response:**
• [First key point to mention]
• [Second key point to mention]
• [Third key point to mention]

**Key Takeaway:**
[One sentence main message]

Keep it SHORT, CLEAR, and ACTIONABLE. The presenter needs quick guidance."""
            }]
        )
        
        suggestion = message.content[0].text
        return jsonify({'success': True, 'suggestion': suggestion})
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'running', 'api_key_set': bool(API_KEY)})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI Presentation Assistant Backend Server")
    print("=" * 60)
    print("\n📋 Setup Instructions:")
    print("1. Install dependencies: pip install flask flask-cors anthropic")
    print("2. Set your API key:")
    print("   - Linux/Mac: export ANTHROPIC_API_KEY='your-key-here'")
    print("   - Windows: set ANTHROPIC_API_KEY=your-key-here")
    print("3. Run this script: python backend.py")
    print("4. Open the HTML file in your browser")
    print("\n🌐 Server starting on http://localhost:5000")
    print("=" * 60)
    print()
    
    app.run(debug=True, port=5001, host='0.0.0.0')
