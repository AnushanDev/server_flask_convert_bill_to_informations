#python app.py

from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from pytesseract import image_to_string
from PIL import Image
from io import BytesIO
import pypdfium2 as pdfium
import json
from subprocess import run, PIPE
from PIL import Image


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
load_dotenv()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_pdf_to_images(file_path, scale=300/72):
    # Ensure the "images" directory exists
    if not os.path.exists('images'):
        os.makedirs('images')

    pdf_file = pdfium.PdfDocument(file_path)
    page_indices = [i for i in range(len(pdf_file))]

    renderer = pdf_file.render(
        pdfium.PdfBitmap.to_pil,
        page_indices=page_indices,
        scale=scale,
    )

    # Create a list to collect all rendered images
    images_list = [image for image in renderer]

    # Concatenate images vertically
    concatenated_image = Image.new('RGB', (images_list[0].width, sum(im.height for im in images_list)))
    y_offset = 0
    for im in images_list:
        concatenated_image.paste(im, (0, y_offset))
        y_offset += im.height

    # Save the concatenated image
    image_file_path = os.path.join('images', 'all_pages.jpeg')
    concatenated_image.save(image_file_path, format='jpeg', optimize=True)

    return image_file_path


def extract_text_from_img(list_dict_final_images):

    image_list = [list(data.values())[0] for data in list_dict_final_images]
    image_content = []
    for index, image_bytes in enumerate(image_list):

        image = Image.open(BytesIO(image_bytes))
        raw_text = str(image_to_string(image))
        image_content.append(raw_text)
    return "\n".join(image_content)

def extract_content_from_url(url: str):
    images_list = convert_pdf_to_images(url)
    return images_list

# 3. Extract structured info from text via LLM
def extract_structured_data(content: str, data_points):
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")
    template = """
    You are an expert admin people who will extract core information from documents

    {content}

    Above is the content; please try to extract all data points from the content above 
    and export in a JSON array format:
    {data_points}

    Now please extract details from the content  and export in a JSON array format, 
    return ONLY the JSON array:
    """

    prompt = PromptTemplate(
        input_variables=["content", "data_points"],
        template=template,
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    results = chain.run(content=content, data_points=data_points)

    return results



@app.route('/hello', methods=['GET'])
def get_hello():
    return jsonify(message='hello world'), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    default_data_points = """{
        "invoice_item": "what is the item that charged",
        "Amount": "how much does the invoice item cost in total",
        "Company_name": "company that issued the invoice",
        "invoice_date": "when was the invoice issued",
    }"""
    if 'file0' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    files = [request.files[f] for f in request.files]
    dataFiles = []
    for file in files:
        if file.filename == '':
            return 'No selected file', 400
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            content = extract_content_from_url(filename)
            result = run(['node', 'ocr_service.js', "images/all_pages.jpeg"], stdout=PIPE, stderr=PIPE)
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8').strip()
                print("Error:", error_msg)
                return jsonify({"error": "Failed to extract text using OCR"}), 500
            ocr_text = result.stdout.decode('utf-8').strip()
            print(ocr_text)
    return dataFiles, 200

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run()
    """ from waitress import serve
    serve(app, host="127.0.0.1", port=8080) """


