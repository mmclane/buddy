from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image
import boto3
import streamlit as st
# from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.editor as mp
import imageio
# from PIL import Image

# Create a client object for Amazon Polly
polly_client = boto3.client('polly', region_name='us-east-1')

# Define a function to convert text to speech using Amazon Polly
def convert_to_speech(text, voice):
    response = polly_client.synthesize_speech(
        Text=text,
        VoiceId=voice,
        OutputFormat='mp3'
    )
    return response['AudioStream'].read()

# Define a function to create a video from an image and speech
def create_video(image_path):
    audioclip = mp.AudioFileClip('text.mp3')
    clip = mp.VideoFileClip(image_path).loop(audioclip.duration)
    
    new_audioclip = mp.CompositeAudioClip([audioclip])
    clip.audio = new_audioclip
    clip.write_videofile("output.webm")
    
def create_image(filenames, output_path):
    with imageio.get_writer(output_path, mode='I') as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)

# text = "Hello, my name is Joanna. I am a text-to-speech bot created using Amazon Polly."
# image = '/home/mmclane/Videos/Screencasts/adjouring2-2024-04-19_10.01.12.mp4'
image_path = 'testing.gif'
duration = 10

# audio = convert_to_speech(text, 'Joanna')

# i = Image.open(image)
image_files=['./source/.media/lips_e.png', './source/.media/lips_r.png', './source/.media/lips_c.png', './source/.media/lips_w.png', './source/.media/lips_u.png', './source/.media/lips_a.png', './source/.media/lips_a.png', './source/.media/lips_u.png', './source/.media/lips_o.png', './source/.media/lips_u.png', './source/.media/lips_sil.png']
create_image(image_files, image_path)
create_video(image_path)
