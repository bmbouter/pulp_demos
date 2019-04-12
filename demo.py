import argparse
import csv
import time


"""
Make a Python 3 virtualenv and install requests and PyYAML
   python3 -m venv pulp_demos
   source pulp_demos/bin/activate

Run the script using the Python3 interpreter
   python demo.py

The data is expected to be in a filename <demo_num>.csv

It is expected to have a format like this:


https://www.youtube.com/watch?v=0T84sdEfBWE
State of Pulp,mhrivnak,0:15
Community Update,bmbouter,4:32
Debian Content Support for Pulp 2,misa,7:42,2.14
Napoleon style docstrings,asmacdo,11:48,3.0
Docs building check for pull requests on github,bizhang,13:59
Generate random SECRET_KEY for Django as part of setup workflow,bizhang,15:21,3.0
Asynchronous updates of importer,dkliban,16:14,3.0
File importer using the ChangeSet provided by the plugin API,jortel,19:40,3.0
Side by side Pulp2/Pulp3 dev installs,asmacdo,33:38


Note the optional fourth argument with the version of Pulp affected.
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Process community demo data.')
    parser.add_argument('--filename', help='Filename with the data', required=True)
    parser.add_argument('--date', help='The date the demo occured', default=time.strftime("%b %d, %Y"))
    parser.add_argument('--author', default='Brian Bouterse', help='The author of the announcements')
    return parser.parse_args()


class Demo(object):

    def __init__(self, title, nick, min, sec, version=None):
        self.title = title
        self.nick = nick
        self.min = min
        self.sec = sec
        self.version = version

    @property
    def time(self):
        return '{min}m{sec}s'.format(min=self.min, sec=self.sec)

    @property
    def version_str(self):
        if self.version is None:
            return ''
        else:
            return ' ({version})'.format(version=self.version)


def main():
    args = parse_args()
    youtube_slug, demos = parse_data(args)
    display_youtube_description(args, youtube_slug, demos)
    display_blog_post(args, youtube_slug, demos)
    display_pulp_list_email(args, youtube_slug, demos)


def parse_data(args):
    demos = []
    with open(args.filename) as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        youtube_link = None
        for row in spamreader:
            if youtube_link is None:
                youtube_link = row[0]
                continue
            min, sec = row[2].split(':')
            try:
                demo_kwargs = {'version': row[3]}
            except IndexError:
                demo_kwargs = {}
            demos.append(Demo(row[0], row[1], min, sec, **demo_kwargs))
    youtube_slug = youtube_link.split('?v=')[1]
    return (youtube_slug, demos)


def display_youtube_description(args, youtube_slug, demos):
    print("""

--------------------   youtube comments   ---------------------
""")
    for demo in demos:
        print('{min}:{sec} {title} ({nick}){version_str}\n'.format(min=demo.min, sec=demo.sec, title=demo.title, nick=demo.nick, version_str=demo.version_str))


def display_pulp_list_email(args, youtube_slug, demos):
    print("""

--------------------   email   ---------------------

The Pulp Community Demo video is available on the Pulp YouTube Channel [0] and on the Pulp blog [1].


Sections from the demo:
""")
    for demo in demos:
        print('* {title} ({nick}){version_str} - http://www.youtube.com/watch?v={youtube_slug}&t={time}\n'.format(
            title=demo.title, nick=demo.nick, youtube_slug=youtube_slug, time=demo.time, version_str=demo.version_str
        ))

    print("""
You can find the presenter IRC nicknames in the links above along with the version numbers they are being released in. You can ask questions via the mailing list or come chat on IRC.

[0]: https://www.youtube.com/PulpProject
[1]: """)


def display_blog_post(args, youtube_slug, demos):
    print("""

--------------------   blog   ---------------------

---
title: Community Demo {date}
author: {author}
tags:
  - demo
---
The Community Demo is available on the [Pulp YouTube Channel](https://www.youtube.com/PulpProject). See the agenda below.

<iframe width="560" height="315" src="https://www.youtube.com/embed/{youtube_slug}" frameborder="0" allowfullscreen></iframe>
""".format(youtube_slug=youtube_slug, date=args.date, author=args.author))

    for demo in demos:
        print("""[{title} ({nick}){version_str}](http://www.youtube.com/watch?v={youtube_slug}&t={time})
""".format(title=demo.title, nick=demo.nick, youtube_slug=youtube_slug, time=demo.time, version_str=demo.version_str))


if __name__ == "__main__":
    main()

