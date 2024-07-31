import json
# import logging
import os
from tempfile import TemporaryDirectory
# import time
import streamlit as st
import boto3
# from botocore.exceptions import ClientError
from play_sounds import play_file
# import requests
from polly_wrapper import PollyWrapper

polly_client = boto3.client("polly")
# logger = logging.getLogger(__name__)

# Initialize Streamlit app
st.title("Amazon Polly Lip-Sync Application")

# Get user input for text to synthesize
text_to_synthesize = st.text_area("Enter text to synthesize", "Hello, how are you?")

# Get user input for voice
voice_id = st.selectbox("Select voice", ["Joanna", "Matthew", "Ivy", "Justin"])

# Button to start synthesis
if st.button("Synthesize Speech"):
    try:
        polly_client = boto3.Session().client('polly')
        response = polly_client.synthesize_speech(
            Text=text_to_synthesize,
            OutputFormat='mp3',
            VoiceId=voice_id,
            SpeechMarkTypes=['viseme']
        )

        # Save the audio stream returned by Amazon Polly on the local disk
        if "AudioStream" in response:
            with TemporaryDirectory() as tmpdir:
                output = os.path.join(tmpdir, "speech.mp3")
                with open(output, 'wb') as file:
                    file.write(response['AudioStream'].read())
                st.audio(output, format='audio/mp3')
                play_file(output)

        # Process visemes
        visemes = json.loads(response['Visemes'])
        st.write("Visemes:", visemes)

    except ClientError as e:
        # logger.error(e)
        st.error("An error occurred while synthesizing speech.")

# Additional Streamlit components and logic can be added here
