from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrock
from langchain_aws import AmazonKnowledgeBasesRetriever

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import logging
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import base64
import time
import json

import speech_recognition as sr
from pydub import AudioSegment

### High level configuration
os.environ["AWS_PROFILE"] = "hackathon"
audioOutputFile = "./temp/output.mp3"
audioInputFile = "./temp/input.wav"
phrases_to_remove = [
  "Based on the context provided,",
  "Based on the provided context,"
]
### Logging setup
debugoutput = True
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
log = logging.getLogger('buddy')

### Bedrock Setup
modelID = "anthropic.claude-v2"

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

model_kwargs =  { 
    "max_tokens": 2048,
    "temperature": 0.9,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

llm = ChatBedrock(client=bedrock, model_id=modelID, model_kwargs=model_kwargs)
bedrock_config = {
  'kb_id': 'ISZGKBFX00',
  'numberOfResults': '6',
  'personality': 'A friendly and excited camp counselor trying to help uses of Campdoc',
}

### Polly Setup
polly = boto3.client('polly')
polly_config = {
  'engine': 'neural',
  'voiceid': 'Matthew'
}
polly_lang_codes = {
  'Arabic': 'arb',
  'Arabic (Gulf)': 'ar-AE',
  'Catalan': 'ca-ES',
  'Chinese (Cantonese)': 'yue-CN',
  'Chinese (Mandarin)': 'cmn-CN',
  'Danish': 'da-DK',
  'Dutch (Belgian)': 'nl-BE',
  'Dutch': 'nl-NL',
  'English (Australian)': 'en-AU',
  'English (British)': 'en-GB',
  'English (Indian)': 'en-IN',
  'English (New Zealand)': 'en-NZ',
  'English (South African)': 'en-ZA',
  'English (US)': 'en-US',
  'English (Welsh)': 'en-GB-WLS',
  'Finnish': 'fi-FI',
  'French': 'fr-FR',
  'French (Belgian)': 'fr-BE',
  'French (Canadian)': 'fr-CA',
  'Hindi': 'hi-IN',
  'German': 'de-DE',
  'German (Austrian)': 'de-AT',
  'Icelandic': 'is-IS',
  'Italian': 'it-IT',
  'Japanese': 'ja-JP',
  'Korean': 'ko-KR',
  'Norwegian': 'nb-NO',
  'Polish': 'pl-PL',
  'Portuguese (Brazilian)': 'pt-BR',
  'Portuguese (European)': 'pt-PT',
  'Romanian': 'ro-RO',
  'Russian': 'ru-RU',
  'Spanish (European)': 'es-ES',
  'Spanish (Mexican)': 'es-MX',
  'Spanish (US)': 'es-US',
  'Swedish': 'sv-SE',
  'Turkish': 'tr-TR',
  'Welsh': 'cy-GB'
}

### Animation Setup
toon_media = {
    "p": {"name": "./media/toon_m.png"},
    "t": {"name": "./media/toon_c.png"},
    "S": {"name": "./media/toon_ch.png"},
    "T": {"name": "./media/toon_th.png"},
    "f": {"name": "./media/toon_f.png"},
    "k": {"name": "./media/toon_c.png"},
    "i": {"name": "./media/toon_e.png"},
    "r": {"name": "./media/toon_r.png"},
    "s": {"name": "./media/toon_c.png"},
    "u": {"name": "./media/toon_w.png"},
    "@": {"name": "./media/toon_u.png"},
    "a": {"name": "./media/toon_a.png"},
    "e": {"name": "./media/toon_a.png"},
    "E": {"name": "./media/toon_u.png"},
    "o": {"name": "./media/toon_o.png"},
    "O": {"name": "./media/toon_u.png"},
    "sil": {"name": "./media/toon_sil.png"},
    "default": {"name": "./media/toon_default.png"},
}

def chatbot(personality, language, freeform_text):
  c="{context}"
  q="{question}"
  template  = f'''You are {personality}. You speak in {language}.
  Answer the question based only on the following context:
  {c}

  Question: {q}'''
  
  prompt = ChatPromptTemplate.from_template(template)

  # Amazon Bedrock - KnowledgeBase Retriever 
  retriever = AmazonKnowledgeBasesRetriever(
      knowledge_base_id=bedrock_config['kb_id'],
      retrieval_config={"vectorSearchConfiguration": {"numberOfResults": bedrock_config['numberOfResults']}},
  )
  
  chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    .assign(response = prompt | llm | StrOutputParser())
    .pick(["response", "context"])
  )

  result = chain.invoke(freeform_text)
  response = result['response']
  
  # If any phrases to remove are in the response, remove them
  for phrase in phrases_to_remove:
    response = response.replace(phrase, "")
  response = response.strip().capitalize()
  
  context = result['context']
  return response, context

