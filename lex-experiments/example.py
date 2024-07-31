import boto3
import json
import numpy as np
import imageio

def create_lip_sync(text, output_file):
    # 1. Obtain Audio and Viseme Data
    polly_client = boto3.client('polly')
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Joanna'  # Replace with desired voice
    )
    with open("audio.mp3", "wb") as f:
        f.write(response['AudioStream'].read())

    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='json',
        VoiceId='Joanna',
        SpeechMarkTypes=['viseme']
    )
    viseme_data = json.loads(response['AudioStream'].read().decode('utf-8'))

    # 2. Preprocess Viseme Data
    frame_rate = 30  # Adjust frame rate as needed
    viseme_frames = []
    for viseme in viseme_data['visemes']:
        start_frame = int(viseme['startTime'] * frame_rate)
        end_frame = int(viseme['endTime'] * frame_rate)
        viseme_frames.extend([viseme['viseme']] * (end_frame - start_frame))

    # 3. Load Lip Sync Images
    lip_sync_images = [imageio.imread(f"./source/.media/lips_{viseme}.png") for viseme in set(viseme_frames)]

    # 4. Create Animation
    frames = []
    for frame_index, viseme in enumerate(viseme_frames):
        image_index = lip_sync_images.index(viseme)
        frames.append(lip_sync_images[image_index])

    # 5. Encode to WebM
    with imageio.get_writer(output_file, mode='I', fps=frame_rate) as writer:
        for frame in frames:
            writer.append_data(frame)

if __name__ == "__main__":
    create_lip_sync("Hello, world!", "output.webm")
