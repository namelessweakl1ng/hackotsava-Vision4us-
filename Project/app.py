from flask import Flask, render_template, request, jsonify
import os, json, uuid
from google import genai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

client = genai.Client()

DATA_FILE = "data/results.json"

def save_result(user_id, result):
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    data[user_id] = result

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save uploaded image
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Send to Gemini API
    with open(filepath, "rb") as f:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[f, "Describe this image in detail and provide any relevant audio/video references."]
        )

    description = response.text if hasattr(response, "text") else str(response)

    # Example dummy iframe URLs (replace with real ones if available)
    video_iframe = "<iframe width='560' height='315' src='https://www.youtube.com/embed/dQw4w9WgXcQ'></iframe>"
    audio_iframe = "<iframe src='https://open.spotify.com/embed/track/4uLU6hMCjMI75M1A2tKUQC'></iframe>"

    user_id = f"user-{uuid.uuid4().hex[:6]}"

    result = {
        "description": description,
        "video_iframe": video_iframe,
        "audio_iframe": audio_iframe
    }

    save_result(user_id, result)

    return jsonify({
        "user_id": user_id,
        "description": description,
        "video_iframe": video_iframe,
        "audio_iframe": audio_iframe
    })

if __name__ == '__main__':
    app.run(debug=True)
