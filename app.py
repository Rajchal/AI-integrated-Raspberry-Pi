import os
from flask import Flask, request, jsonify
import requests
import json

# Environment vars
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:0.6b')
FLASK_PORT = int(os.getenv('FLASK_PORT', 3000))


app = Flask(__name__)

classification = 'average'  # Default classification

@app.route('/')
def index():
    return jsonify({"message": "Fast LLM API is running."})

@app.route('/ask', methods=['POST'])
def ask_question():
    global classification
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    question = data.get('question')
    think_bool= data.get('think', False)
    if not user_id or not question:
        return jsonify({'error': 'user_id and question are required'}), 400
    try:
        perf_resp = requests.get(f'http://192.168.4.1/student-performance/{user_id}', timeout=5)
        perf_resp.raise_for_status()
        perf_data = perf_resp.json()
        print(perf_data)
        if 'classification' in perf_data:
            classification = perf_data['classification']
    except Exception:
        return jsonify({'error': 'Failed to fetch user performance data'}), 500

    classes = {
        '90-100': 'gifted',
        '80-90': 'excellent',
        '70-80': 'good',
        '60-70': 'above average',
        '50-60': 'below average',
        '40-50': 'struggling',
        '30-40': 'needs improvement',
        '20-30': 'significantly behind',
        '10-20': 'severely behind',
        '0-10': 'critical'
    }
    # Short prompt based on classification only
    intellect = classes.get(classification, 'average')
    instruction = {
        'gifted': "Explain in detail like i have a very high iq:",
        'excellent': "Explain in detail like i have a high iq:",
        'good': "Explain in detail like i have an average iq:",
        'above average': "Explain simply like i am 10 yrs old:",
        'below average': "Explain simply like i am 10 yrs old:",
        'struggling': "Explain simply like i am 10 yrs old:",
        'needs improvement': "Explain simply like i am 10 yrs old:",
        'significantly behind': "Explain simply like i am 10 yrs old:",
        'severely behind': "Explain simply like i am 10 yrs old:",
        'critical': "Explain simply like i am 10 yrs old:",
    }.get(intellect, "Answer this normal as i am an average kid:")
    if think_bool:
        prompt = f"{instruction} {question}"
    else:
        prompt = f"/no_think {instruction} {question}"

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "num_predict": 50,  # shorter, faster
                "stream": False
            },
            timeout=90  # shorter timeout
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Model request failed: {e}'}), 500

    answer = response.json().get('response', 'Sorry, no response.')
    return jsonify({
        'user_id': user_id,
        'question': question,
        'answer': answer+ f" (Classification: {classification})",
    })



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)