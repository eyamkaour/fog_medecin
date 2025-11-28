from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/receive_data", methods=["POST"])
def receive_data():
    data = request.json
    print("Données reçues du Fog:", data)  # Affiche tout dans le terminal
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
