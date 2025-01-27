from flask import Flask, request, jsonify, send_file
from transformers import AutoTokenizer, AutoModelForCausalLM
from diffusers import StableDiffusionPipeline
import torch
import textwrap
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip
from gtts import gTTS
from fpdf import FPDF
import re
import os
from flask_cors import CORS
import base64
from io import BytesIO
from googleapiclient.discovery import build
import json
# Initialize the Flask app
app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# Your YouTube API Key
API_KEY = 'API_KEY'
SEARCH_ENGINE_ID = 'SEARCH_ENGINE_ID'

# Create YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Store feedback in a JSON file
FEEDBACK_FILE = "feedback.json"

class TextImageVideoGenerator:
    def __init__(self, text_model_name='EleutherAI/gpt-neo-1.3B',
                 image_model_name='runwayml/stable-diffusion-v1-5'):
        # Text generation setup
        self.tokenizer = AutoTokenizer.from_pretrained(text_model_name)
        self.text_model = AutoModelForCausalLM.from_pretrained(text_model_name)

        # Image generation setup
        self.image_pipeline = StableDiffusionPipeline.from_pretrained(
            image_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        if torch.cuda.is_available():
            self.image_pipeline = self.image_pipeline.to("cuda")

    def generate_text(self, prompt, max_length=500):
    
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids

    # Generate text with attention mask and explicitly set pad_token_id
        output = self.text_model.generate(
        input_ids,
        max_length=max_length,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        do_sample=True,
        pad_token_id=self.tokenizer.eos_token_id  # Explicitly set the pad_token_id
    )

        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return generated_text

    def extract_image_prompts(self, text):
        paragraphs = text.split("\n\n")
        prompts = []
        for paragraph in paragraphs:
            words = re.findall(r'\b\w+\b', paragraph.lower())
            common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'])
            key_words = [word for word in words if word not in common_words]
            prompts.append(" ".join(key_words[:10]))
        return prompts

    
    # Function to get image links from Google Custom Search
    def get_images(self, query, num_images=5):
        service = build('customsearch', 'v1', developerKey=API_KEY)
        request = service.cse().list(
            q=query,
            cx=SEARCH_ENGINE_ID,
            searchType='image',
            num=num_images,
            imgSize='MEDIUM',
            fileType='png',
            fields='items(link)'
        )
        response = request.execute()
        image_links = [item['link'] for item in response.get('items', [])]
        return image_links

    def get_youtube_link(self,prompt):
    
        request = youtube.search().list(
            part='snippet',
            q=prompt,
            type='video',
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            return f'https://www.youtube.com/watch?v={video_id}'
        else:
            return 'No relevant video found.'
    


    
# Initialize the generator
generator = TextImageVideoGenerator()


@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': 'Prompt is required.'}), 400

    try:
        # Generate text
        print("Generating text...")
        generated_text = generator.generate_text(prompt)
        print("Generated text successfully.")
        
        # Extract image prompts
        print("Extracting image prompts...")
        image_prompts = generator.extract_image_prompts(generated_text)
        print("Image prompts:", image_prompts)
        

        # Fetch additional images using Google Custom Search
        print("Fetching images")
        additional_image_links = generator.get_images(query=prompt)  # Pass query as keyword argument
        print("Fetched additional images successfully.")

        # Fetch YouTube link using the instance method
        print("Fetching YouTube link...")
        video_link = generator.get_youtube_link(prompt)
        print("YouTube link fetched successfully:", video_link)


        return jsonify({
            'text': generated_text,
            'youtube_link': video_link,
            'additional_image_links': additional_image_links
            
        })

    except Exception as e:
        print("Error occurred:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/search_images', methods=['POST'])
def search_images():
    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': 'Prompt is required.'}), 400

    print("Searching for images...")
    image_links = get_images(prompt, num_images=5)

    if not image_links:
        return jsonify({'error': 'No images found.'}), 404

    # Return the image links to the frontend
    return jsonify({'images': image_links})   

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    Route to download generated files.
    """
    return send_file(filename, as_attachment=True)

# Save feedback
@app.route('/feedback', methods=['POST'])
def save_feedback():
    feedback_data = request.json
    if not feedback_data.get('name') or not feedback_data.get('email') or not feedback_data.get('message'):
        return jsonify({'error': 'All fields are required.'}), 400

    try:
        # Read existing feedback
        if not os.path.exists(FEEDBACK_FILE):
            feedback_list = []
        else:
            with open(FEEDBACK_FILE, 'r') as file:
                feedback_list = json.load(file)

        # Add new feedback
        feedback_list.append(feedback_data)

        # Save updated feedback
        with open(FEEDBACK_FILE, 'w') as file:
            json.dump(feedback_list, file, indent=4)

        return jsonify({'success': 'Feedback saved successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# View all feedback
@app.route('/feedback', methods=['GET'])
def view_feedback():
    try:
        if not os.path.exists(FEEDBACK_FILE):
            return jsonify({'feedback': []}), 200

        with open(FEEDBACK_FILE, 'r') as file:
            feedback_list = json.load(file)
        return jsonify({'feedback': feedback_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
