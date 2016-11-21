#!/usr/bin/env python

import dateutil.parser
import html
import markdown
import mutagen.easyid3
import mutagen
import mutagen.id3
import mutagen.mp3
import os
import pathlib
import plumbum
import shutil
import taglib
import re
import unidecode
import yaml

BASE_DIR = (pathlib.Path(__file__) / '..').resolve()
AUDIO_DATA_PATH = BASE_DIR / 'audio.yaml'
ORIGINAL_DIR = BASE_DIR / 'wr' / 'Audio' / 'FLAC Originals'
FLAC_DIR = BASE_DIR / 'flac'
MP3_DIR = BASE_DIR / 'dist' / 'Audio' / 'MP3'
M4A_DIR = BASE_DIR / 'dist' / 'Audio' / 'M4A'

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

def set_flac_tags(path, tags):
    cmd = plumbum.local['metaflac']['--remove-all-tags', str(path)]
    # print(cmd)
    cmd()
    cmd = plumbum.local['metaflac']
    for field, value in tags.items():
        cmd = cmd['--set-tag=%s=%s' % (field.upper(), value)]
    cmd = cmd[str(path)]
    # print(cmd)
    cmd()

standard_mp3_tag_maps = {
    'title': 'TIT2',
    'artist': 'TOPE',
    'album': 'TALB',
    'organization': 'TPUB',
    'performer': 'TPE1',
    'tracknumber': 'TRCK',
    'genre': 'TCON',
    'copyright': 'TCOP',
}

def set_mp3_tags(path, tags):
    meta = mutagen.id3.ID3()
    for field, value in tags.items():
        frame_name = standard_mp3_tag_maps.get(field)
        if frame_name:
            frame = getattr(mutagen.id3, frame_name)(encoding=3, text=value)
        elif field == 'license':
            frame = mutagen.id3.WCOP(url=value)
        elif field == 'description':
            frame = mutagen.id3.COMM(encoding=3, language='eng', text=value)
        elif field == 'date':
            frame = mutagen.id3.TDRC(encoding=3, text=value[0:4])
        else:
            print('Warning: unknown mp3 field map %s' % field)
        meta.add(frame)
    meta.save(str(path), v1=mutagen.id3.ID3v1SaveOptions.REMOVE)

def add_description(meta):
    if 'description' in meta:
        return
    description = ('Read by %(reader)s on ' % meta) + \
        meta['date'].strftime('%B %-d, %Y') + \
        ' at Abhayagiri Buddhist Monastery.'
    list_for_description = lambda items: '; '.join(map(curly, items))
    if 'readings' in meta:
        description += ' Readings: ' + \
            list_for_description(meta['readings'])
    if 'questions' in meta:
        description += ' Questions: ' + \
            list_for_description(meta['questions'])
    meta['description'] = description

def get_original_path(meta):
    glob = meta.get('original_glob') or \
        (meta['date'].strftime('%Y-%m-%d') + '*.flac')
    tests = list(ORIGINAL_DIR.glob(glob))
    if len(tests) == 1:
        return tests[0]
    else:
        print(glob)
        raise Exception('Could not find original for %s' % meta['title'])

total = len(list(ORIGINAL_DIR.glob('*.flac')))
n = 1

data = yaml.load(AUDIO_DATA_PATH.open('r', encoding='utf-8'))
for audio in data['audio']:
    meta = data['default'].copy()
    meta.update(audio)
    meta['date'] = dateutil.parser.parse(meta['date'])
    meta['artist'] = meta.get('author') or meta['speaker']
    meta['performer'] = meta.get('reader') or meta['speaker']
    add_description(meta)

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
    flac_path = FLAC_DIR / (base_filename + '.flac')
    mp3_path = MP3_DIR / (base_filename + '.mp3')
    m4a_path = M4A_DIR / (base_filename + '.m4a')

    tags = { key: meta[key] for key in [
        'title',
        'artist',
        'performer',
        'album',
        'genre',
        'description',
        'organization',
        'copyright',
        'license',
    ] }
    tags['tracknumber'] = '%02d/%d' % (n, total)
    tags['date'] = meta['date'].strftime('%Y-%m-%d')

    if not flac_path.exists():
        original_path = get_original_path(meta)
        print('Copying original to %s' % flac_path.name)
        shutil.copy(str(original_path), str(flac_path))

    print('Updating tags on %s' % flac_path.name)
    set_flac_tags(flac_path, tags)

    if not mp3_path.exists():
        print("Encoding %s" % mp3_path.name)
        chain = \
            plumbum.local['flac']['-c', '-d', str(flac_path)] | \
            plumbum.local['lame']['--cbr', '-b', '64', '-m', 'm', '-', str(mp3_path)]
        chain(retcode=(0,-13))
    print('Updating tags on %s' % mp3_path.name)
    set_mp3_tags(mp3_path, tags)

    if not m4a_path.exists():
        print("Encoding %s" % m4a_path.name)
        plumbum.local['ffmpeg']('-i', str(flac_path),
            '-c:a', 'libfdk_aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            str(m4a_path)
        )
    # m4a tags get set by ffmpeg

    n += 1
