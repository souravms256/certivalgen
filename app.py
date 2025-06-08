from flask import Flask, render_template, request, send_from_directory, url_for, jsonify, flash, redirect, make_response
import os
import json
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
import datetime
import logging
from io import BytesIO
from pdf2image import convert_from_path

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
TEMPLATE_FOLDER = "static/templates"
PREVIEW_FOLDER = "static/previews"
OUTPUT_FOLDER = "certificates"
FONT_FOLDER = "static/fonts"
CONFIG_FILE = "template_config.json"

# Ensure folders exist
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONT_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default template configurations
DEFAULT_CONFIG = {
    "black_template.pdf": {
        "name_position": {"x": 0.5, "y": 0.45},
        "font_size": 45,
        "font_color": [1.0, 0.84, 0.0],
        "font_name": "PinyonScriptRegular",
        "text_alignment": "center"
    },
    "brown_floral_template.pdf": {
        "name_position": {"x": 0.5, "y": 0.55},
        "font_size": 40,
        "font_color": [0.4, 0.2, 0.0],
        "font_name": "PinyonScriptRegular",
        "text_alignment": "center"
    }
}

class CertificateGenerator:
    def __init__(self):
        self.config = self.load_template_config()
        self.fonts = self.load_fonts()

    def load_fonts(self):
        """Load available fonts"""
        fonts = {}
        default_fonts = ['PinyonScript-Regular.ttf', 'Dancing-Script.ttf', 'Great-Vibes.ttf']

        for font_file in default_fonts:
            font_path = os.path.join(FONT_FOLDER, font_file)
            if os.path.exists(font_path):
                font_name = font_file.split('.')[0].replace('-', '')
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    fonts[font_name] = font_path
                    logger.info(f"Loaded font: {font_name}")
                except Exception as e:
                    logger.warning(f"Failed to load font {font_file}: {e}")

        if not fonts:
            logger.warning("No custom fonts loaded. Using default fonts.")
            fonts['Helvetica'] = None
            fonts['Times-Roman'] = None

        return fonts

    def load_template_config(self):
        """Load template configuration from JSON file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

        self.save_template_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    def save_template_config(self, config):
        """Save template configuration to JSON file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_color_from_list(self, color_list):
        """Convert color list to reportlab Color object"""
        if len(color_list) == 3:
            return Color(color_list[0], color_list[1], color_list[2])
        return Color(0, 0, 0)

    def add_text_to_certificate(self, input_pdf, output_pdf, name, template_name):
        """Add text to certificate with configurable positioning"""
        try:
            pdf_reader = PdfReader(input_pdf)
            pdf_writer = PdfWriter()
            page = pdf_reader.pages[0]

            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            template_config = self.config.get(template_name, DEFAULT_CONFIG.get(template_name, list(DEFAULT_CONFIG.values())[0]))

            packet = BytesIO()
            canvas_obj = canvas.Canvas(packet, pagesize=(page_width, page_height))

            font_name = template_config.get('font_name', 'Helvetica')
            if font_name in self.fonts:
                canvas_obj.setFont(font_name, template_config['font_size'])
            else:
                canvas_obj.setFont('Helvetica', template_config['font_size'])

            color = self.get_color_from_list(template_config['font_color'])
            canvas_obj.setFillColor(color)

            pos_config = template_config['name_position']
            x_pos = pos_config['x'] * page_width
            y_pos = pos_config['y'] * page_height

            if template_config.get('text_alignment', 'center') == 'center':
                text_width = pdfmetrics.stringWidth(name, font_name, template_config['font_size'])
                x_pos = x_pos - (text_width / 2)

            canvas_obj.drawString(x_pos, y_pos, name)
            canvas_obj.save()

            packet.seek(0)
            overlay_reader = PdfReader(packet)
            overlay_page = overlay_reader.pages[0]
            page.merge_page(overlay_page)
            pdf_writer.add_page(page)

            for p in pdf_reader.pages[1:]:
                pdf_writer.add_page(p)

            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)

            return True

        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            return False

    def generate_preview_images(self):
        """Generate preview images for all templates"""
        templates_generated = 0
        for filename in os.listdir(TEMPLATE_FOLDER):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(TEMPLATE_FOLDER, filename)
                preview_path = os.path.join(PREVIEW_FOLDER, filename.replace(".pdf", ".png"))

                if not os.path.exists(preview_path):
                    try:
                        pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
                        pages[0].save(preview_path, "PNG")
                        templates_generated += 1
                        logger.info(f"Generated preview for {filename}")
                    except Exception as e:
                        logger.error(f"Failed to generate preview for {filename}: {e}")

        return templates_generated

