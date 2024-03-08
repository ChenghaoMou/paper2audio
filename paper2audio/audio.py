from pydub import AudioSegment
from pydub.playback import play as play_audio

def play(file):
    sound = AudioSegment.from_file(file, codec="pcm_alaw")
    play_audio(sound)

def check_mp3_file_integrity(file):
    try:
        AudioSegment.from_file(file, codec="mp3")
        return True
    except Exception:
        return False