from flask import Flask, request, jsonify
import sqlite3 
import jwt
import datetime
from functools import wraps


app = Flask(__name__)

app.config['DEBUG'] = True

SECRET_KEY = "toto_jk9514Th99"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'statusCode': 403, 'message': 'Token requerido'})
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'statusCode': 401, 'message': 'Token expirado'})
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(""" 
                CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT,
                email TEXT,
                birthdate DATE,
                status TEXT default 'active',
                secret_question TEXT,
                secret_answer TEXT
                )
                """)
                   
    cursor.execute(""" 
                CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                create_date DATE,
                initial_price TEXT,
                retail_price TEXT,
                wholesale_price TEXT
                )
                """)
    
    
    cursor.execute("INSERT INTO users (username, password, email, birthdate, status, secret_question, secret_answer) SELECT 'admin', '1234', 'admin@localhost.com', '1990-01-01', 'active', 'Cual es tu mascota?', 'perro' WHERE NOT EXISTS (SELECT 1 FROM users WHERE username ='admin')")
    cursor.execute("INSERT INTO users (username, password, email, birthdate, status, secret_question, secret_answer) SELECT 'user', 'pass', 'user@localhost', '2002-07-02',  'active', 'Cual es tu color favorito?', 'azul' WHERE NOT EXISTS (SELECT 1 FROM users WHERE username ='user')")
    conn.commit()
    conn.close()

@app.route('/user')
def get_user():
    username = request.args.get('username') or ''
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    user =  cursor.fetchone()
    return jsonify({"user":user})



@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)

    user = cursor.fetchone()
    if user:
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'statusCode': 401, 'message': 'Credenciales inválidas'})
    
@app.route('/admin/data')
def admin_data():
    return jsonify({"data" : "Datos confidenciales. Acceso sin autenticacion"})

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    birthdate = request.form.get('birthdate')
    secret_question = request.form.get('secret_question')
    secret_answer = request.form.get('secret_answer')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = f"""
        INSERT INTO users (username, password, email, birthdate, secret_question, secret_answer)
        VALUES ('{username}', '{password}', '{email}', '{birthdate}', '{secret_question}', '{secret_answer}')
    """
    cursor.execute(query)

    return jsonify({"statusCode": 200, "message": "Registro exitoso"})


@app.route('/update_user', methods=['PUT'])
def update_user():
    id_user = request.form.get('id')
    new_username = request.form.get('username')
    new_email = request.form.get('email')
    new_password = request.form.get('password')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = f"""
        UPDATE users
        SET username = '{new_username}',
            email = '{new_email}',
            password = '{new_password}'
        WHERE id = {id_user}
    """

    cursor.execute(query)

    return jsonify({"message": "Usuario actualizado correctamente"})



@app.route('/delete_user', methods=['PUT'])
def delete_user():
    user_id = request.form.get('id')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = "UPDATE users SET status = 'inactive' WHERE id = ?"
    cursor.execute(query, (user_id,))

    return jsonify({"message": "Usuario desactivado correctamente"})


@app.route('/getuser_byid', methods=['GET'])
def getuser_byid():
    user_id = request.args.get('id')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = "SELECT id, username, email FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"user": {
            "id": user[0],
            "username": user[1],
            "email": user[2]
        }})
    else:
        return jsonify({"statusCode": 404, "message": "Usuario no encontrado"})

@app.route('/add_products', methods=['POST'])
@token_required
def add_products():
    data = request.form
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, description, create_date, initial_price, retail_price, wholesale_price)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (data['name'], data['description'], data['create_date'],
         data['initial_price'], data['retail_price'], data['wholesale_price']))
    conn.commit()
    conn.close()
    return jsonify({"statusCode": 200, "message": "Producto creado correctamente"})

@app.route('/all_products', methods=['GET'])
@token_required
def all_products():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "create_date": row[3],
            "initial_price": row[4],
            "retail_price": row[5],
            "wholesale_price": row[6]
        })

    return jsonify(products), 200

@app.route('/update_products/<int:id>', methods=['PUT'])
@token_required
def update_products(id):
    data = request.form
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET name=?, description=?, create_date=?,
        initial_price=?, retail_price=?, wholesale_price=?
        WHERE id=?""",
        (data['name'], data['description'], data['create_date'],
         data['initial_price'], data['retail_price'], data['wholesale_price'], id))
    conn.commit()
    conn.close()
    return jsonify({"statusCode": 200, "message": "Producto actualizado correctamente"})

@app.route('/delete_products/<int:id>', methods=['DELETE'])
@token_required
def delete_products(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"statusCode": 200 ,"message": "Producto eliminado correctamente"})



if __name__ == '__main__':
    init_db()
    app.run(debug=True)