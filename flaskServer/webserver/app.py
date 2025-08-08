from flask import Flask, render_template, jsonify
import mariadb
# import os
# Make sure Flask and mariadb are installed in your environment:
# pip install flask mariadb
app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return "This is the login page"

@app.route('/database', methods=['GET', 'POST'])
def database():
    config = {
        'host': 'mysqldb',                #'172.21.0.2',
        'port': 3306,
        'user': 'me',
        'password': 'yourSAFEpassword',
        'database': 'student'
    }
    conn = mariadb.connect(**config)
    cur = conn.cursor()
    sql= "SELECT * FROM student"
    cur.execute (sql)
    myresult = cur.fetchall()
    return jsonify(myresult)                             #"{}".format(myresult)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)