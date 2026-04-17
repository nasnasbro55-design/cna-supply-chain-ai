from flask import Flask, jsonify
import json
import subprocess
import os

app = Flask(__name__)

from flask_cors import CORS
CORS(app)

@app.route('/api/alerts')
def get_alerts():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base_dir, 'output', 'nlp_alerts.json')) as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/refresh', methods=['POST'])
def refresh_alerts():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(
            ['python3', 'scripts/generate_nlp_alerts.py'],
            input='n\n',
            text=True,
            cwd=base_dir
        )
        return jsonify({"status": "refreshed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=2027, debug=True)
