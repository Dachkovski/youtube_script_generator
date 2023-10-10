from flask import Flask, request, jsonify, abort
import autogen
import os
import logging
import re

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)

# Configuration
PORT = os.environ.get("PORT", 5001)

# API Key Validation Pattern
API_KEY_PATTERN = r"^sk-[A-Za-z0-9]{43}$"

@app.route('/generate_script', methods=['POST'])
def generate_script():
    data = request.get_json()

    if not data:
        abort(400, "Invalid data format")

    topic = data.get('topic')
    api_key = data.get('api_key')
    form = data.get('form')

    if not topic:
        abort(400, "Missing topic in request data")

    if not api_key:
        abort(400, "Missing api_key in request data")

    if not form:
        abort(400, "Missing 'longform/shortform' in request data")

    if not re.match(API_KEY_PATTERN, api_key):
        abort(403, "Invalid API key structure")

    config_list = [
        {
            'model': 'gpt-4',
            'api_key': api_key
        }
    ]

    llm_config={
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

    task = f"Give me a viral youtube {form} script about current events about the topic: '{topic}'. Separate the scipt into scenes. Each scene is sperarated by a ';'. Only output the script text. Don't output any meta descriptions like 'scene:' oder (opening shot) etc.', just the text. Make sure the topic is trending and edited."


    result = user_proxy.initiate_chat(manager, message=task)

    return jsonify(result)

@app.errorhandler(400)
def bad_request(error):
    return jsonify(error=str(error)), 400

@app.errorhandler(403)
def forbidden(error):
    return jsonify(error=str(error)), 403

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify(error="Internal Server Error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
