"""
Data Cleaning AI Website
Main Flask Application
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from config import config
from data_cleaner import DataCleaner
from io import BytesIO
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(config['development'])
CORS(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

data_cleaner = DataCleaner()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded file for data cleaning"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Analyze data
        analysis = data_cleaner.analyze_data(filepath)
        
        return jsonify(analysis), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean', methods=['POST'])
def clean_data():
    """Clean data based on selected options"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get cleaning options from request
        options = request.form.to_dict()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Clean data
        cleaned_df, report = data_cleaner.clean_data(filepath, options)
        
        # Save cleaned file
        output_filename = f"cleaned_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        if filename.endswith('.csv'):
            cleaned_df.to_csv(output_path, index=False)
        else:
            cleaned_df.to_excel(output_path, index=False)
        
        return jsonify({
            'success': True,
            'report': report,
            'filename': output_filename,
            'rows': len(cleaned_df),
            'columns': list(cleaned_df.columns)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download cleaned file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """API status check"""
    return jsonify({'status': 'online', 'version': '1.0.0'}), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
