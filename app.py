import os
from flask import Flask, request, jsonify
import requests

# Environment vars
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen:0.5b')
FLASK_PORT = int(os.getenv('FLASK_PORT', 3000))


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
    instruction = generate_ai_prompts(users)

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
            timeout=99  # longer timeout
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
    intellect = data.get('intellect', 'high').lower()
    if intellect not in {'low', 'normal', 'high'}:
        return jsonify({'error': 'Intellect must be "low", "normal", or "high".'}), 400
    users[user_id] = {'intellect': intellect}
    return jsonify({'user_id': user_id, 'intellect': intellect})

# function to give prompt based on user intellect
def generate_ai_prompts(students):
    prompts = {}
    for student, subjects in students.items():
        prompts[student] = {}
        for subject, data in subjects.items():
            level, age_group = calculate_level(data)
            prompt = f"Generate 5 {level} questions in {subject} for a {age_group} student."
            prompts[student][subject] = {
                "level": level,
                "prompt": prompt
            }
    return prompts

def calculate_level(subject_data):
    accuracy = subject_data['correct'] / subject_data['total']
    avg_time = subject_data['avg_time']

    if accuracy < 0.4 or avg_time > 20:
        return "Beginner", "5-year-old"
    elif 0.4 <= accuracy < 0.6:
        return "Intermediate", "10-year-old"
    elif 0.6 <= accuracy < 0.8:
        return "Advanced", "14-year-old"
    else:
        return "Expert", "18-year-old"
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
