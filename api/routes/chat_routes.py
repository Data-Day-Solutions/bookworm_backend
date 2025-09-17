from flask import request, jsonify
from flask import Blueprint

try:
    from ragbot_tools.rag_chatbot_function import run_chatbot
except (ImportError, ModuleNotFoundError):
    from api.ragbot_tools.rag_chatbot_function import run_chatbot

try:
    from tools.supabase_functions import check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import check_session


chat_bp = Blueprint("chat", __name__)


@chat_bp.route('/chatbot', methods=['POST'])
def chatbot():

    """
    Chat with Buddy
    ---
    tags:
      - Chat
    post:
      description: Send a prompt to the chatbot and receive a response.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_prompt:
                  type: string
                  example: "Tell me a joke about books."
      responses:
        200:
          description: Chatbot successfully processed the prompt
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: "Successfully processed prompt."
                  data:
                    type: string
                    example: "Why did the book go to the doctor? Because it had a bad spine!"
        401:
          description: Unauthorized - user is not authenticated
    """

    if check_session():

        data = request.get_json()
        user_prompt = data.get('user_prompt')
        chatbot_response = run_chatbot(user_prompt)

        return jsonify({"message": "Successfully processed prompt.", "data": chatbot_response}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@chat_bp.route('/chatbot/example', methods=['GET'])
def chatbot_example():

    """
    Chatbot Example Endpoint
    ---
    tags:
      - Chat
    get:
      description: Get a sample chatbot response without authentication.
      responses:
        200:
          description: Example chatbot response
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: "Example chatbot response."
                  data:
                    type: string
                    example: "Hello! I'm Buddy, your friendly chatbot 😄"
    """

    return jsonify({
        "message": "Example chatbot response.",
        "data": "Hello! I'm Buddy, your friendly chatbot 😄"
    }), 200
