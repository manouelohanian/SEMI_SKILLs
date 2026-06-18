print("STARTING SERVER...")

from flask import Flask, request, jsonify
from analyzer import analyze_test_log

app = Flask(__name__)

API_KEY = "your_secret_key"


@app.route("/analyze", methods=["POST"])
def analyze():
    key = request.headers.get("x-api-key")

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json

    input_file = data.get("input_file")
    sigma_tests = data.get("sigma_tests", [])

    if not input_file:
        return jsonify({"error": "Missing input file"}), 400

    try:
        result = analyze_test_log(input_file, sigma_tests)
        return jsonify({
            "status": "ok",
            "report": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)