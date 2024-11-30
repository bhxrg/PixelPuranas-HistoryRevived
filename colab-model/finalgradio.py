# -*- coding: utf-8 -*-
"""finalgradio.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TxBwVEIUDpGDX_mWLRi4sKeDkJ8DcIcV
"""

# Install required packages
!pip install google-api-python-client gtts moviepy gradio transformers reportlab

# Install necessary packages
# Uncomment the below line to install packages in your environment
# !pip install google-api-python-client gtts transformers gradio torch pillow

# Import required libraries
from googleapiclient.discovery import build
from gtts import gTTS
from PIL import Image
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import requests
from io import BytesIO
import textwrap
import torch
import time  # For performance metrics
import gradio as gr

# Set up API keys (replace with your actual keys)
API_KEY = 'YOUR_API_KEY'
SEARCH_ENGINE_ID = 'YOUR_SEARCH_ENGINE_ID'

# Initialize the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Set device for model (GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Initialize the text generation model (using GPT-Neo)
text_model_name = 'EleutherAI/gpt-neo-1.3B'
tokenizer = AutoTokenizer.from_pretrained(text_model_name)
text_model = AutoModelForCausalLM.from_pretrained(text_model_name).to(device)

# Function to generate text based on a prompt
def generate_text(prompt, max_length=500):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    output = text_model.generate(
        input_ids,
        max_length=max_length,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        do_sample=True
    )
    generated_text = tokenizer.decode(output[0].cpu(), skip_special_tokens=True)
    wrapper = textwrap.TextWrapper(width=80)
    formatted_text = "\n\n".join(wrapper.fill(line) for line in generated_text.split("\n"))
    return formatted_text

# Function to fetch a relevant YouTube video link
def get_youtube_link(query, max_results=1):
    request = youtube.search().list(
        part='snippet',
        q=query,
        type='video',
        maxResults=max_results
    )
    response = request.execute()
    if response['items']:
        video_id = response['items'][0]['id']['videoId']
        return f'https://www.youtube.com/watch?v={video_id}'
    else:
        return 'No relevant video found.'

# Function to get image links from Google Custom Search
def get_images(query, num_images=5):
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
    return [item['link'] for item in response.get('items', [])]

# Function to generate audio from text
def generate_audio(text, filename='narration.mp3'):
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    return filename

# Modified function to include YouTube autoplay video and link
def generate_text_and_video_with_metrics(prompt):
    start_time = time.time()  # Start timing

    # Generate text
    text_start = time.time()
    generated_text = generate_text(prompt)
    text_end = time.time()

    # Fetch YouTube video
    video_start = time.time()
    video_link = get_youtube_link(prompt)
    video_end = time.time()

    # Extract the video ID from the link
    video_id = video_link.split('v=')[-1]

    # Create an HTML embed code for the YouTube video
    embed_code = f"""
    <iframe width="560" height="315"
    src="https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
    frameborder="0" allow="accelerometer; autoplay; clipboard-write;
    encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
    </iframe>
    """

    # Measure total execution time
    total_time = time.time() - start_time

    # Include performance metrics
    metrics = f"""
    Performance Metrics:
    - Text Generation Time: {text_end - text_start:.2f} seconds
    - Video Fetching Time: {video_end - video_start:.2f} seconds
    - Total Execution Time: {total_time:.2f} seconds
    """

    # Return text, embed, link, and metrics
    return generated_text, embed_code, video_link, metrics

# Gradio Interface setup for text & video generator with metrics
text_video_interface = gr.Interface(
    fn=generate_text_and_video_with_metrics,
    inputs=gr.Textbox(label="Enter a historical or conceptual prompt"),
    outputs=[
        gr.Textbox(label="Generated Text"),
        gr.HTML(label="YouTube Video (Autoplay)"),
        gr.Textbox(label="YouTube Video Link"),
        gr.Textbox(label="Performance Metrics")
    ]
)

# Function to search for images (returns image URLs)
def get_images_gradio(prompt):
    image_links = get_images(prompt)
    return image_links

# Gradio Interface setup for image search
image_interface = gr.Interface(
    fn=get_images_gradio,
    inputs=gr.Textbox(label="Enter a prompt for images"),
    outputs=gr.Gallery(label="Relevant Images")
)

# Combine all interfaces into a single Gradio app with tabs
combined_interface = gr.TabbedInterface(
    [text_video_interface, image_interface],
    ["Text & Video Generator (with Metrics)", "Image Search"]
)

# Launch the Gradio interface
combined_interface.launch(share=True)

