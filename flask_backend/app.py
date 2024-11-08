from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from openai import OpenAI
import threading
import json
import numpy as np
from scipy.stats import norm
from urllib.request import urlopen

# Initialize Flask app
app = Flask(__name__)

# Set up OpenAI and Elasticsearch clients
API_KEY = "YOUR_OPENAI_API_KEY"
ELASTIC_CLOUD_ID = "YOUR_ELASTIC_CLOUD_ID"
ELASTIC_API_KEY = "YOUR_ELASTIC_API_KEY"

openai_client = OpenAI(api_key=API_KEY)
client = Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    api_key=ELASTIC_API_KEY,
)

# Global variable to store course context data
course_map_data = []
first_run = True

# Function to parse question with GPT
def parse_question_with_gpt(question):
    prompt = f"""
    Instructions:
    - You are an advanced language parser.
    - Extract and return only the specified details from the given question.
    - Extract:
      - Course Codes, Categories, Semesters, Description, Critical Requirement, Total Credits, Next Subject Codes, Prior Requirements, Category, Session, Optional, Minimum Passing Grade.

    Format your output strictly as a JSON object.
    Question: {question}
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a specialized text extraction tool."},
                  {"role": "user", "content": prompt}]
    )
    response_text = response.choices[0].message.content.strip()
    
    try:
        response_json = json.loads(response_text)
        response_json['Course Codes'].extend(response_json.get('Prior Requirements', []))
        response_json['Course Codes'].extend(response_json.get('Next Subject Codes', []))
        return response_json
    except json.JSONDecodeError:
        return {"error": "Failed to parse GPT response"}

# Route for parsing a question
@app.route('/parse_question', methods=['POST'])
def parse_question():
    data = request.json
    question = data.get("question", "")
    parsed_output = parse_question_with_gpt(question)
    return jsonify(parsed_output)

# Elasticsearch query to get initial results or search based on question
@app.route('/search', methods=['POST'])
def get_elasticsearch_results():
    global first_run
    data = request.json
    question = data.get("question", "")
    
    if first_run:
        first_run = False
        response = client.search(index="course_index", query={"match_all": {}}, size=10)
        results = [{'Course Codes': [hit['_source'].get('id')]} for hit in response['hits']['hits']]
        return jsonify(results)
    else:
        parsed_output = parse_question_with_gpt(question)
        if not isinstance(parsed_output, dict):
            return jsonify({"error": "Parsing failed"})
        # Other custom search logic could go here.
        return jsonify(parsed_output)

# Route to generate a course map
@app.route('/generate_course_map', methods=['GET'])
def generate_course_map():
    context = store_course_info("")
    if not context:
        return jsonify({"error": "No course data available to generate a map."})

    prompt = f"""
    Instructions:
    - You are an assistant tasked with generating a comprehensive course map.
    - Generate a well-structured map describing the relationships and details of each course.
    Context: {context}
    """
    openai_response = generate_openai_completion(prompt, "Create a course map.")
    return jsonify({"course_map": openai_response})

# Function to store course information in context
def store_course_info(openai_completion):
    parsed_output = parse_question_with_gpt(openai_completion)
    course_map_data.append(parsed_output)
    return course_map_data

# API call to trigger storing course info
@app.route('/store_course_info', methods=['POST'])
def store_course_info_api():
    data = request.json
    openai_completion = data.get("openai_completion", "")
    thread = threading.Thread(target=store_course_info, args=(openai_completion,))
    thread.start()
    return jsonify({"status": "Storing course info in a separate thread"})

# Function to create a prompt for OpenAI completion
def create_openai_prompt(results):
    context = store_course_info("")
    prompt = f"""
    Instructions:
    - You are an assistant for question-answering tasks.
    Context: {(context, results)}
    """
    return prompt

# OpenAI completion function
def generate_openai_completion(user_prompt, question):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": user_prompt}, {"role": "user", "content": question}]
    )
    return response.choices[0].message.content

# Main route to handle user questions
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get("question", "")

    # Parse question and store data in thread
    openai_completion = parse_question_with_gpt(question)
    thread = threading.Thread(target=store_course_info, args=(openai_completion,))
    thread.start()

    # Generate and return response
    elastic_search_result = get_elasticsearch_results()
    context_prompt = create_openai_prompt(elastic_search_result)
    openai_response = generate_openai_completion(context_prompt, question)
    return jsonify({"response": openai_response})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