cert_generator = CertificateGenerator()

@app.route('/', methods=['GET', 'POST'])
def index():
    cert_generator.generate_preview_images()
    templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
    templates.sort()

    if request.method == 'POST':
        return generate_certificate()

    return render_template('index.html', templates=templates)

def generate_certificate():
    try:
        name = request.form.get('name', '').strip()
        template_file = request.form.get('template', '').strip()

        if not name:
            flash('Please provide a recipient name.', 'error')
            templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
            templates.sort()
            return render_template('index.html', templates=templates, error='Please provide a recipient name.')

        if not template_file:
            flash('Please select a template.', 'error')
            templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
            templates.sort()
            return render_template('index.html', templates=templates, error='Please select a template.')

        if not template_file.endswith('.pdf'):
            flash('Invalid template selected.', 'error')
            templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
            templates.sort()
            return render_template('index.html', templates=templates, error='Invalid template selected.')

        input_path = os.path.join(TEMPLATE_FOLDER, template_file)
        if not os.path.exists(input_path):
            flash('Selected template not found.', 'error')
            templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
            templates.sort()
            return render_template('index.html', templates=templates, error='Selected template not found.')

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        output_filename = f"{safe_name}_{timestamp}_certificate.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        success = cert_generator.add_text_to_certificate(
            input_path, output_path, name, template_file
        )

        if success:
            logger.info(f"Certificate generated successfully for {name}")
            response = make_response(send_from_directory(
                OUTPUT_FOLDER,
                output_filename,
                as_attachment=True,
                download_name=f"{name}_Certificate.pdf"
            ))
            response.headers['X-Success-Message'] = f"Certificate generated successfully for {name}"
            return response
        else:
            flash('Error generating certificate. Please try again.', 'error')
            templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
            templates.sort()
            return render_template('index.html', templates=templates, error='Error generating certificate. Please try again.')

    except Exception as e:
        logger.error(f"Unexpected error in generate_certificate: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
        templates.sort()
        return render_template('index.html', templates=templates, error='An unexpected error occurred. Please try again.')

@app.route('/api/templates')
def get_templates():
    templates = []
    for filename in os.listdir(TEMPLATE_FOLDER):
        if filename.endswith('.pdf'):
            preview_file = filename.replace('.pdf', '.png')
            preview_path = os.path.join(PREVIEW_FOLDER, preview_file)

            templates.append({
                'name': filename,
                'display_name': filename.replace('.pdf', '').replace('_', ' ').title(),
                'preview_url': url_for('static', filename=f'previews/{preview_file}') if os.path.exists(preview_path) else None
            })

    return jsonify(templates)

@app.route('/api/template-config/<template_name>')
def get_template_config(template_name):
    config = cert_generator.config.get(template_name, {})
    return jsonify(config)

@app.route('/api/template-config/<template_name>', methods=['POST'])
def update_template_config(template_name):
    try:
        new_config = request.json
        cert_generator.config[template_name] = new_config
        cert_generator.save_template_config(cert_generator.config)
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/config')
def config_page():
    templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pdf')]
    return render_template('config.html', templates=templates, config=cert_generator.config)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    for folder in [TEMPLATE_FOLDER, PREVIEW_FOLDER, OUTPUT_FOLDER, FONT_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    cert_generator.generate_preview_images()

    print("🚀 Certificate Generator is starting...")
    print(f"📁 Templates folder: {TEMPLATE_FOLDER}")
    print(f"🖼️ Previews folder: {PREVIEW_FOLDER}")
    print(f"📄 Output folder: {OUTPUT_FOLDER}")
    print(f"🔤 Fonts folder: {FONT_FOLDER}")

    app.run(debug=True, host='0.0.0.0', port=5000)
