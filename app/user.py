from flask import Blueprint, render_template, flash, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Temp
from . import db
import tempfile
import os
import cv2 as cv
import pytesseract
import requests
import json
import pdfplumber

user = Blueprint('user', __name__)


@user.route('/', methods=['GET', 'POST'])
def index():
    
    if request.method == 'GET':
        return render_template('index.html', user=current_user)   
    else:
        
        file = request.files['file']
        
        if not file:
            flash("Empty Document!", category='error')
        else:
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file.filename == '':
                flash("No file name", category="error")
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
                                
                                # new_document = Document(file=image_name, data=file_content.read(), user_id=current_user.id)
                                # db.session.add(new_document)
                                # db.session.commit()
                                # flash("Document Created!", category='success')
                                text = ocr(image_name, file_content.read())
                                
                                
                                # Edit text in Zoho Writer
                                url = "https://api.office-integrator.com/writer/officeapi/v1/documents?apikey=a962b1868966a007667c7c5f1bf74e72"
                                payload = {
                                    'apikey': 'a962b1868966a007667c7c5f1bf74e72'
                                }
                                files = [
                                    ('document', (image_name, text))
                                ]
                                headers = {
                                    'Cookie': '051913c8ce=b2f3b97207f13ead5d1d3527e09c8d2a; JSESSIONID=686BD1B361CAD1F0E9EB3F754824651E; ZW_CSRF_TOKEN=437ff7a0-834d-48a7-9388-066a1a4c541b; _zcsr_tmp=437ff7a0-834d-48a7-9388-066a1a4c541b'
                                }

                                response = requests.request("POST", url, headers=headers, data=payload, files=files)

                                json_data = json.loads(response.text)
                                # print(json_data['document_url'])
                                # return json_data['document_url']
                                link = json_data['document_url']
                                
                                
                                # Delete the temporary file
                                os.unlink(temp_filename)
                                return link
                    else:
                        print('Failed to download the image.')
                
            elif file_extension in ['.jpg', '.jpeg', '.pdf']:      
                # 
                # 
                # 
                # TEST SECTION
                # 
                # 
                # 
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_filename = temp_file.name

                file.save(temp_filename)

                # flash("Document Loading!", category='success')
                text = ocr(file.filename, temp_file.read())
                # print(f'this is the link: {link}')
                
                    # Edit text in Zoho Writer
                url = "https://api.office-integrator.com/writer/officeapi/v1/documents?apikey=a962b1868966a007667c7c5f1bf74e72"
                payload = {
                    'apikey': 'a962b1868966a007667c7c5f1bf74e72'
                }
                files = [
                    ('document', (file.filename, text))
                ]
                headers = {
                    'Cookie': '051913c8ce=b2f3b97207f13ead5d1d3527e09c8d2a; JSESSIONID=686BD1B361CAD1F0E9EB3F754824651E; ZW_CSRF_TOKEN=437ff7a0-834d-48a7-9388-066a1a4c541b; _zcsr_tmp=437ff7a0-834d-48a7-9388-066a1a4c541b'
                }

                response = requests.request("POST", url, headers=headers, data=payload, files=files)

                json_data = json.loads(response.text)
                # print(json_data['document_url'])
                # return json_data['document_url']
                link = json_data['document_url']
                
                
                # Delete the temporary file
                os.unlink(temp_filename)
                    
                # 
                # 
                # 
                return link
            else:
                return '0'
    


def ocr(file_name, file_data):
    # document = Document.query.get_or_404(document_id)
    file_extension = os.path.splitext(file_name)[1].lower()
    
    if file_extension == '.pdf':
        # Perform OCR on PDF using pdfplumber
        text = extract_text_from_pdf(file_data)
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        # Perform OCR on image using pytesseract
        text = extract_text_from_image(file_data)
    else:
        flash("Unsupported file format", category='error')
        return '0'

    return text

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
    
    # print(text)
    
    return text

