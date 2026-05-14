import os
from gtts import gTTS
from argparse import ArgumentParser
from pydub import AudioSegment

def main(arg):
    with open(arg.text, "r") as f:
        data = f.readlines()

    text = ""
    for s in data:
        text = text + s + ". "

    ok = True
    if arg.lang == "vi":
        tts = gTTS(text, lang='vi', tld='co.vi')
    elif arg.lang == "en":
        tts = gTTS(text, lang='en')
    elif arg.lang == "cn":
        tts = gTTS(text, lang='cn')
    elif arg.lang == "fr":
        tts = gTTS(text, lang='fr')
    else:
        ok = False

    if ok:
        tts.save("temp.mp3")
        sound = AudioSegment.from_mp3("temp.mp3")
        sound.export(arg.audio_export, format="wav")
        os.remove("temp.mp3")
        print("Export speech from text completed!")
        print('Please check the wav file at', args.audio_export)

    else:
        print("Please choose one language from list ['en', 'vi', 'cn', 'fr']")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--text", default='./source_text/Intro_Quang.txt', help="path to text file")
    parser.add_argument("--lang", default='vi', choices=['en', 'vi', 'cn', 'fr'],
                        help="Choose a language")
    parser.add_argument("--audio_export", default='./source_audio/Intro.wav', help="path to save wav file")

    args = parser.parse_args()
    main(args)