import re
from flask import Flask, render_template, request, send_file, flash
import docx
import uuid
from io import BytesIO
import zipfile
import logging

app = Flask(__name__)
app.secret_key = 'sarkari_parcha_parser_secret_key'  # Required for flash messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store everything in memory instead of disk
file_store = {}
image_store = {}

def is_valid_docx(file_bytes):
    """Check if the file is a valid DOCX file"""
    try:
        zip_file = zipfile.ZipFile(BytesIO(file_bytes))
        # Check for essential docx components
        required_files = ['[Content_Types].xml', 'word/document.xml']
        for file in required_files:
            if file not in zip_file.namelist():
                return False
        return True
    except zipfile.BadZipFile:
        return False
    except Exception as e:
        logger.error(f"Error validating DOCX: {str(e)}")
        return False

def parse_docx(file_bytes):
    """Parse DOCX file from memory and count questions, options, answers, and solutions"""
    try:
        # Validate the file before processing
        if not is_valid_docx(file_bytes):
            raise ValueError("Invalid or corrupted DOCX file")
        
        # Load docx from bytes
        doc = docx.Document(BytesIO(file_bytes))
        rels = doc.part._rels
        image_rel_map = {}
        
        # Extract and store images
        for rel in rels:
            try:
                if "image" in rels[rel].target_ref:
                    image_rel_map[rel] = save_image(rels[rel].target_part.blob)
            except Exception as e:
                logger.warning(f"Could not process image relation: {str(e)}")
                continue

        content_html = ""
        q_count = 0
        opt_count = 0  # Changed to count actual options rather than assuming 4 per question
        ans_count = 0
        sol_count = 0
        
        for para in doc.paragraphs:
            try:
                text = para.text.strip()
                
                # First, add any images in this paragraph to the HTML content
                try:
                    for blip in para._element.xpath(".//a:blip"):
                        embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        img_url = image_rel_map.get(embed)
                        if img_url:
                            content_html += f"<img src='{img_url}' style='max-width:400px; margin:10px 0;'><br><br>"
                except Exception as e:
                    logger.warning(f"Error processing paragraph images: {str(e)}")

                # Skip empty paragraphs with no images
                if not text and not para._element.xpath(".//a:blip"):
                    continue

                # Process text paragraphs
                escaped_text = (text.replace("&", "&amp;")
                                .replace("<", "&lt;")
                                .replace(">", "&gt;")
                                .replace('"', "&quot;"))
                
                if re.match(r"^Q\d+", text):
                    q_count += 1
                    content_html += f"<span style='color:blue; font-weight:bold;'>{escaped_text}</span><br><br>"
                elif text.startswith(("a.", "b.", "c.", "d.")):
                    opt_count += 1  # Count actual options
                    content_html += f"<span style='color:green;'>{escaped_text}</span><br><br>"
                elif text.startswith("Ans."):
                    ans_count += 1
                    content_html += f"<span style='color:red;'>{escaped_text}</span><br><br>"
                elif text.startswith("Sol."):
                    sol_count += 1
                    content_html += f"<span style='color:purple;'>{escaped_text}</span><br><br>"
                else:
                    content_html += f"<span style='color:black;'>{escaped_text}</span><br><br>"
            except Exception as e:
                logger.warning(f"Error processing paragraph: {str(e)}")
                continue
        
        return content_html, q_count, opt_count, ans_count, sol_count
    
    except ValueError as e:
        # Re-raise value errors (like our invalid DOCX validation)
        raise
    except KeyError as e:
        # Handle specific KeyError for corrupt docx
        if "There is no item named 'NULL' in the archive" in str(e):
            raise ValueError("Corrupt DOCX file: Missing required components")
        else:
            logger.error(f"KeyError in parse_docx: {str(e)}")
            raise ValueError(f"Error processing DOCX file: {str(e)}")
    except Exception as e:
        logger.error(f"Error in parse_docx: {str(e)}")
        raise ValueError(f"Error processing DOCX file: {str(e)}")

def save_image(blob):
    """Save image to memory store"""
    try:
        img_id = str(uuid.uuid4())
        image_store[img_id] = blob
        # Return a URL-like path that will be handled by our route
        return f"/image/{img_id}"
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('No file part', 'error')
                return render_template('index.html', data=data)
                
            file = request.files['file']
            
            # Check if file was selected
            if file.filename == '':
                flash('No selected file', 'error')
                return render_template('index.html', data=data)
                
            expected_q = int(request.form.get('expected_questions', 0))

            # Validate file extension
            if not file.filename.lower().endswith('.docx'):
                flash('Only .docx files are supported', 'error')
                return render_template('index.html', data=data)
                
            # Read file content into memory
            file_bytes = file.read()
            
            try:
                # Process the document
                html_content, q, o, a, s = parse_docx(file_bytes)
                
                # Store in memory for reference if needed
                file_id = str(uuid.uuid4())
                file_store[file_id] = {
                    'filename': file.filename,
                    'bytes': file_bytes
                }

                # Fixed logic for status checks - now properly comparing expected vs actual
                status = {
                    'questions': '✅' if expected_q > 0 and q == expected_q else f'❌ ({q}/{expected_q})',
                    'options': '✅' if expected_q > 0 and o == expected_q * 4 else f'❌ ({o}/{expected_q * 4})',
                    'answers': '✅' if expected_q > 0 and a == expected_q else f'❌ ({a}/{expected_q})',
                    'solutions': '✅' if expected_q > 0 and s == expected_q else f'❌ ({s}/{expected_q})',
                }

                data = {
                    'filename': file.filename,
                    'content': html_content,
                    'questions': q,
                    'options': o,
                    'answers': a,
                    'solutions': s,
                    'expected': expected_q,
                    'status': status,
                    'file_id': file_id  # Store this for potential future use
                }
                
            except ValueError as e:
                flash(str(e), 'error')
                logger.error(f"File processing error: {str(e)}")
                
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            logger.error(f"Unexpected error: {str(e)}")
                
    return render_template('index.html', data=data)

@app.route('/image/<img_id>')
def serve_image(img_id):
    """Serve images from memory"""
    if img_id in image_store:
        try:
            image_data = image_store[img_id]
            return send_file(BytesIO(image_data), mimetype='image/png')
        except Exception as e:
            logger.error(f"Error serving image {img_id}: {str(e)}")
            return "Error loading image", 500
    return "Image not found", 404

# Add route to download the original file if needed
@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id in file_store:
        try:
            file_data = file_store[file_id]
            return send_file(
                BytesIO(file_data['bytes']),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=file_data['filename']
            )
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return "Error downloading file", 500
    return "File not found", 404



if __name__ == '__main__':
    app.run(debug=True)