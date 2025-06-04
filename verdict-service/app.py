from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/verdict', methods=['POST'])
def get_verdict():
    data = request.json
    # Here you would implement the logic to analyze the data and provide a verdict
    # For now, we'll return a mock response
    verdict = {
        "status": "safe",  # or "phishing"
        "message": "The link is safe to use."
    }
    return jsonify(verdict), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)