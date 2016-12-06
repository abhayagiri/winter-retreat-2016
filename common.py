import dateutil.parser
import html
import markdown
import os
import pathlib
import plumbum
import re
import unidecode
import yaml

BASE_DIR = (pathlib.Path(__file__) / '..').resolve()
AUDIO_DATA_PATH = BASE_DIR / 'audio.yaml'
ORIGINAL_DIR = BASE_DIR / 'wr' / 'Audio' / 'FLAC Originals'
FLAC_DIR = BASE_DIR / 'flac'
MP3_DIR = BASE_DIR / 'dist' / 'DVD' / 'Audio' / 'MP3'
MP3_LQ_DIR = BASE_DIR / 'dist' / 'CD' / 'Audio'
M4A_DIR = BASE_DIR / 'dist' / 'DVD' / 'Audio' / 'M4A'
ALBUM_COVER_PATH = BASE_DIR / 'wr' / 'CD Cover/Winter Retreat 2016 Cover.jpg'


def curly(s):
    md = markdown.markdown(s, extensions=['markdown.extensions.smarty'])
    return html.unescape(re.sub(r'<.+?>', '', md))

def array_to_mdlist(lst):
    return '* ' + '\n* '.join(lst)

def filenamey(s):
    s = unidecode.unidecode(s)
    s = re.sub(r'[^-_.,\'\w\s]', ' ', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()

def short_name(s):
    s = unidecode.unidecode(s)
    s = re.sub(r'^ *(Ajahn|Tan|Samanera|Anagarika) *', '', s)
    return {
        'Pasanno': 'AP',
        'Karunadhammo': 'AKd',
        'Jotipalo': 'AJ',
        'Naniko': 'AN',
        'Debbie Stamp': 'Debbie',
        'Beth Steff': 'Beth',
    }.get(s, s)

def add_base_filename(meta):
    if 'base_filename' in meta:
        return
    base_filename = filenamey(
        meta['date'].strftime('%Y-%m-%d') + ' ' +
        short_name(meta['performer'])
    )
    if 'speaker' in meta:
        base_filename += ' ' + filenamey(meta['title'])
    else:
        base_filename += ' ' + filenamey('Reading %s by %s' % (
            meta['title'],
            meta['artist']
        ))
    meta['base_filename'] = base_filename

def get_original_path(meta):
    glob = meta.get('original_glob') or \
        (meta['date'].strftime('%Y-%m-%d') + '*.flac')
    tests = list(ORIGINAL_DIR.glob(glob))
    if len(tests) == 1:
        return tests[0]
    else:
        print(glob)
        raise Exception('Could not find original for %s' % meta['title'])

def get_audio_data():
    data = yaml.load(AUDIO_DATA_PATH.open('r', encoding='utf-8'))
    for i, audio in enumerate(data['audio']):
        meta = data['default'].copy()
        meta.update(audio)
        meta['date'] = dateutil.parser.parse(meta['date'])
        meta['artist'] = meta.get('author') or meta['speaker']
        meta['performer'] = meta.get('reader') or meta['speaker']
        add_base_filename(meta)
        data['audio'][i] = meta
    return data
