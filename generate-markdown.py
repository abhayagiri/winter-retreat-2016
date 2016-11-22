#!/usr/bin/env python

import markdown

from common import *

data = get_audio_data()
total = len(data['audio'])
n = 1
md = ''

for meta in data['audio']:

    md += '## %s\n\n' % meta['title']
    md += '%s  \n' % meta['date'].strftime('%B %-d, %Y')
    if 'speaker' in meta:
        md += 'By **%s**\n\n' % meta['speaker']
    else:
        md += 'By **%s**, read by %s\n\n' % (meta['author'], meta['reader'])

    list_for_markdown = lambda items: '* '.join(map(curly, items))
    if 'readings' in meta:
        md += 'Readings:\n\n* ' + \
            list_for_markdown(meta['readings']) + '\n\n'
    if 'questions' in meta:
        md += 'Questions:\n\n* ' + \
            list_for_markdown(meta['questions']) + '\n\n'

(BASE_DIR / 'index.html').open('w', encoding='utf-8').write(markdown.markdown(md))
