from google.cloud import texttospeech_v1beta1 as tts


def generate(part, voice_name="en-US-Wavenet-D"):
    client = tts.TextToSpeechClient()
    inp = tts.SynthesisInput(
        text=part["text"]
        .replace("\n", " ")
        .encode("ascii", "ignore")
        .decode("ascii", "ignore")
    )
    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.ALAW,
    )
    voice = tts.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
    )

    request = tts.SynthesizeSpeechRequest(
        input=inp,
        audio_config=audio_config,
        voice=voice,
    )
    return client.synthesize_speech(request=request)


if __name__ == "__main__":
    
    r = generate({"text": "Hello World"}, voice_name="en-US-Wavenet-D")
    with open("output.mp3", "wb") as out:
        out.write(r.audio_content)