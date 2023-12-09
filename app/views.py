from flask import Blueprint, render_template, flash, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Document, User
from . import db
import json
import pytesseract
import base64
import os
import tempfile
from flask import send_file
import cv2 as cv
import pdfplumber
import requests
from PIL import Image
from io import BytesIO
import csv
import io
import webbrowser

views = Blueprint('views', __name__)


@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'GET':
        if request.method == 'GET':
            document_data = [{'id': document.id, 'name': document.file, 'data': document.data} for document in current_user.document_id]
            user = User.query.filter_by(id=current_user.id).first()
            lastname = user.lastname
            return render_template('home.html', user=current_user, documents=document_data, name = lastname)

    elif request.method == 'POST':
        file = request.files['file']
        # print(file.filename)
        # print(file)
        
        if not file:
            flash("Empty Document!", category='error')
        else:
            if file.filename == '':
                flash("No file name", category="error")
            else:      
                file_extension = os.path.splitext(file.filename)[1].lower()
                if file_extension in ['.jpg', '.jpeg', '.pdf']:
                    new_document = Document(file=file.filename, data=file.read(), user_id=current_user.id)
                    db.session.add(new_document)
                    db.session.commit()
                    flash("Document Created!", category='success')  
                elif file_extension in ['.png', '.tif', '.tiff', '.bmp', '.mdi', '.gif', '.fax', '.ico', '.heic', '.webp', '.svg', '.psd']:
                    short_file_extension = file_extension.replace('.', '')
                    print(short_file_extension)
                    print(short_file_extension)
                    url = f"https://v2.convertapi.com/convert/{short_file_extension}/to/jpg?Secret=9UiOkO8cz1WZJfZW&StoreFile=true"
                    payload = {}
                    files = []

                    with tempfile.NamedTemporaryFile(suffix='.' + short_file_extension) as temp_file:
                        # Save the image to the temporary file
                        file.save(temp_file.name)
                        temp_file.seek(0)

                        files.append(('File', (file.filename, open(temp_file.name, 'rb'), short_file_extension)))

                        headers = {}
                        # try:
                        response = requests.request("POST", url, headers=headers, data=payload, files=files)
                            
                        # print(response.text['Files']['Url'])
                        response_data = json.loads(response.text)
                        # print(response_data)
                        print(f'response data: {response.text}')
                        image_url = response_data['Files'][0]['Url']
                        image_name = response_data['Files'][0]['FileName']
                        image_response = requests.get(image_url)
                        print(f'Status code: {image_response.status_code}')

                        if image_response.status_code == 200:
                             with tempfile.NamedTemporaryFile(delete=False) as file:
                                file.write(image_response.content)
                                temp_filename = file.name
                                with open(temp_filename, 'rb') as file_content:
                                    new_document = Document(file=image_name, data=file_content.read(), user_id=current_user.id)
                                    db.session.add(new_document)
                                    db.session.commit()
                                    flash("Document Created!", category='success')
                        else:
                            print('Failed to download the image.')
                else:
                    flash("Unsupported Format!", category='error')  
    else:
        return "Invalid method"
    
    return redirect(url_for('views.home'))


@views.route('/delete-document/<int:document_id>', methods=['GET'])
def delete_document(document_id):
    document = Document.query.get(document_id)
    if document:
        if document.user_id == current_user.id:
            db.session.delete(document)
            db.session.commit()
            flash("Document Deleted!", category='success')
        else:
            flash("This is not your Document", category="error")
    else:
        flash("Document does not exist", category="error")
    return redirect(url_for('views.home'))
    


@views.route('/get_document_image/<int:document_id>', methods=['GET'])
@login_required
def get_document_image(document_id):
    document = Document.query.get_or_404(document_id)
    file_extension = os.path.splitext(document.file)[1].lower()

    if file_extension == '.pdf':
        # Extract a thumbnail from the first page of the PDF
        thumbnail = extract_pdf_thumbnail(document.data)
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        # Read the image file
        thumbnail = Image.open(BytesIO(document.data))
    else:
        flash("Unsupported file format", category='error')
        return redirect(url_for('views.home'))
    
    # Create a thumbnail of the image
    thumbnail = create_thumbnail(thumbnail)
    
    # Save the thumbnail to a temporary file
    temp_dir = tempfile.gettempdir()
    temp_filename = f"thumbnail_{document_id}.jpg"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    thumbnail.save(temp_filepath, "JPEG")
    
    # Serve the temporary thumbnail file
    return send_file(temp_filepath, mimetype='image/jpeg', as_attachment=False)

