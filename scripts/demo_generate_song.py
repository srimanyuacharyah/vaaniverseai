"""Demo script: generate a song and optionally save/sing it."""
import sys
sys.path.insert(0, 'src')
from vaaniverse import song_generator, tts

def main():
    song = song_generator.generate_song(theme='love', lang='hi')
    print('Lyrics:\n')
    print(song['lyrics'])
    print('\nMelody (notes):', song['melody'])
    song_generator.save_song(song, prefix='demo_song')
    print('\nSaved demo_song.txt and demo_song.melody.txt')
    # Speak the lyrics as a placeholder for singing
    tts.speak(song['lyrics'], lang='hi')

if __name__ == '__main__':
    main()
