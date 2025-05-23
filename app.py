import os
from flask import Flask, request, jsonify
import requests

# Environment vars
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi:latest')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))


app = Flask(__name__)

# In-memory storage (only)
users = {}

@app.route('/')
def index():
    return jsonify({"message": "Fast LLM API is running."})

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    question = data.get('question')
    if not user_id or not question:
        return jsonify({'error': 'user_id and question are required'}), 400

    user = users.get(user_id, {'intellect': 'normal'})
    intellect = user.get('intellect', 'normal')

    # Short prompt based on intellect only
    instruction = {
        'high': "Explain in detail like i have a very high iq:",
        'low': "Explain simply like i am 10 yrs old:",
    }.get(intellect, "Answer this normal as i am an average kid:")

    prompt = f"{instruction} {question}"

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "num_predict": 50,  # shorter, faster
                "stream": False
            },
            timeout=30  # shorter timeout
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Model request failed: {e}'}), 500

    answer = response.json().get('response', 'Sorry, no response.')
    return jsonify({
        'user_id': user_id,
        'question': question,
        'answer': answer
    })

@app.route('/user/<user_id>', methods=['PUT'])
def set_user_intellect(user_id):
    data = request.get_json(force=True, silent=True) or {}
    intellect = data.get('intellect', 'normal').lower()
    if intellect not in {'low', 'normal', 'high'}:
        return jsonify({'error': 'Intellect must be "low", "normal", or "high".'}), 400
    users[user_id] = {'intellect': intellect}
    return jsonify({'user_id': user_id, 'intellect': intellect})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
