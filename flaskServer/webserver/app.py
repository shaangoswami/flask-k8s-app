from flask import Flask, render_template, request, jsonify
from datetime import datetime
import requests


app = Flask(__name__)

# In-memory storage (resets on restart - no database needed!)
visitors = []
messages = []

@app.route('/')
def home():
    """Home page"""
    # Log visitor
    visitor_ip = request.remote_addr
    visit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visitors.append({'ip': visitor_ip, 'time': visit_time})
    url = "https://api.github.com/repos/shaangoswami/flask-k8s-app/commits"
    response = requests.get(url)

    commits = [
        f"{c['sha'][:7]} - {c['commit']['message']}"
        for c in response.json()[:5]
    ]
    
    return render_template('index.html', commits=commits)

@app.route('/api/stats')
def get_stats():
    """Get visitor statistics"""
    return jsonify({
        'visitors': len(visitors),
        'status': 'connected'
    })

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission"""
    try:
        data = request.get_json()
        message_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'message': data.get('message'),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        messages.append(message_data)
        
        return jsonify({
            'success': True,
            'message': 'Message received successfully!'
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/messages')
def get_messages():
    """Get all messages"""
    return jsonify({
        'success': True,
        'messages': messages[-10:]  # Last 10 messages
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'visitors': len(visitors),
        'messages': len(messages)
    }), 200

@app.route('/api/info')
def app_info():
    """Application information"""
    return jsonify({
        'app': 'Flask Web Application',
        'version': '1.0',
        'python_version': '3.11',
        'deployed_on': 'Kubernetes (MicroK8s)',
        'total_visitors': len(visitors),
        'total_messages': len(messages)
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Flask Application Starting...")
    print("=" * 60)
    print("📍 Running on: http://0.0.0.0:5000")
    print("🌐 NodePort Access: http://10.20.4.221:30080")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
