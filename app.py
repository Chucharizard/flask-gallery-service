import os
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_cors import CORS
import sqlite3
import time
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
CORS(app)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos y carpeta de imágenes
DATABASE = os.environ.get('DATABASE_PATH', 'images.db')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# URL base para acceder a las imágenes (modificar para producción)
BASE_URL = os.environ.get('BASE_URL', '')

# Verificar si estamos en entorno de producción
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

# Desactiva S3 para desarrollo local
USE_S3 = False

# Crear directorios necesarios
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla de imágenes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        filename TEXT NOT NULL,
        mimetype TEXT NOT NULL,
        size INTEGER NOT NULL,
        storage_type TEXT DEFAULT 'local',
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos
init_db()

# Función para obtener URL de una imagen
def get_image_url(filename, storage_type='local'):
    return f"{BASE_URL}/api/uploads/{filename}"

# Función auxiliar para obtener todas las imágenes
def get_all_images():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images ORDER BY upload_date DESC')
    images = cursor.fetchall()
    conn.close()
    
    image_list = []
    for image in images:
        image_url = get_image_url(image['filename'])
        
        image_list.append({
            'id': image['id'],
            'title': image['title'],
            'description': image['description'],
            'filename': image['filename'],
            'path': image_url,
            'mimetype': image['mimetype'],
            'size': image['size'],
            'upload_date': image['upload_date']
        })
    
    return image_list

# ---- RUTAS WEB (HTML) ----

@app.route('/')
def web_index():
    images = get_all_images()
    return render_template('index.html', images=images)

@app.route('/gallery')
def web_gallery():
    images = get_all_images()
    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['GET', 'POST'])
def web_upload():
    if request.method == 'POST':
        # Verificar si la solicitud tiene el archivo
        if 'image' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['image']
        
        # Si el usuario no selecciona un archivo, el navegador
        # envía un archivo vacío sin nombre
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        # Verificar que sea una imagen
        allowed_mimetypes = ['image/jpeg', 'image/png', 'image/gif']
        if file.mimetype not in allowed_mimetypes:
            flash('El archivo no es una imagen válida', 'danger')
            return redirect(request.url)
        
        # Generar nombre único
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        
        # Guardar localmente
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        # Guardar en la base de datos
        title = request.form.get('title', 'Sin título')
        description = request.form.get('description', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO images (title, description, filename, mimetype, size)
        VALUES (?, ?, ?, ?, ?)
        ''', (title, description, filename, file.mimetype, file_size))
        conn.commit()
        conn.close()
        
        flash('Imagen subida correctamente', 'success')
        return redirect(url_for('web_gallery'))
    
    return render_template('upload.html')

@app.route('/image/<int:image_id>')
def web_image_detail(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()
    conn.close()
    
    if not image:
        flash('Imagen no encontrada', 'danger')
        return redirect(url_for('web_gallery'))
    
    image_url = get_image_url(image['filename'])
    
    image_data = {
        'id': image['id'],
        'title': image['title'],
        'description': image['description'],
        'filename': image['filename'],
        'path': image_url,
        'mimetype': image['mimetype'],
        'size': image['size'],
        'upload_date': image['upload_date']
    }
    
    return render_template('image_detail.html', image=image_data)

@app.route('/delete/<int:image_id>', methods=['POST'])
def web_delete_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener información de la imagen
    cursor.execute('SELECT filename FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()
    
    if not image:
        flash('Imagen no encontrada', 'danger')
        return redirect(url_for('web_gallery'))
    
    # Eliminar el archivo
    filepath = os.path.join(UPLOAD_FOLDER, image['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Eliminar registro de la base de datos
    cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()
    
    flash('Imagen eliminada correctamente', 'success')
    return redirect(url_for('web_gallery'))

# ---- API ENDPOINTS (JSON) ----

@app.route('/api')
def api_index():
    return jsonify({
        'message': 'Flask API con SQLite para imágenes funcionando'
    })

@app.route('/api/images', methods=['GET'])
def api_get_images():
    try:
        images = get_all_images()
        return jsonify({
            'success': True,
            'count': len(images),
            'data': images
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener imágenes',
            'error': str(e)
        }), 500

@app.route('/api/images/<int:image_id>', methods=['GET'])
def api_get_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()
    conn.close()
    
    if not image:
        return jsonify({
            'success': False,
            'message': 'Imagen no encontrada'
        }), 404
    
    image_url = get_image_url(image['filename'])
    
    return jsonify({
        'success': True,
        'data': {
            'id': image['id'],
            'title': image['title'],
            'description': image['description'],
            'filename': image['filename'],
            'path': image_url,
            'mimetype': image['mimetype'],
            'size': image['size'],
            'uploadDate': image['upload_date']
        }
    })

@app.route('/api/upload', methods=['POST'])
def api_upload_image():
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No se ha enviado ninguna imagen'
        }), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No se ha seleccionado ninguna imagen'
        }), 400
    
    # Verificar que sea una imagen
    allowed_mimetypes = ['image/jpeg', 'image/png', 'image/gif']
    if file.mimetype not in allowed_mimetypes:
        return jsonify({
            'success': False,
            'message': 'El archivo no es una imagen válida'
        }), 400
    
    # Generar nombre único
    timestamp = int(time.time())
    filename = f"{timestamp}_{secure_filename(file.filename)}"
    
    # Guardar localmente
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    
    # Guardar en la base de datos
    title = request.form.get('title', 'Sin título')
    description = request.form.get('description', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO images (title, description, filename, mimetype, size)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, description, filename, file.mimetype, file_size))
    conn.commit()
    
    # Obtener el ID de la imagen recién insertada
    image_id = cursor.lastrowid
    
    # Obtener la imagen recién insertada
    cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()
    conn.close()
    
    # Generar URL según el tipo de almacenamiento
    image_url = get_image_url(image['filename'])
    
    return jsonify({
        'success': True,
        'message': 'Imagen subida correctamente',
        'data': {
            'id': image['id'],
            'title': image['title'],
            'description': image['description'],
            'filename': image['filename'],
            'path': image_url,
            'mimetype': image['mimetype'],
            'size': image['size'],
            'uploadDate': image['upload_date']
        }
    }), 201

@app.route('/api/images/<int:image_id>', methods=['DELETE'])
def api_delete_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener información de la imagen
    cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()
    
    if not image:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Imagen no encontrada'
        }), 404
    
    # Eliminar el archivo
    filepath = os.path.join(UPLOAD_FOLDER, image['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Eliminar registro de la base de datos
    cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Imagen eliminada correctamente',
        'data': {
            'id': image['id'],
            'title': image['title'],
            'filename': image['filename']
        }
    })

# Servir archivos de imagen
@app.route('/api/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # En desarrollo, usar debug=True
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
