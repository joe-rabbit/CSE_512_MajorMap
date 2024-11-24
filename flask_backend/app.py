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

# Deleting the existing index if it exists
if client.indices.exists(index="course_index"):
    client.indices.delete(index="course_index")

# Define the updated mapping
mappings = {
    "mappings": {
        "properties": {
            "id": {
                "type": "keyword"  # Used for exact matches (lexical search)
            },
            "Subject_Name": {
                "type": "text",  # String field for full-text search
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "Description": {
                "type": "text"
            },
            "Critical_Requirment": {
                "type": "keyword"
            },
            "Optional": {
                "type": "keyword"
            },
            "Minimum_Passing_Grade": {
                "type": "keyword"
            },
            "Total_Credits": {
                "type": "keyword"
            },
            "Next_Subject_Code": {
                "type": "keyword"
            },
            "Category": {
                "type": "keyword"
            },
            "Session": {
                "type": "keyword"
            },
            "Semester": {
                "type": "keyword"
            },
            "prior_requirements": {
                "type": "keyword"
            },
            "mandatory_priors": {
                "type": "keyword"
            },
            "subject_name_vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

# Create the index with the updated mapping
client.indices.create(index="course_index", body=mappings)

# Load data from the provided URL
url = "https://joe-rabbit.github.io/subjects_elastic_search/data.json"
response = urlopen(url)
courses = json.loads(response.read())

# Prepare operations for bulk indexing
operations = []
for course in courses:
    # Ensure all fields are strings and transform the Subject_Name into an embedding
    for key, value in course.items():
        if not isinstance(value, str):
            course[key] = str(value)

    if isinstance(course["Subject_Name"], str):
        try:
            # Transforming the Subject_Name into an embedding using the model
            course["subject_name_vector"] = model.encode(course["Subject_Name"]).tolist()
            operations.append({"index": {"_index": "course_index"}})
            operations.append(course)
        except Exception as e:
            print(f"Error processing course ID {course.get('id')}: {e}")
    else:
        print(f"Skipping course with non-string Subject_Name: {course.get('id')}")

# Debug print a sample document
if operations:
    print("Sample document to be indexed:", operations[1])

# Use the client to bulk index the transformed data
response = client.bulk(index="course_index", operations=operations, refresh=True)

# Check for any errors in the response

if response['errors']:
    print("Errors occurred during bulk indexing:", response)
# response = client.search(
#     index="course_index",
#     query={
#         "bool": {
#             "filter": [
#                 {"term": {"Subject_Name.keyword": "Principles of Programming Java"}}  # Exact match on Subject_Name
#             ]
#         }
#     },
#     size=10  # Adjust the number of results as needed
# )
# print(response)
def search_courses(course_id=None, subject_name=None, subject_code=None, category=None, semester=None,
                   description=None, critical_requirement=None, total_credits=None, next_subject_code=None,
                   prior_requirement=None, session=None, optional=None, minimum_passing_grade=None):
    should_conditions = []

    # Add conditions based on provided parameters
    if course_id:
        should_conditions.append({"term": {"id": str(course_id)}})
    if subject_name:
        should_conditions.append({"term": {"Subject_Name.keyword": subject_name}})
    if subject_code:
        should_conditions.append({"term": {"Subject_Code.keyword": subject_code}})
    if category:
        should_conditions.append({"term": {"Category.keyword": category}})
    if semester:
        should_conditions.append({"wildcard": {"Semester": f"*{semester}*"}})
    if description:
        should_conditions.append({"match": {"Description": description}})
    if critical_requirement:
        should_conditions.append({"term": {"Critical_Requirement": critical_requirement}})
    if total_credits:
        should_conditions.append({"term": {"Total_Credits": total_credits}})
    if next_subject_code:
        should_conditions.append({"term": {"Next_Subject_Code.keyword": next_subject_code}})
    if prior_requirement:
        should_conditions.append({"term": {"Prior_Requirement.keyword": prior_requirement}})
    if session:
        should_conditions.append({"term": {"Session.keyword": session}})
    if optional:
        should_conditions.append({"term": {"Optional": optional}})
    if minimum_passing_grade:
        should_conditions.append({"term": {"Minimum_Passing_Grade.keyword": minimum_passing_grade}})

    # Construct the query with a minimum should match condition
    query = {
        "bool": {
            "should": should_conditions,
            "minimum_should_match": 1  # Adjust as needed
        }
    }

    # Execute the search query
    response = client.search(
        index="course_index",
        query=query,
        size=10  # Adjust size based on your requirement
    )

    # Filter response to only include specified fields
    filtered_response = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        filtered_hit = {
            'Course Codes': [source.get('id')],
            'Categories': [source.get('Category', '')],
            'Semesters': [source.get('Semester', '')],
            'Description': [source.get('Description', '')],
            'Critical Requirement': [source.get('Critical_Requirement', '')],
            'Total Credits': [source.get('Total_Credits', '')],
            'Next Subject Codes': [source.get('Next_Subject_Code', '')],
            'Prior Requirements': [source.get('prior_requirements', '')],
            'Category': [source.get('Category', '')],
            'Session': [source.get('Session', '')],
            'Optional': [source.get('Optional', '')],
            'Minimum_passing_Grade': [source.get('Minimum_Passing_Grade', '')]
        }
        filtered_response.append(filtered_hit)
        print(filtered_response)

    return filtered_response




def get_elasticsearch_results(question):
    global first_run

    if first_run:
        # Run a match_all query on the first execution
        first_run = False  # Update the flag after the first run
        response = client.search(
            index="course_index",
            query={"match_all": {}},
            size=10  # Adjust the size as needed
        )
        # Filter response to only include specified fields
        filtered_response = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            filtered_hit = {
                'Course Codes': [source.get('id')],
                'Categories': [source.get('Category', '')],
                'Semesters': [source.get('Semester', '')],
                'Description': [source.get('Description', '')],
                'Critical Requirement': [source.get('Critical_Requirement', '')],
                'Total Credits': [source.get('Total_Credits', '')],
                'Next Subject Codes': [source.get('Next_Subject_Code', '')],
                'Prior Requirements': [source.get('prior_requirements', '')],
                'Category': [source.get('Category', '')],
                'Session': [source.get('Session', '')],
                'Optional': [source.get('Optional', '')],
                'Minimum_passing_Grade': [source.get('Minimum_Passing_Grade', '')]
            }
            filtered_response.append(filtered_hit)
        return filtered_response
    else:
        # Use GPT to parse the question to extract course details
        parsed_output = parse_question_with_gpt(question)

        if not isinstance(parsed_output, dict):
            print("Parsing failed or returned unexpected format. Raw output:", parsed_output)
            return []



        # Extract all course details from parsed_output
        course_ids = parsed_output.get("Course Codes", [])
        categories = parsed_output.get("categories", [])
        semesters = parsed_output.get("semesters", [])
        descriptions = parsed_output.get("Description", [])
        critical_requirements = parsed_output.get("Critical Requirement", [])
        total_credits = parsed_output.get("Total Credits", [])
        next_subject_codes = parsed_output.get("Next Subject Codes", [])
        prior_requirements = parsed_output.get("Prior Requirements", [])
        sessions = parsed_output.get("Session", [])
        optional_flags = parsed_output.get("Optional", [])
        minimum_passing_grades = parsed_output.get("Minimum_passing_Grade", [])

        # Combine all course details into a list of dictionaries for processing
        responses = []
        if course_ids:
            for i, course_id in enumerate(course_ids):
                response_data = {
                    "course_id": course_id,
                    "category": categories[i] if i < len(categories) else None,
                    "semester": semesters[i] if i < len(semesters) else None,
                    "description": descriptions[i] if i < len(descriptions) else None,
                    "critical_requirement": critical_requirements[i] if i < len(critical_requirements) else None,
                    "total_credits": total_credits[i] if i < len(total_credits) else None,
                    "next_subject_code": next_subject_codes[i] if i < len(next_subject_codes) else None,
                    "prior_requirement": prior_requirements[i] if i < len(prior_requirements) else None,
                    "session": sessions[i] if i < len(sessions) else None,
                    "optional": optional_flags[i] if i < len(optional_flags) else None,
                    "minimum_passing_grade": minimum_passing_grades[i] if i < len(minimum_passing_grades) else None
                }
                # Append the processed response to the list
                print(response_data)
                responses.append(search_courses(**response_data))
                # pretty_response(responses)
            return responses
        else:
            return []

# Function to parse question with GPT
def parse_question_with_gpt(question):
    # Create the parsing prompt with more explicit instructions
    prompt = f"""
    Instructions:
    - You are an advanced language parser.
    - Extract and return only the specified details from the given question.
    - Extract:
      - Course Codes (e.g., CSE 330, MAT 101, EEE 220)
      - Categories (e.g., 'Gold', 'Silver', 'Elective', 'Core')
      - Semesters (e.g., 1, 2, spring, fall)
      - Description (e.g., An introductory course that teaches the fundamentals of problem-solving using the Java programming language. The course covers algorithm design, structured programming concepts, basic algorithms, techniques, and an overview of computer systems. Social and ethical responsibilities in programming are also discussed.)
      - Critical Requirement (e.g., True)
      - Total Credits (e.g., 3)
      - Next Subject Codes (e.g., 'CSE 230')
      - Prior Requirements (e.g., 'CSE 110')
      - Category include 'Gold' and 'SCIT'
      - Session (e.g., 'C')
      - Optional (e.g., 'False')
      - Minimum Passing Grade (e.g., 'C')

    - If any of the above details are not found, return them as empty lists (e.g., "Course Codes": [], "Categories": [], "Semesters": [],...).
    - Ensure that 'Prior Requirements' and 'Next Subject Codes' are also included in 'Course Codes'.

    Format your output strictly as a JSON object in this format:
    {{
        "Course Codes": [],
        "Categories": [],
        "Semesters": [],
        "Description": [],
        "Critical Requirement": [],
        "Total Credits": [],
        "Next Subject Codes": [],
        "Prior Requirements": [],
        "Category": [],
        "Session": [],
        "Optional": [],
        "Minimum_passing_Grade": []
    }}

    Question:
    {question}
    """

    # Send the prompt to OpenAI's API and get the response
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a specialized text extraction tool."},
            {"role": "user", "content": prompt},
        ]
    )

    # Clean and parse the response
    response_text = response.choices[0].message.content.strip()

    # Find the first occurrence of '{' and the last occurrence of '}'
    json_start = response_text.find('{')
    json_end = response_text.rfind('}')
    if json_start != -1 and json_end != -1:
        response_text = response_text[json_start:json_end + 1]

    # Attempt to parse the response as JSON
    try:
        response_json = json.loads(response_text)

        # Ensure 'Prior Requirements' and 'Next Subject Codes' are added to 'Course Codes'
        response_json['Course Codes'].extend(response_json.get('Prior Requirements', []))
        response_json['Course Codes'].extend(response_json.get('Next Subject Codes', []))

        return response_json
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        print("Returning raw response for manual inspection.")
        return response_text



# Elasticsearch query to get initial results or search based on question


# Function to store course information in context
def store_course_info(openai_completion):
    parsed_output = parse_question_with_gpt(openai_completion)
    course_map_data.append(parsed_output)
    return course_map_data




# Function to store and process course information
def store_course_info(openai_completion):
    global course_counter

    # Parse the output to extract course codes, prior requirements, and next subject codes
    parsed_output = parse_question_with_gpt(openai_completion)
    # print(parsed_output)
    parsed_outputs = get_elasticsearch_results(parsed_output)
       # Store the context in the course map data
    course_map_data.append(parsed_outputs)
    # print(parsed_outputs)
    parsed_output_1 = parse_question_with_gpt(parsed_outputs)
    # print(parsed_output_1)
    parsed_outputs = get_elasticsearch_results(parsed_output_1)
    course_map_data.append(parsed_outputs)
    # print(parsed_outputs)

    # Create a context for GPT




    return course_map_data

# Function to create a prompt for OpenAI completion
def create_openai_prompt(results):
    context = store_course_info("")
    prompt = f"""
    Instructions:
    - You are an assistant for student advising and helping students finish course soon.
    - Answer questions truthfully and factually using only the context presented.
    - You are correct, factual, precise, and reliable.
    - All Students have to take a SCIT course
    -BELOW IS THE ALEK TEST U NEED TO ASK STUDENTS BEFORE ANSWERING IF THEY SCORE 0-60 THEY GET PLACED IN MAT 117
    - IF ITS 61-75 YOU GET PLACED IN MAT 170
    - 76-100 YOU GET MAT 265.
    - SCIT Category include PHY 101,PHY 180 and PHY 220
    -CHEM 101 , CHEM 160 and CHEM 220
    - BIO 101,BIO 160 and BIO 220
    -You need to guide student to take either physics fully or chemistry fully or bio fully and cant switch
    -by default assume score for ALEK test to be 75
 

    Context:
    {(context,results)}
    """
    return prompt
def execute_store_info_in_thread(openai_completion):
    # Create and start a thread for `store_course_info`
    thread = threading.Thread(target=store_course_info, args=(openai_completion,))
    thread.start()
    return thread

def generate_openai_completion(user_prompt, question):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": user_prompt},
            {"role": "user", "content": question},
        ]
    )
    return response.choices[0].message.content

