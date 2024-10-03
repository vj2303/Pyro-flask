from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import re
import json
import os
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
 
# Set Tesseract executable path (if necessary)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create a route to handle image uploads and processing
@app.route('/extract_data', methods=['POST'])
def extract_data():
    # Check if the request has the file part
    if 'image' not in request.files:
        return jsonify({'error': 'No image file found in the request'}), 400

    image_file = request.files['image']
    
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the image file securely
    filename = secure_filename(image_file.filename)
    image_path = os.path.join('./uploads', filename)
    os.makedirs('./uploads', exist_ok=True)
    image_file.save(image_path)
    
    # Load the image and extract text
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image)
    
    # Clean the text
    cleaned_text = re.sub(r'[^A-Za-z0-9%.:\s-]', '', extracted_text)
    
    # Initialize output data structure
    output_data = {
        'extracted_text': extracted_text,
        'top_cities': [],
        'followers_and_non_followers': {},
        'gender_distribution': {
            'Men': '0.0%',
            'Women': '0.0%'
        },
        'age_distribution': {}
    }
    
    # Regex patterns and extraction logic
    city_pattern = r'(Mumbai|Bangalore|Pune|Delhi)\s*(\d{1,2}\.\d+%)'
    age_pattern = r'(\d{1,2}-\d{1,2}|\d{1,2}\+?)\s*([\d.]+%)'
    followers_percentage_pattern = r'(\d+\.\d+%)\s*Followers'
    non_followers_percentage_pattern = r'(\d+\.\d+%)\s*Non-followers'
    increase_in_followers_pattern = r'\+(\d+\.\d+%)'
    gender_pattern = r'(\d+\.\d+%)\s*(Men|Women)'

    # City extraction
    city_matches = re.findall(city_pattern, cleaned_text)
    if city_matches:
        for match in city_matches:
            output_data['top_cities'].append({
                'city': match[0],
                'percentage': match[1]
            })

    # Age distribution extraction
    age_matches = re.findall(age_pattern, cleaned_text)
    for age_range, percentage in age_matches:
        output_data['age_distribution'][age_range.strip()] = percentage.strip()

    # Followers and non-followers extraction
    followers_match = re.search(followers_percentage_pattern, cleaned_text)
    non_followers_match = re.search(non_followers_percentage_pattern, cleaned_text)
    increase_in_followers_match = re.search(increase_in_followers_pattern, cleaned_text)
    
    if followers_match:
        output_data['followers_and_non_followers']['followers_percentage'] = followers_match.group(1)
    if non_followers_match:
        output_data['followers_and_non_followers']['non_followers_percentage'] = non_followers_match.group(1)
    if increase_in_followers_match:
        output_data['followers_and_non_followers']['increase_in_followers'] = increase_in_followers_match.group(1) 

    # Gender distribution extraction
    gender_matches = re.findall(gender_pattern, cleaned_text)
    if gender_matches:
        for match in gender_matches:
            percentage, gender = match
            output_data['gender_distribution'][gender] = percentage

    # Return the extracted data as JSON
    return jsonify(output_data) 

