from flask import Flask, jsonify
import json

app = Flask(__name__)

from flask_cors import CORS
CORS(app)

@app.route('/api/alerts')
def get_alerts():
    with open('../output/nlp_alerts.json') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=2027, debug=True)