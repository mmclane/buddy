from langchain.chains import LLMChain
# from langchain_aws import BedrockLLM
from langchain_community.llms import Bedrock
# from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
import boto3
# from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import streamlit as st
# from audio_recorder_streamlit import audio_recorder # This is used to record audio from the user
import base64
# import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image

os.environ["AWS_PROFILE"] = "hackathon"
polly = boto3.client('polly')
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
modelID = "anthropic.claude-v2"

llm = Bedrock(
    model_id=modelID,
    client=bedrock_client,
    model_kwargs={"max_tokens_to_sample": 2000,"temperature":0.9}
)

lips = {
    "p": {"name": "./source/.media/lips_m.png"},
    "t": {"name": "./source/.media/lips_c.png"},
    "S": {"name": "./source/.media/lips_ch.png"},
    "T": {"name": "./source/.media/lips_th.png"},
    "f": {"name": "./source/.media/lips_f.png"},
    "k": {"name": "./source/.media/lips_c.png"},
    "i": {"name": "./source/.media/lips_e.png"},
    "r": {"name": "./source/.media/lips_r.png"},
    "s": {"name": "./source/.media/lips_c.png"},
    "u": {"name": "./source/.media/lips_w.png"},
    "@": {"name": "./source/.media/lips_u.png"},
    "a": {"name": "./source/.media/lips_a.png"},
    "e": {"name": "./source/.media/lips_a.png"},
    "E": {"name": "./source/.media/lips_u.png"},
    "o": {"name": "./source/.media/lips_o.png"},
    "O": {"name": "./source/.media/lips_u.png"},
    "sil": {"name": "./source/.media/lips_sil.png"},
}

def my_chatbot(personality, language,freeform_text):
    prompt = PromptTemplate(
        input_variables=["personaility", "language", "freeform_text"],
        template="You are {personality}. You are in {language} responding in short answers.\n\n{freeform_text}"
    )

    bedrock_chain = LLMChain(llm=llm, prompt=prompt)

    response=bedrock_chain({'personality':personality, 'language':language, 'freeform_text':freeform_text})
    return response

def create_mp3(text, filename):
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Engine='neural', LanguageCode='en-US', VoiceId='Matthew', OutputFormat='mp3', Text=text)
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
      # Note: Closing the stream is important because the service throttles on the
      # number of parallel connections. Here we are using contextlib.closing to
      # ensure the close method of the stream object will be called automatically
      # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
          output = f"./{filename}"
          try:
            # Open a file for writing the output as a binary stream
            with open(output, "wb") as file:
              file.write(stream.read())
          except IOError as error:
            # Could not write to file, exit gracefully
            print(error)
            sys.exit(-1)
    else:
      # The response didn't contain audio data, exit gracefully
      print("Could not stream audio")
      sys.exit(-1)   

# Define a function to create a video from an image and speech
def create_video(image_path, audio, duration):
    clip = VideoFileClip(image_path).set_duration(duration)
    audio_clip = clip.audio.set_audio(audio)
    final_clip = clip.set_audio(audio_clip)
    return final_clip

def create_text_card(text, title="Response"):
  st.markdown(f"### {title}")
  st.write(f"> {text}")

def speak(text):
  create_mp3(text, 'text.mp3')
  with open('text.mp3', 'rb') as audio_file:
    audio_bytes = audio_file.read()
  base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
  audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
  st.markdown(audio_html, unsafe_allow_html=True)

if __name__ == "__main__":
  st.title("M3test Chatbot")
  mute = st.sidebar.checkbox("Mute", value=True) 
  language = st.sidebar.selectbox("Language", ["english", "spanish", "french"])
  personality = st.sidebar.selectbox("Personality", ["Bugs Bunny", "Deadpool", "Marvin the depressed robot"])
  face = st.sidebar.empty()
  face.image(lips['sil']['name'], use_column_width=True)

  if language:
    freeform_text = st.sidebar.text_area(label="what is your question?",
    max_chars=100)

  if freeform_text:
    response = my_chatbot(personality,language,freeform_text)
    if not mute:
      speak(response['text'])
    create_text_card(response['text'], title="{}'s response".format(personality))
    video = create_video('./source/.media/lips_a.png', 'text.mp3', 5)
    face.image(video, use_column_width=True)
