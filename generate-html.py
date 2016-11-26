#!/usr/bin/env python

import jinja2
import markdown
import time

from common import *


HTML_TEMPLATE_PATH = BASE_DIR / 'index.html.tmpl'
HTML_DIST_PATH = BASE_DIR / 'dist' / 'index.html'
IMAGE_SPREAD = 6

def reading_to_markdown(item):
    if type(item) is dict:
        text = item['text']
        url = item['url']
    else:
        text = str(item)
        url = None
    if url:
        return '[%s](%s)' % (text, url)
    else:
        return text


def question_audio_to_markdown(text, audio_url):
    return '[%s](%s)' % (text, audio_url)


def get_main_html(data):
    n = 1
    i = 0
    html = ''
    for meta in data['audio']:
        oddeven = "odd" if n % 2 else "even"
        if n % IMAGE_SPREAD == 0:
            try:
                url = data['images'][i]
                i += 1
            except IndexError:
                url = data['images'][0]
            if not url.startswith('http'):
                url = 'img/' + url
            html += '<div class="parallax-window" data-parallax="scroll" ' + \
                ('data-image-src="%s"></div>' % url)
        html += '<div class="container entry %s">\n' % oddeven
        audio_url = 'DVD/Audio/MP3/' + meta['base_filename'] + '.mp3'
        md = '## [%s](%s)\n\n' % (meta['title'], audio_url)
        if 'speaker' in meta:
            md += '**%s**' % meta['speaker']
        else:
            md += '**%s** -- Read by %s' % (meta['author'], meta['reader'])
        md += ' -- %s\n\n' % meta['date'].strftime('%B %-d, %Y')
        if 'readings' in meta:
            md += 'Readings:\n\n* ' + \
                '\n* '.join(map(reading_to_markdown, meta['readings'])) + \
                '\n\n'
        if 'questions' in meta:
            question_to_markdown = lambda text: \
                question_audio_to_markdown(text, audio_url)
            md += 'Questions:\n\n* ' + \
                '\n* '.join(map(question_to_markdown, meta['questions'])) + \
                '\n\n'
        html += markdown.markdown(md, extensions=['markdown.extensions.smarty'])
        html += '</div>\n'
        n += 1
    return html


def main():
    template = HTML_TEMPLATE_PATH.open('r', encoding='utf-8').read()
    html = jinja2.Template(template).render(
        main=get_main_html(get_audio_data()),
        version_stamp=time.time()
    )
    HTML_DIST_PATH.open('w', encoding='utf-8').write(html)


if __name__ == '__main__':
    main()
