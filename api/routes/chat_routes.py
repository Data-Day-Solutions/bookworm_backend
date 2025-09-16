try:
    from ragbot_tools.rag_chatbot_function import run_chatbot
except (ImportError, ModuleNotFoundError):
    from api.ragbot_tools.rag_chatbot_function import run_chatbot

try:
    from tools.supabase_functions import check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import check_session

from flask import request, jsonify
from flask import Blueprint

chat_bp = Blueprint("chat", __name__)

# routes = []


@chat_bp.route('/chatbot', methods=['POST'])
def chatbot():

    """
    Chatbot List Endpoint
    ---
    post:
      description: Chat with Buddy
      responses:
        200:
          description: A list of books
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 1
                    title:
                      type: string
                      example: "The Hobbit"
    """

    if check_session():

        data = request.get_json()
        user_prompt = data.get('user_prompt')
        chatbot_response = run_chatbot(user_prompt)

        return jsonify({"message": "Successfully processed prompt.", "data": chatbot_response}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# routes.append(dict(
#     rule='/chatbot',
#     view_func=chatbot,
#     options=dict(methods=['POST'])))
