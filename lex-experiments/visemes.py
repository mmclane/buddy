import boto3
import os
import sys
import json
from contextlib import closing
from botocore.exceptions import BotoCoreError, ClientError

os.environ["AWS_PROFILE"] = "hackathon"
polly = boto3.client('polly')

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

def get_visemes(text):
    try:
        response = polly.synthesize_speech(Engine='neural', LanguageCode='en-US', VoiceId='Matthew', OutputFormat='json', Text=text, SpeechMarkTypes=['viseme'])
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)
    # visemes = response
    visemes = [
                json.loads(v)
                for v in response["AudioStream"].read().decode().split()
                if v
            ]
    return visemes


text = "You are the bot king, Matt"
# create_mp3(text, "m3test.mp3")
visemes = get_visemes(text)

print(visemes)