def create_mp3(text, filename, language):
    log.info(f"Creating mp3 for: {text}")
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Engine=polly_config['engine'], LanguageCode=polly_lang_codes[language], VoiceId=polly_config['voiceid'], OutputFormat='mp3', Text=text)
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        log.info(error)
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
          output = f"./{filename}"
          try:
            with open(output, "wb") as file:
              file.write(stream.read())
          except IOError as error:
            log.info(error)
            print(error)
            sys.exit(-1)
    else:
      log.info("Could not stream audio")
      sys.exit(-1)
    
    if os.path.exists(output):
      log.info(f"Audio file created: {output}")
      

def create_text_card(text, title="Response"):
  st.markdown(f"### {title}")
  st.write(f"> {text}")

def get_visemes(text, language):
    log.info(f"Getting visemes from polly")
    try:
        response = polly.synthesize_speech(Engine=polly_config['engine'], LanguageCode=polly_lang_codes[language], VoiceId=polly_config['voiceid'], OutputFormat='json', Text=text, SpeechMarkTypes=['viseme'])
    except (BotoCoreError, ClientError) as error:
        log.info(error)
        print(error)
        sys.exit(-1)
    visemes = [
                json.loads(v)
                for v in response["AudioStream"].read().decode().split()
                if v
            ]
    log.info(f"Visemes: {visemes}")
    return visemes

def speak(text, language):
  log.info(f"Speaking in {language}")

  create_mp3(text, audioOutputFile, language)

  with open(audioOutputFile, 'rb') as audio_file:
    audio_bytes = audio_file.read()
  base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
  audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
  log.info("create audio card")

  st.markdown(audio_html, unsafe_allow_html=True)

def animate(viseme, images):
    log.info('animating')
    prev_time = 0
    for viseme in visemes:
        t = (viseme['time'] - prev_time)/ 1000
        prev_time = viseme['time']
        time.sleep(t)
        face.image(images[viseme['value']]['name'], use_column_width=True)
        # print(f"Viseme: {viseme['value']}, Duration: {t}")
        
    face.image(images['default']['name'], use_column_width=True)

def get_transcription(audio):
  log.info("Getting transcription")
  try:
    # use the audio file as the audio source                                        
    r = sr.Recognizer()
    with sr.AudioFile(audio) as source:
        audio = r.record(source)  # read the entire audio file                  
        transcription = r.recognize_google(audio)

  except (BotoCoreError, ClientError) as error:
      log.info(error)
      print(error)
      sys.exit(-1)
  
  return transcription  

if __name__ == "__main__":
  st.title("Buddy Chatbot")
  mute = st.sidebar.checkbox("Mute", value=True)
  transcribe = st.sidebar.checkbox("Transcribe", value=False)
  if mute:
    bringAlive = st.sidebar.checkbox("Bring Buddy Alive", value=False)
  else:
    bringAlive = st.sidebar.checkbox("Bring Buddy Alive", value=True)
  language = st.sidebar.selectbox("Language", polly_lang_codes.keys(), index=13)
  face = st.sidebar.empty()
  face.image(toon_media['default']['name'], use_column_width=True)

  if transcribe:
    st.write("Click on the microphone to start recording")
    audio_bytes = audio_recorder()
    if audio_bytes:
        with open(audioInputFile, 'wb') as af:
          af.write(audio_bytes)
        transcript = get_transcription(audioInputFile)
        st.write(transcript)
        st.audio(audio_bytes, format="audio/wav")
        response, context = chatbot(bedrock_config['personality'],language,transcript)
        create_text_card(response, title="Buddy's response")
        if not mute:
          st.write("Let me say that for you...")
          visemes = get_visemes(response, language)
          speak(response, language)
          if bringAlive:
              face.image(toon_media['default']['name'], use_column_width=True)
              animate(visemes, toon_media)

  else:
    if language:
      freeform_text = st.sidebar.text_area(label="what is your question?",
      max_chars=100)


    if freeform_text:
      create_text_card(freeform_text, title="You asked")
      response, context = chatbot(bedrock_config['personality'],language,freeform_text)
      create_text_card(response, title="Buddy's response")

      if not mute:
          st.write("Let me say that for you...")
          visemes = get_visemes(response, language)
          speak(response, language)
          if bringAlive:
              face.image(toon_media['default']['name'], use_column_width=True)
              animate(visemes, toon_media)
