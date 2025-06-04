from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    email_response = requests.post('http://email-parser:5000/parse', json=data)
    link_response = requests.post('http://link-analyzer:5000/analyze', json=data)

    email_result = email_response.json()
    link_result = link_response.json()

    verdict_response = requests.post('http://verdict-service:5000/verdict', json={
        'email_result': email_result,
        'link_result': link_result
    })

    return jsonify(verdict_response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)