def generate_course_map_with_gpt():
    # Get the context from stored course information
    context = store_course_info("")
    print(context)
    if not context:
        return "No course data available to generate a map."

    # Create a prompt for GPT
    prompt = f"""
    Instructions:
    - You are an assistant tasked with generating a comprehensive course map.
    - Use the provided context to create a descriptive map that outlines courses, their prior requirements, next subjects, and other relevant details.
    -Make sure to make a map for all codes courses It should be comprehensive from 1st sem to 8th sem
    -Make sure to cover all critical subjects
    -Make sure to address prequists in the previous semesters if you gonna print the next sem subjects as well

    Context:
    {context}

    Generate a well-structured map describing the relationships and details of each course.
    """

    # Generate the map using GPT
    openai_completion = generate_openai_completion(prompt, "Create a course map based on the context.")
    return openai_completion
# Main route to handle user questions
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get("question", "")
    # Main loop to process user input, store data, and generate a course map
    if question.lower() == "map":
        # Generate the course map using GPT
        course_map = generate_course_map_with_gpt()
        return jsonify({"response": f"Course Map: {course_map}"})

    # Run the parser and Elasticsearch search for user questions
    openai_completion = parse_question_with_gpt(question)

    # Run `store_course_info` in a separate thread
    thread = execute_store_info_in_thread(openai_completion)

    # Print the result of the question (this runs on the main thread)
    elastic_search_result = get_elasticsearch_results(question)
    print(elastic_search_result)
    context_prompt = create_openai_prompt(elastic_search_result)
    openai_response = generate_openai_completion(context_prompt, question)
    # print(openai_response)

    return jsonify({"response": openai_response})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
