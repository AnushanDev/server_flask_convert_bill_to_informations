#python app.py
from pypdf import PdfReader
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import json

app = Flask(__name__)
CORS(app)
load_dotenv()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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


def convert_pdf_to_text(path_pdf):
    reader = PdfReader(path_pdf)
    number_of_pages = len(reader.pages)
    page = reader.pages[0]
    text = page.extract_text()
    return text


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
            monTxt = convert_pdf_to_text(filename)
            data = extract_structured_data(monTxt, default_data_points)
            json_data = json.loads(data)
            dataFiles += json_data
    return dataFiles, 200

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run()


