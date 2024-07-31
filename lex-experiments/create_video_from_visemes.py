import moviepy.editor as mp
import imageio as io
import ast

# Define a function to create a video from an image and speech
def create_video(image_path):
    audioclip = mp.AudioFileClip('m3test.mp3')
    clip = mp.VideoFileClip(image_path)
    
    new_audioclip = mp.CompositeAudioClip([audioclip])
    clip.audio = new_audioclip
    clip.write_videofile("m3output.webm")

def create_image(visems, image_path):
  previous_time = 0
  frames = []
  for viseme in visemes:
    duration = viseme['time'] - previous_time
    for i in range(duration):
      file = io.imread(lips[viseme['value']]['name'])
      frames.append(file)

  frames.append(io.imread(lips['sil']['name']))
    
  with io.get_writer(image_path, mode='I', duration=0.2) as writer:
    for frame in frames:
      writer.append_data(frame)

image_path = 'work.gif'
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

with open('visemes.txt', 'r') as f:
    lines = f.readlines()
    visemes = []
    for line in lines:
        visemes.append(ast.literal_eval(line.strip()))

create_image(visemes, image_path)
create_video(image_path)
