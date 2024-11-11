import os
import qrcode
import shutil
from flask import Flask, render_template, request, url_for, send_from_directory, redirect, flash
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)

# Configuración de la carpeta de subidas
# UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta de subidas si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'pptx', 'zip', 'rar', 'csv'}

# Función para verificar extensiones permitidas
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        folder_name = request.form.get('folder_name')
        existing_folder = request.form.get('existing_folder')
        folder_to_use = folder_name if folder_name else existing_folder
        
        if 'file' not in request.files or not folder_to_use:
            return render_template('upload.html', error="Por favor, llena todos los campos.")

        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Determina la carpeta a usar
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_to_use)
            os.makedirs(folder_path, exist_ok=True)

            # Guarda el archivo en la carpeta
            file_path = os.path.join(folder_path, filename)
            file.save(file_path)

            # Genera el código QR con el enlace para descargar el archivo
            download_url = url_for('uploaded_file', filename=f"{folder_to_use}/{filename}", _external=True)
            qr = qrcode.make(download_url)
            qr_filename = 'qr_code.png'
            qr_path = os.path.join(folder_path, qr_filename)
            qr.save(qr_path)

            # Genera las URLs para el archivo y el QR
            file_url = url_for('uploaded_file', filename=f"{folder_to_use}/{filename}")
            qr_code_url = url_for('uploaded_file', filename=f"{folder_to_use}/{qr_filename}")

            # Listar las carpetas existentes
            folder_names = [folder for folder in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, folder))]

            return render_template('upload.html', uploaded=True, file_url=file_url, qr_code_url=qr_code_url, folder_names=folder_names)

        else:
            return render_template('upload.html', error="Tipo de archivo no permitido.")
    
    # Listar las carpetas existentes al cargar la página de upload
    folder_names = [folder for folder in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, folder))]
    return render_template('upload.html', uploaded=False, folder_names=folder_names)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Ruta para ver el contenido de la carpeta
@app.route('/folder/<folder_name>')
def view_folder(folder_name):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # Obtener los archivos dentro de la carpeta
        return render_template('folder.html', folder_name=folder_name, files=files)
    else:
        return render_template('upload.html', error="La carpeta no existe.")

# Ruta para renombrar una carpeta
@app.route('/rename_folder', methods=['POST'])
def rename_folder():
    old_name = request.form.get('folder_name')
    new_name = request.form.get('new_name')

    if old_name and new_name:
        old_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], old_name)
        new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)

        if os.path.exists(old_folder_path) and not os.path.exists(new_folder_path):
            os.rename(old_folder_path, new_folder_path)

        return redirect(url_for('upload'))
    return render_template('upload.html', error="Nombre de carpeta inválido o ya existe una carpeta con el nuevo nombre.")

# Ruta para eliminar una carpeta
@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    folder_name = request.form.get('folder_name')
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)  # Eliminar la carpeta y su contenido
            time.sleep(1)  # Breve retraso para asegurar la eliminación
            if not os.path.exists(folder_path):  # Verificar si la carpeta se ha eliminado
                return redirect(url_for('upload'))
            else:
                raise Exception("La carpeta aún existe después de intentar eliminarla.")
        except PermissionError:
            return render_template('upload.html', error="No tienes permisos suficientes para eliminar la carpeta.")
        except Exception as e:
            print(f"Error al eliminar la carpeta: {e}")
            return render_template('upload.html', error="No se pudo eliminar la carpeta.")
    
    return render_template('upload.html', error="La carpeta no existe.")


@app.route('/view_files/<folder_name>')
def view_files(folder_name):
    try:
        # Ruta de la carpeta
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

        # Verifica si la carpeta existe
        if not os.path.exists(folder_path):
            flash(f"La carpeta {folder_name} no existe.", 'error')
            return redirect(url_for('upload'))

        # Obtiene los archivos de la carpeta
        files = os.listdir(folder_path)

        return render_template('view_files.html', folder_name=folder_name, files=files)
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('upload'))


if __name__ == '__main__':
    #app.run(debug=True)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host="0.0.0.0", port=os.getenv("PORT", default=5000))
