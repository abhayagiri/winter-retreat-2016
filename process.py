#!/usr/bin/env python

import dateutil.parser
import mutagen
import mutagen.id3
import mutagen.mp4
import mutagen.easymp4
import pathlib
import plumbum
import shutil
import yaml

from common import *

PRINT_CMD = False
NOOP = False

def add_description(meta):
    if 'description' in meta:
        return
    description = ('Read by %(reader)s on ' % meta) + \
        meta['date'].strftime('%B %-d, %Y') + \
        ' at Abhayagiri Buddhist Monastery.'
    list_for_description = lambda items: '; '.join(map(curly, items))
    if 'readings' in meta:
        description += ' Readings: ' + \
            list_for_description(meta['readings']) + '.'
    if 'questions' in meta:
        description += ' Questions: ' + \
            list_for_description(meta['questions']) + '.'
    meta['description'] = description

def add_cover_data(meta, cache={}):
    if not cache:
        cache['cover_data'] = ALBUM_COVER_PATH.open('rb').read()
    meta['cover_data'] = cache['cover_data']

def set_flac_tags(path, tags):
    # metaflac is much faster than mutagen
    cmd = plumbum.local['metaflac']
    cmd = cmd['--remove-all']
    cmd = cmd[str(path)]
    PRINT_CMD and print(cmd)
    NOOP or cmd()

    cmd = plumbum.local['metaflac']
    for field, value in tags.items():
        if field == 'cover_data':
            continue
        cmd = cmd['--set-tag=%s=%s' % (field.upper(), value)]
    cmd = cmd['--import-picture-from=' + str(ALBUM_COVER_PATH)]
    cmd = cmd[str(path)]
    PRINT_CMD and print(cmd)
    NOOP or cmd()

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
        elif field == 'cover_data':
            frame = mutagen.id3.APIC(
                encoding=3,
                mime='image/jpeg',
                type=3, # 3 is for the cover image
                desc='Cover',
                data=value
            )
        else:
            print('Warning: unknown mp3 field map %s' % field)
        meta.add(frame)
    NOOP or meta.save(str(path), v1=mutagen.id3.ID3v1SaveOptions.REMOVE)

m4a_tag_mapping = {
    'description': 'comment',
}

mutagen.easymp4.EasyMP4Tags.RegisterTextKey('cover', 'covr')

def set_m4a_tags(path, tags):
    meta = mutagen.easymp4.EasyMP4(str(path))
    meta.delete()
    for field, value in tags.items():
        field = m4a_tag_mapping.get(field, field)
        if field in ('license', 'organization', 'performer', 'cover_data'):
            pass # no equivalent field
        else:
            meta.tags[field] = value
    meta.tags['cover'] = [
        mutagen.mp4.MP4Cover(
            tags['cover_data'],
            imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG
        )
    ]
    NOOP or meta.save()

data = get_audio_data()
total = len(data['audio'])
n = 1
md = ''

for meta in data['audio']:

    add_description(meta)
    add_cover_data(meta)

    flac_path = FLAC_DIR / (meta['base_filename'] + '.flac')
    mp3_path = MP3_DIR / (meta['base_filename'] + '.mp3')
    m4a_path = M4A_DIR / (meta['base_filename'] + '.m4a')

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
        'cover_data',
    ] }
    tags['tracknumber'] = '%02d/%d' % (n, total)
    tags['date'] = meta['date'].strftime('%Y-%m-%d')

    if not flac_path.exists():
        original_path = get_original_path(meta)
        print('Copying original to %s' % flac_path.name)
        NOOP or shutil.copy(str(original_path), str(flac_path))

    print('Updating tags on %s' % flac_path.name)
    set_flac_tags(flac_path, tags)

    if not mp3_path.exists():
        print("Encoding %s" % mp3_path.name)
        chain = \
            plumbum.local['flac']['-c', '-d', str(flac_path)] | \
            plumbum.local['lame']['--cbr', '-b', '64', '-m', 'm', '-', str(mp3_path)]
        PRINT_CMD and print(chain)
        NOOP or chain(retcode=(0,-13))

    print('Updating tags on %s' % mp3_path.name)
    set_mp3_tags(mp3_path, tags)

    if not m4a_path.exists():
        print("Encoding %s" % m4a_path.name)
        cmd = plumbum.local['ffmpeg']['-i', str(flac_path),
            '-map_metadata', '-1',
            '-c:a', 'libfdk_aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            str(m4a_path)
        ]
        PRINT_CMD and print(cmd)
        NOOP or cmd()

    print('Updating tags on %s' % m4a_path.name)
    set_m4a_tags(m4a_path, tags)

    n += 1
