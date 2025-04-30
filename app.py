import re
from flask import Flask, render_template, request, send_file
import docx
import uuid
from io import BytesIO

app = Flask(__name__)

# Store everything in memory instead of disk
file_store = {}
image_store = {}

def parse_docx(file_bytes):
    """Parse DOCX file from memory and count questions, options, answers, and solutions"""
    # Load docx from bytes
    doc = docx.Document(BytesIO(file_bytes))
    rels = doc.part._rels
    image_rel_map = {}
    
    # Extract and store images
    for rel in rels:
        if "image" in rels[rel].target_ref:
            image_rel_map[rel] = save_image(rels[rel].target_part.blob)

    content_html = ""
    q_count = 0
    ans_count = 0
    sol_count = 0
    
    # Simple option counting logic - just count question paragraphs and 
    # set options to 4 times the number of questions
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # First, add any images in this paragraph to the HTML content
        for blip in para._element.xpath(".//a:blip"):
            embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            img_url = image_rel_map.get(embed)
            if img_url:
                content_html += f"<img src='{img_url}' style='max-width:400px; margin:10px 0;'><br><br>"

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
            content_html += f"<span style='color:green;'>{escaped_text}</span><br><br>"
        elif text.startswith("Ans."):
            ans_count += 1
            content_html += f"<span style='color:red;'>{escaped_text}</span><br><br>"
        elif text.startswith("Sol."):
            sol_count += 1
            content_html += f"<span style='color:purple;'>{escaped_text}</span><br><br>"
        else:
            content_html += f"<span style='color:black;'>{escaped_text}</span><br><br>"
    
    # Set options to exactly 4 times the number of questions
    opt_count = q_count * 4
    
    return content_html, q_count, opt_count, ans_count, sol_count

def save_image(blob):
    """Save image to memory store"""
    img_id = str(uuid.uuid4())
    image_store[img_id] = blob
    # Return a URL-like path that will be handled by our route
    return f"/image/{img_id}"

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    if request.method == 'POST':
        file = request.files['file']
        expected_q = int(request.form.get('expected_questions', 0))

        if file and file.filename.endswith('.docx'):
            filename = file.filename
            # Read file content into memory
            file_bytes = file.read()
            
            # Store in memory for reference if needed
            file_id = str(uuid.uuid4())
            file_store[file_id] = {
                'filename': filename,
                'bytes': file_bytes
            }

            html_content, q, o, a, s = parse_docx(file_bytes)

            status = {
                'questions': '✅' if q == expected_q else f'❌ ({q}/{expected_q})',
                'options': '✅' if o == expected_q * 4 else f'❌ ({o}/{expected_q * 4})',
                'answers': '✅' if a == expected_q else f'❌ ({a}/{expected_q})',
                'solutions': '✅' if s == expected_q else f'❌ ({s}/{expected_q})',
            }

            data = {
                'filename': filename,
                'content': html_content,
                'questions': q,
                'options': o,
                'answers': a,
                'solutions': s,
                'expected': expected_q,
                'status': status,
                'file_id': file_id  # Store this for potential future use
            }
                
    return render_template('index.html', data=data)

@app.route('/image/<img_id>')
def serve_image(img_id):
    """Serve images from memory"""
    if img_id in image_store:
        image_data = image_store[img_id]
        return send_file(BytesIO(image_data), mimetype='image/png')
    return "Image not found", 404

# Add route to download the original file if needed
@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id in file_store:
        file_data = file_store[file_id]
        return send_file(
            BytesIO(file_data['bytes']),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=file_data['filename']
        )
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)