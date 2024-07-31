# from langchain_aws import BedrockLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrock
from langchain_aws import AmazonKnowledgeBasesRetriever


import boto3
# from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import streamlit as st
# from audio_recorder_streamlit import audio_recorder # This is used to record audio from the user
import base64
import time
import json

### High level configuration
os.environ["AWS_PROFILE"] = "hackathon"
audioOutputFile = "output.mp3"

### Bedrock Setup
modelID = "anthropic.claude-v2"
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)
model_kwargs =  { 
    "max_tokens": 2048,
    "temperature": 0.9,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}
# llm = BedrockLLM(model_id=modelID, model_kwargs={"max_tokens_to_sample": 2000,"temperature":0.9})
llm = ChatBedrock(client=bedrock_runtime, model_id=modelID, model_kwargs=model_kwargs)
bedrock_config = {
  'kb_id': 'ISZGKBFX00',
  'numberOfResults': '4'
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
lips = {
    "p": {"name": "./source/media/lips_m.png"},
    "t": {"name": "./source/media/lips_c.png"},
    "S": {"name": "./source/media/lips_ch.png"},
    "T": {"name": "./source/media/lips_th.png"},
    "f": {"name": "./source/media/lips_f.png"},
    "k": {"name": "./source/media/lips_c.png"},
    "i": {"name": "./source/media/lips_e.png"},
    "r": {"name": "./source/media/lips_r.png"},
    "s": {"name": "./source/media/lips_c.png"},
    "u": {"name": "./source/media/lips_w.png"},
    "@": {"name": "./source/media/lips_u.png"},
    "a": {"name": "./source/media/lips_a.png"},
    "e": {"name": "./source/media/lips_a.png"},
    "E": {"name": "./source/media/lips_u.png"},
    "o": {"name": "./source/media/lips_o.png"},
    "O": {"name": "./source/media/lips_u.png"},
    "sil": {"name": "./source/media/lips_sil.png"},
}

toon_media = {
    "p": {"name": "./source/media/toon_m.png"},
    "t": {"name": "./source/media/toon_c.png"},
    "S": {"name": "./source/media/toon_ch.png"},
    "T": {"name": "./source/media/toon_th.png"},
    "f": {"name": "./source/media/toon_f.png"},
    "k": {"name": "./source/media/toon_c.png"},
    "i": {"name": "./source/media/toon_e.png"},
    "r": {"name": "./source/media/toon_r.png"},
    "s": {"name": "./source/media/toon_c.png"},
    "u": {"name": "./source/media/toon_w.png"},
    "@": {"name": "./source/media/toon_u.png"},
    "a": {"name": "./source/media/toon_a.png"},
    "e": {"name": "./source/media/toon_a.png"},
    "E": {"name": "./source/media/toon_u.png"},
    "o": {"name": "./source/media/toon_o.png"},
    "O": {"name": "./source/media/toon_u.png"},
    "sil": {"name": "./source/media/toon_sil.png"},
}

def chatbot(personality, language, freeform_text):
  c="{context}"
  q="{question}"
  template  = f'''You are {personality}. You speak in {language}.
  Answer the question based only on the following context:
  {c}

  Question: {q}'''
  
  # template = '''Answer the question based only on the following context:
  # {context}

  # Question: {question}'''
  
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
  context = result['context']
  
  return response, context
  # input  = f"You are {personality}. You are in {language}.\n\n{freeform_text}"
  # return llm.invoke(input)
    
def create_mp3(text, filename, language):
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Engine=polly_config['engine'], LanguageCode=polly_lang_codes[language], VoiceId=polly_config['voiceid'], OutputFormat='mp3', Text=text)
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
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
            print(error)
            sys.exit(-1)
    else:
      print("Could not stream audio")
      sys.exit(-1)   

def create_text_card(text, title="Response"):
  st.markdown(f"### {title}")
  st.write(f"> {text}")

def get_visemes(text, language):
    try:
        response = polly.synthesize_speech(Engine=polly_config['engine'], LanguageCode=polly_lang_codes[language], VoiceId=polly_config['voiceid'], OutputFormat='json', Text=text, SpeechMarkTypes=['viseme'])
    except (BotoCoreError, ClientError) as error:
        print(error)
        sys.exit(-1)
    visemes = [
                json.loads(v)
                for v in response["AudioStream"].read().decode().split()
                if v
            ]
    return visemes

def speak(text, language):
  create_mp3(text, audioOutputFile, language)
  with open(audioOutputFile, 'rb') as audio_file:
    audio_bytes = audio_file.read()
  base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
  audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
  st.markdown(audio_html, unsafe_allow_html=True)

def animate(viseme, images):
    # print('animating')
    prev_time = 0
    for viseme in visemes:
        t = (viseme['time'] - prev_time)/ 1000
        prev_time = viseme['time']
        time.sleep(t)
        face.image(images[viseme['value']]['name'], use_column_width=True)
        # print(f"Viseme: {viseme['value']}, Duration: {t}")
        
    face.image(images['sil']['name'], use_column_width=True)

if __name__ == "__main__":
  st.title("Buddy Chatbot")
  mute = st.sidebar.checkbox("Mute", value=True) # TODO: Change back to True
  # showContext = st.sidebar.checkbox("Show Context", value=False)
  if mute:
    bringAlive = st.sidebar.checkbox("Bring Buddy Alive", value=False, disabled=True) # TODO: change value back to False
  else:
    bringAlive = st.sidebar.checkbox("Bring Buddy Alive", value=False) # TODO: change value back to False
  language = st.sidebar.selectbox("Language", polly_lang_codes.keys(), index=13)
  personality = st.sidebar.selectbox("Personality", ["Bugs Bunny", "Deadpool", "Marvin the depressed robot"])
  face = st.sidebar.empty()
  face.image('./source/media/toon.png', use_column_width=True)
#   face.image('./source/media/lips_sil.png', use_column_width=True)

  if language:
    freeform_text = st.sidebar.text_area(label="what is your question?",
    max_chars=100)

  if freeform_text:
    response, context = chatbot(personality,language,freeform_text)
    create_text_card(response, title="Buddy's response")
    # if showContext:
    #   create_text_card(context, title="Buddy's context")

    if not mute:
        visemes = get_visemes(response, language)
        speak(response, language)
        if bringAlive:
            face.image(lips['sil']['name'], use_column_width=True) # TODO: Change to toon
            animate(visemes, lips)