def extract_pdf_thumbnail(pdf_data):
    with pdfplumber.open(BytesIO(pdf_data)) as pdf:
        first_page = pdf.pages[0]
        image = first_page.to_image(resolution=72)  # Set the resolution as desired
        thumbnail = image.original.convert("RGB")
        return thumbnail

def create_thumbnail(image, max_size=(200, 200)):
    image.thumbnail(max_size)
    return image



@views.route('/ocr/<int:document_id>', methods=['GET'])
@login_required
def ocr(document_id):
    document = Document.query.get_or_404(document_id)
    file_extension = os.path.splitext(document.file)[1].lower()
    
    if file_extension == '.pdf':
        # Perform OCR on PDF using pdfplumber
        text = extract_text_from_pdf(document.data)
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        # Perform OCR on image using pytesseract
        text = extract_text_from_image(document.data)
    else:
        flash("Unsupported file format", category='error')
        return redirect(url_for('views.home'))
    
    # if text == " ":
    #     flash("Image is too dark for processing", category="error")
    #     return redirect(url_for('views.home'))

    # Edit text in Zoho Writer
    url = "https://api.office-integrator.com/writer/officeapi/v1/documents?apikey=a962b1868966a007667c7c5f1bf74e72"
    payload = {
        'apikey': 'a962b1868966a007667c7c5f1bf74e72'
    }
    files = [
        ('document', (document.file.split('.', 1)[0], text))
    ]
    headers = {
        'Cookie': '051913c8ce=b2f3b97207f13ead5d1d3527e09c8d2a; JSESSIONID=686BD1B361CAD1F0E9EB3F754824651E; ZW_CSRF_TOKEN=437ff7a0-834d-48a7-9388-066a1a4c541b; _zcsr_tmp=437ff7a0-834d-48a7-9388-066a1a4c541b'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    json_data = json.loads(response.text)
    print(json_data['document_url'])
    return redirect(json_data['document_url'])

def preprocess_image(image):
    
    # Convert image to grayscale
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    # Calculate the average pixel value in the image
    average_pixel_value = cv.mean(gray_image)[0]
    
    print(f'average_pixel_value {average_pixel_value}')

    # Determine if the image has a black background
    has_black_background = average_pixel_value < 150

    if has_black_background:
        # Invert colors for black background images
        image = cv.bitwise_not(image)
    
    return image


def extract_text_from_pdf(pdf_data):
    with tempfile.NamedTemporaryFile(delete=False) as temp_pdf_file:
        temp_pdf_file.write(pdf_data)
        temp_pdf_file.close()
        
        with pdfplumber.open(temp_pdf_file.name) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
                
        os.unlink(temp_pdf_file.name)
        
    return text

def extract_text_from_image(image_data):
    temp_dir = tempfile.gettempdir()
    temp_filename = "temp_image.jpg"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    
    with open(temp_filepath, 'wb') as temp_image_file:
        temp_image_file.write(image_data)
        
    image = cv.imread(temp_filepath)
    preprocessed_image = preprocess_image(image)
    text = pytesseract.image_to_string(preprocessed_image)
    
    os.unlink(temp_filepath)
    
    print(text)
    
    return text

# @app.route('/process', methods=['POST'])
# def process_image():
#     # Get the uploaded file from the form
#     file = request.files['file']

#     # Save the file to a temporary location
#     temp_path = tempfile.mktemp(suffix='.jpg')
#     file.save(temp_path)

#     # Read the image using OpenCV
#     image = cv2.imread(temp_path)

#     # Get the adjustment values from the form
#     contrast = float(request.form['contrast'])
#     brightness = int(request.form['brightness'])

#     # Perform image adjustments
#     adjusted_image = adjust_contrast(image, contrast, brightness)

#     # Save the edited image to a temporary location
#     edited_path = tempfile.mktemp(suffix='.jpg')
#     cv2.imwrite(edited_path, adjusted_image)
    
#     text = ocr()

#     # Clean up temporary files
#     file.close()
#     # ...

#     # Return the edited image
#     return send_file(edited_path, mimetype='image/jpeg')

def adjust_contrast(image, alpha, beta):
    # Apply contrast and brightness adjustment
    adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return adjusted


# def extract_text_from_image(image_data):
#     temp_dir = tempfile.gettempdir()
#     temp_filename = "temp_image.jpg"
#     temp_filepath = os.path.join(temp_dir, temp_filename)
    
#     with open(temp_filepath, 'wb') as temp_image_file:
#         temp_image_file.write(image_data)
        
#     image = cv.imread(temp_filepath, cv.COLOR_BGR2GRAY)
#     image = cv.GaussianBlur(image, )
#     text = pytesseract.image_to_string(image)

    
#     os.unlink(temp_filepath)
#     print(text)
    
#     return text



@views.route('/socr/<int:document_id>', methods=['GET'])
@login_required
def socr(document_id):
    document = Document.query.get_or_404(document_id)

    # Save the image data to a temporary file
    temp_dir = tempfile.gettempdir()
    temp_filename = f"document_{document_id}.jpg"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    with open(temp_filepath, 'wb') as file:
        file.write(document.data)

    image = cv.imread(temp_filepath)

    url = 'https://app.nanonets.com/api/v2/OCR/Model/ceeebab1-5f48-4ce9-845e-066b81ce3d97/LabelFile/?async=false'

    data = {'file': open(temp_filepath, 'rb')}

    response = requests.post(url, auth=requests.auth.HTTPBasicAuth('78d1996a-9789-11ed-b6de-a693374d4922', ''), files=data)

    data = json.loads(response.text)
    
        # Extract the headers from the first dictionary in the list
    filtered_data = []
    for item in data['result'][0]['prediction']:
        filtered_item = {item['label']: item['ocr_text']}
        filtered_data.append(filtered_item)
        
    document_name = document.file.split('.', 1)[0]
    
    #
    #
    #
    #
    #
    #
    #
    # TEST 1
    #
    # document = Document.query.get_or_404(document_id)
    # document_name = document.file.split('.', 1)[0]
    
    # url = "http://localhost:3000/json-data"
    # headers = {}
    # payload ={}
    
    # response = requests.request('GET', url, headers = headers, data = payload)
    
    # data = json.loads(response.text)
    
    # # Extract the headers from the first dictionary in the list
    # filtered_data = []
    # for item in data['result'][0]['prediction']:
    #     filtered_item = {item['label']: item['ocr_text']}
    #     filtered_data.append(filtered_item)
    
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
        
    return render_template('select-fields.html', data = filtered_data, user=current_user, document_name = document_name)
     




@views.route('/edit-socr', methods=['GET','POST'])
@login_required
def edit_socr():
    selected_fields = request.form.getlist('fields')
    document_name = request.form.get('document_name')
    
    # Create a dictionary to store the selected fields
    selected_data = {}
    for field in selected_fields:
        key, value = field.split('|')
        selected_data[key] = value

    # Convert the selected_data dictionary to a CSV file
    csv_data = []
    csv_header = []
    for key, value in selected_data.items():
        csv_header.append(key)
        csv_data.append(value)

    # Create a file-like object in memory
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(csv_header)  # Write the header
    csv_writer.writerow(csv_data)  # Write the data row
    csv_buffer.seek(0)  # Reset the buffer's position to the beginning


    # # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as file:
        csv_file = file.name

        # Write the CSV data to the temporary file
        with open(csv_file, 'w') as f:
            f.write(csv_buffer.getvalue())
    
        # # # Edit CSV in Zoho Sheet

    url = "https://api.office-integrator.com/sheet/officeapi/v1/spreadsheet?apikey=a962b1868966a007667c7c5f1bf74e72"

    payload = {}
    files = [
        ('document', (f'{document_name}.csv', open(csv_file, 'rb')))
    ]
    headers = {
        'Cookie': 'JSESSIONID=6FB8F4F92D3AAF97A531DCB19C6D1362; _zcsr_tmp=06290659-5cf1-498a-9212-abd7535a4d40; c6d59bfa86=b4d10425a28875a69de70bd48446c54d; zscookcsr=06290659-5cf1-498a-9212-abd7535a4d40'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    # print(response.text)

    try:
        data = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print("Error: Invalid JSON response")
        print("Response content:")
        print(response.text)
        return response.text
    
    # return csv_header

    # print(data['document_url'])

    return redirect(data['document_url'])
    

    
@views.route('/model/<int:document_id>', methods=['GET','POST'])
@login_required
def select_model(document_id):
    return render_template('select-model.html', user = current_user, document_id = document_id)
