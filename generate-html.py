#!/usr/bin/env python

import html
import jinja2
import markdown
import re
import time
import urllib

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


def audio_link(url, text, title, escape=True):
    matches = re.search(r'([0-9]+):([0-9]+)', text)
    if matches:
        time = int(matches.group(1)) * 60 + int(matches.group(2))
    else:
        time = 0
    if not title:
        title = text
    if escape:
        text = html.escape(text)
    return '<a href="%s" title="%s" data-time="%d">%s</a>' % (
        urllib.parse.quote(url),
        html.escape(title),
        time,
        text
    )


def get_main_html(data):
    n = 1
    i = 0
    result = ''
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
            result += '<div class="parallax-window" data-bleed="10" data-parallax="scroll" ' + \
                ('data-image-src="%s"></div>' % url)
        result += '<div class="container entry %s">\n' % oddeven
        audio_url = 'DVD/Audio/MP3/' + meta['base_filename'] + '.mp3'
        md = '<h2>' + audio_link(audio_url,
            html.escape(meta['title']) +
            ' <span class="glyphicon glyphicon-headphones"></span>',
            meta['title'], escape=False) + '</h2>\n'
        if 'speaker' in meta:
            md += '**%s**' % meta['speaker']
        else:
            md += '**%s** -- Read by %s' % (meta['author'], meta['reader'])
        md += ' -- %s\n\n' % meta['date'].strftime('%B %-d, %Y')
        if 'description' in meta:
            md += meta['description'] + '\n\n'
        if 'readings' in meta:
            md += 'Readings:\n\n* ' + \
                '\n* '.join(map(reading_to_markdown, meta['readings'])) + \
                '\n\n'
        if 'questions' in meta:
            question_to_markdown = lambda text: \
                audio_link(audio_url, text, meta['title'])
            md += 'Questions:\n\n* ' + \
                '\n* '.join(map(question_to_markdown, meta['questions'])) + \
                '\n\n'
        result += markdown.markdown(md, extensions=['markdown.extensions.smarty'])
        result += '</div>\n'
        n += 1
    return result


def main():
    template = HTML_TEMPLATE_PATH.open('r', encoding='utf-8').read()
    HTML_DIST_PATH.open('w', encoding='utf-8').write(
        jinja2.Template(template).render(
            main=get_main_html(get_audio_data()),
            version_stamp=time.time()
        )
    )


if __name__ == '__main__':
    main()
