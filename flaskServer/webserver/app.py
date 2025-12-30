from flask import Flask, render_template, request, jsonify
import mariadb
import sys
import os

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysqldb'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'me'),
    'password': os.getenv('DB_PASSWORD', 'yourSAFEpassword'),
    'database': os.getenv('DB_NAME', 'student')
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = mariadb.connect(
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database']
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None

def init_db():
    """Initialize database and create tables if they don't exist"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create visitors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ip_address VARCHAR(50),
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create messages table (for contact form)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Database tables initialized successfully")
            cursor.close()
            conn.close()
        except mariadb.Error as e:
            print(f"Error initializing database: {e}")
    else:
        print("⚠️ Could not connect to database for initialization")

@app.route('/')
def home():
    """Home page"""
    # Log visitor
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            ip_address = request.remote_addr
            cursor.execute("INSERT INTO visitors (ip_address) VALUES (?)", (ip_address,))
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error logging visitor: {e}")
    
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Get visitor statistics"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visitors")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return jsonify({'visitors': count, 'status': 'connected'})
        else:
            return jsonify({'visitors': 0, 'status': 'disconnected'})
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'visitors': 0, 'status': 'error'})

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
                (name, email, message)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Message saved successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    except Exception as e:
        print(f"Error submitting contact form: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/messages')
def get_messages():
    """Get all messages (for admin/testing)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, message, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            messages = []
            for (id, name, email, message, created_at) in cursor:
                messages.append({
                    'id': id,
                    'name': name,
                    'email': email,
                    'message': message,
                    'created_at': str(created_at)
                })
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'messages': messages})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    except Exception as e:
        print(f"Error getting messages: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return jsonify({'status': 'healthy', 'database': 'connected'}), 200
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 503
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/api/db-status')
def db_status():
    """Check database connection status"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return jsonify({
                'connected': True,
                'version': version,
                'host': DB_CONFIG['host'],
                'database': DB_CONFIG['database']
            })
        else:
            return jsonify({'connected': False})
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Flask Application")
    print("=" * 50)
    print(f"Database Host: {DB_CONFIG['host']}")
    print(f"Database Name: {DB_CONFIG['database']}")
    print(f"Database User: {DB_CONFIG['user']}")
    print("=" * 50)
    
    # Initialize database tables
    init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
# from flask import Flask, render_template, jsonify
# import mariadb

# app = Flask(__name__)


# @app.route("/", methods=['GET', 'POST'])
# def index():
#     return render_template('index.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     return "This is the login page"

# @app.route('/database', methods=['GET', 'POST'])
# def database():
#     config = {
#         'host': 'mysqldb',                #'172.21.0.2',
#         'port': 3306,
#         'user': 'me',
#         'password': 'yourSAFEpassword',
#         'database': 'student'
#     }
#     conn = mariadb.connect(**config)
#     cur = conn.cursor()
#     sql= "SELECT * FROM student"
#     cur.execute (sql)
#     myresult = cur.fetchall()
#     return jsonify(myresult)                             #"{}".format(myresult)


# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
