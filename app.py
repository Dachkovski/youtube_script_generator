from flask import Flask, request, jsonify, abort
import autogen
import os
import logging
import re
import uuid
import threading

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)

# Configuration
PORT = os.environ.get("PORT", 5001)

# API Key Validation Pattern
API_KEY_PATTERN = r"^sk-[A-Za-z0-9]{48}$"

# Dictionary to store ongoing requests and their results
ongoing_requests = {}

def process_request(request_id, api_key, style, topic):
    config_list = [
        {
            'model': 'gpt-4',
            'api_key': api_key
        }
    ]

    llm_config = {
        "request_timeout": 600,
        "seed": 42,
        "config_list": config_list,
        "temperature": 0
    }

    editor = autogen.AssistantAgent(
        name="content_editor",
        llm_config=llm_config,
        system_message=f"Experienced youtube content editor."
    )

    writer = autogen.AssistantAgent(
        name="script_writer",
        llm_config=llm_config,
        system_message=f"Script writer with a proven record in writing viral video scripts for successful youtubers."
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={"work_dir": "groupchat"},
        llm_config=llm_config,
        system_message="Reply TERMINATE if the task has been solved at full satisfaction. Otherwise, reply CONTINUE, or the reason why the task is not solved yet."
    )

    groupchat = autogen.GroupChat(agents=[user_proxy, editor, writer], messages=[], max_round=12)
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    task = f"Give me a viral youtube {style} script about current events about the topic: '{topic}'. Separate the script into scenes. Each scene is separated by a ';'. Only output the script text. Don't output any meta descriptions like 'scene:' or (opening shot) etc., just the text. Make sure the topic is trending and edited."

    user_proxy.initiate_chat(manager, message=task, clear_history=True)

    ongoing_requests[request_id]['result'] = groupchat.messages[-2]['content'].strip('\n')
    ongoing_requests[request_id]['status'] = 'completed'


@app.route('/submit_script_request', methods=['POST'])
def submit_script_request():
    data = request.get_json()
    logging.info(f"Received request data: {data}")

    if not data:
        abort(400, "Invalid data format")

    topic = data.get('topic')
    style = data.get('style')
    api_key = data.get('api_key')

    if not topic:
        abort(400, "Missing topic in request data")

    if not api_key:
        abort(400, "Missing api_key in request data")

    if not style:
        abort(400, "Missing style in request data")

    if not re.match(API_KEY_PATTERN, api_key):
        abort(403, "Invalid API key structure")

    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())

    # Store the request data in the dictionary with a 'processing' status
    ongoing_requests[request_id] = {
        'status': 'processing',
        'result': None
    }

    # Start a new thread to process the request in the background
    thread = threading.Thread(target=process_request, args=(request_id, api_key, style, topic))
    thread.start()

    response = jsonify(request_id=request_id)
    logging.info(f"Response data: {response.get_json()}")
    # Return the unique ID to the client
    return response


@app.route('/get_script_result/<request_id>', methods=['GET'])
def get_script_result(request_id):
    logging.info(f"Received request for ID: {request_id}")
    request_data = ongoing_requests.get(request_id)

    if not request_data:
        abort(404, "Request ID not found")

    if request_data['status'] == 'processing':
        response = jsonify(status='processing')
        logging.info(f"Response data: {response.get_json()}")
        return response

    response = jsonify(status='completed', result=request_data['result'])
    logging.info(f"Response data: {response.get_json()}")
    return response

@app.errorhandler(400)
def bad_request(error):
    return jsonify(error=str(error)), 400

@app.errorhandler(403)
def forbidden(error):
    return jsonify(error=str(error)), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify(error=str(error)), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify(error=str(error)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
