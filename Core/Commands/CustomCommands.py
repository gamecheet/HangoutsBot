import asyncio
import http.client
from Core.Commands.Dispatcher import DispatcherSingleton
from Core.Util import UtilBot
from Core.Util import UtilDB
import hangups
import urllib
from urllib import parse, request, error
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import random
import errno
from glob import glob
import subprocess
import types
from .fliptextdict import fliptextdict

@DispatcherSingleton.register
def me(bot, event, *args):
    pass

@DispatcherSingleton.register
def s(bot, event, *args):
    pass

@DispatcherSingleton.register
def load_images_from_folder(bot, event, *args):
    folder = args[0]
    # loop through folder
    for filename in glob(os.path.join('images', folder, '*')):
        # if filename not in imageids, upload it and store filename,id
        filetail = os.path.split(filename)[1]
        filehead = os.path.split(os.path.split(filename)[0])[1]
        filekey = os.path.join(filehead, filetail)
        print(filekey)
        image_id = UtilDB.get_imageid_for_filename(filekey)
        if image_id is None:
            bot.send_message(event.conv,
                             "Uploading {}".format(filekey))
            image_id = yield from UtilBot.upload_image(bot, filename)
            UtilDB.set_imageid_for_filename(filekey, image_id)
            ####os.remove(filename)
        UtilDB.set_alias_for_filename(filekey, folder)
    bot.send_message(event.conv, "Done.")

@DispatcherSingleton.register
def ezhik(bot, event, *args):
    args = ['ezhik']
    yield from img(bot, event, *args)

def load_json(filename):
    try:
        imageids_filename = filename
        imageids = json.loads(open(imageids_filename, encoding='utf-8').read(), encoding='utf-8')
        return imageids
    except IOError as e:
        if e.errno == errno.ENOENT:
            imageids = {}
            return imageids
        else:
           print('Exception:')
           print(str(e))
           return None

def save_json(filename, dict):
    with open(filename, 'w') as f:
        json.dump(dict, f, indent=2, sort_keys=True)

@DispatcherSingleton.register_hidden
def load_aliased_images(bot, event, *args):
    file_exception = False
    try:
        imageids_filename = 'imageids.json'
        imageids = json.loads(open(imageids_filename, encoding='utf-8').read(), encoding='utf-8')
    except IOError as e:
        if e.errno == errno.ENOENT:
            imageids = {}
        else:
           print('Exception:')
           print(str(e))
           file_exception = True
    # loop through values in image_aliases.json
    aliases = load_json('image_aliases.json')
    for v in aliases.values():
        print('V = ' + str(v))
        for url in v if not isinstance(v, str) else [v]:
            print('URL = ' + url)
            # if url is not in imageids, upload it and store filename,id
            image_id = imageids.get(url)
            if image_id is None:
                print('URL = ' + url)
                filename = UtilBot.download_image(url, 'images')
                image_id = yield from UtilBot.upload_image(bot, filename)
                if not file_exception:
                    imageids[url] = image_id
                    with open(imageids_filename, 'w') as f:
                        json.dump(imageids, f, indent=2, sort_keys=True)
                    os.remove(filename)

@DispatcherSingleton.register
def image(bot, event, *args):
    yield from img(bot, event, *args)

@DispatcherSingleton.register
def img(bot, event, *args):
    if len(args) > 0 and args[0] == 'list':
        aliases = UtilDB.get_list_of_aliases()
        segments = []
        for alias in aliases:
            segments.append(hangups.ChatMessageSegment(alias))
            segments.append(hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK))
        bot.send_message_segments(event.conv, segments)
    elif len(args) > 0 and args[0] == 'add':
        if len(args) < 3:
           bot.send_message(event.conv, "Error: not enough arguments")
           return
        # alias is all arguments except the first and last
        alias = ''.join(args[1:len(args)-1])
        # strip spaces and non-alphanumeric characters
        alias = ''.join(filter(str.isalnum, alias))
        alias = alias.lower()
        url = args[len(args)-1]
        if UtilDB.get_urls_for_alias(alias) is not None:
            bot.send_message(event.conv, "Error: that alias already exists")
            return
        print(str(is_valid_url(url)))
        if not is_valid_url(url):
            bot.send_message(event.conv, "Error: invalid URL")
            return
        UtilDB.set_alias_for_url(url, alias)
        bot.send_message(event.conv, "Alias {alias} saved with URL {url}".format(alias=alias,url=url))
#no special arguments
    elif len(args) > 0:
        url = args[0]
        is_alias = False
        alias = ''.join(args)
        # strip spaces and non-alphanumeric characters
        alias = ''.join(filter(str.isalnum, alias))
        alias = alias.lower()
        alias_url_list = UtilDB.get_urls_for_alias(alias)
        if alias_url_list is not None:
            random_url = random.choice(alias_url_list)
            if random_url is not None:
                url = random_url
                is_alias = True
        image_id_list = UtilDB.get_imageids_for_alias(alias)
        image_id = None
        if image_id_list is not None:
            image_id = random.choice(image_id_list)
            is_alias = True
        if not is_valid_url(url):
            url = 'http://' + url
            if not is_valid_url(url) and image_id is None:
                bot.send_message(event.conv, "Error: invalid alias or URL.")
                return            
        if image_id is None:
            image_id = UtilDB.get_imageid_for_url(url)
        desc = None
        if not is_alias:
            image_info = UtilBot.get_image_info(url)
            url, desc = image_info
        if desc is None and not is_alias:
            desc = ' '.join(args[1:])
        print(image_id)
        if image_id is None:
            filename = UtilBot.download_image(url, 'images', False)
            image_id = yield from UtilBot.upload_image(bot, filename)
            UtilDB.set_imageid_for_url(url, image_id)
            os.remove(filename)
        bot.send_message_segments(event.conv,
            [hangups.ChatMessageSegment(desc)] if desc else None,
            image_id)

@DispatcherSingleton.register_hidden
def send_image(bot, event, image_id, desc=None):
    bot.send_message_segments(event.conv,
        [hangups.ChatMessageSegment(desc)] if desc else None,
        image_id)

@DispatcherSingleton.register
def log(bot, event, *args):
    msg = ' '.join(args)
    log = open('log.txt', 'a+')
    log.writelines(msg + "\n")
    for c in msg: log.writelines(hex(ord(c)) + " ")
    log.writelines("\n")
    log.close()

@DispatcherSingleton.register
def rate(bot, event, *args):
    ratings = dict(
                   agree      ="\u2714"
                  ,disagree   ="\u274c"
                  ,funny      ="\U0001f604"
                  ,winner     ="\U0001f31f"
                  ,zing       ="\u26a1"
                  ,informative="\u2139"
                  ,friendly   ="\u2764"
                  ,useful     ="\U0001f527"
                  ,optimistic ="\U0001f308"
                  ,artistic   ="\U0001f3a8"
                  ,late       ="\u23f0"
                  ,dumb       ="\U0001f4e6"
                  ,box        ="\U0001f4e6"
                  )

    try:
        bot.send_message(event.conv, ratings[args[0]])
    except KeyError:
        bot.send_message(event.conv, "That's not a valid rating. You are \U0001f4e6 x 1")

@DispatcherSingleton.register
def navyseals(bot, event, *args):
     if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*Navy Seals*
Usage: /navyseals
Purpose: Shits fury all over you.
""")
        bot.send_message_segments(event.conv, segments)
     else:
        bot.send_message(event.conv,
'''What the fuck did you just fucking say about me, you little bitch? \
I'll have you know I graduated top of my class in the Navy Seals, and \
I've been involved in numerous secret raids on Al-Quaeda, and I have over \
300 confirmed kills. I am trained in gorilla warfare and I'm the top sniper \
in the entire US armed forces. You are nothing to me but just another target. \
I will wipe you the fuck out with precision the likes of which has never \
been seen before on this Earth, mark my fucking words. You think you can \
get away with saying that shit to me over the Internet? Think again, fucker. \
As we speak I am contacting my secret network of spies across the USA and \
your IP is being traced right now so you better prepare for the storm, \
maggot. The storm that wipes out the pathetic little thing you call your \
life. You're fucking dead, kid. I can be anywhere, anytime, and I can kill \
you in over seven hundred ways, and that's just with my bare hands. Not only \
am I extensively trained in unarmed combat, but I have access to the entire \
arsenal of the United States Marine Corps and I will use it to its full \
extent to wipe your miserable ass off the face of the continent, you little \
shit. If only you could have known what unholy retribution your little \
"clever" comment was about to bring down upon you, maybe you would have held \
your fucking tongue. But you couldn't, you didn't, and now you're paying the \
price, you goddamn idiot. I will shit fury all over you and you will drown in \
it. You're fucking dead, kiddo.''')

@DispatcherSingleton.register
def yt(bot, event, *args):
    youtube(bot, event, *args)
    
@DispatcherSingleton.register
def YouTube(bot, event, *args):
    youtube(bot, event, *args)
    
@DispatcherSingleton.register
def xfiles(bot, event, *args):
    if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*xfiles*
Usage: /xfiles
Purpose: but what if bot is not kill
""")
        bot.send_message_segments(event.conv, segments)
    else:
        args = ['xfiles','theme']
        youtube(bot, event, *args)

@DispatcherSingleton.register
def ytban(bot, event, *args):
    search_terms = " ".join(args)
    youtube_info = UtilBot.find_youtube_info(search_terms)
    youtube_banlist = load_json('youtube_banlist.json')

    if youtube_info['item_id'] not in youtube_banlist:
        youtube_banlist.append(youtube_info['item_id'])

    bot.send_message(event.conv,
                     'Video "{title}" with ID "{id}" is now banned'.format(
                       title=youtube_info['item_title'], id=youtube_info['item_id']))

    save_json('youtube_banlist.json', youtube_banlist)

@DispatcherSingleton.register
def youtube(bot, event, *args):
    Segment = hangups.ChatMessageSegment
    if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*YouTube*
Usage: /youtube <optional: search parameter>
Purpose: Get the first result from YouTube\'s search using search parameter.
""")
        bot.send_message_segments(event.conv, segments)
    else:
        search_terms = " ".join(args)
        youtube_info = UtilBot.find_youtube_info(search_terms)
        youtube_banlist = load_json('youtube_banlist.json')

        if youtube_info['item_id'] in youtube_banlist:
            bot.send_message(event.conv, 'Sorry, that video is banned.')
        else:
            bot.send_message_segments(event.conv, [hangups.ChatMessageSegment('Result:', is_bold=True),
                                                   hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                                                   hangups.ChatMessageSegment(youtube_info['item_title'],
                                                                              hangups.SegmentType.LINK,
                                                                              link_target=youtube_info['item_url'])])

@DispatcherSingleton.register
def linktest(bot, event, *args):
        link_url = 'http://facepunch.com'
        link_title = 'Facepunch'
        bot.send_message_segments(event.conv,
                                  [hangups.ChatMessageSegment(link_title,
                                                              hangups.SegmentType.LINK,
                                                              link_target=link_url),
                                   hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                                   hangups.ChatMessageSegment(link_url,
                                                              hangups.SegmentType.LINK,
                                                              link_target=link_url)])

@DispatcherSingleton.register
def roulette(bot, event, *args):
    #static variables
    if not hasattr(roulette, "_rouletteChamber"):
        roulette._rouletteChamber = random.randrange(0, 6)
    if not hasattr(roulette, "_rouletteBullet"):
        roulette._rouletteBullet = random.randrange(0, 6)

    if len(args) > 0 and args[0] == 'spin':
        roulette._rouletteBullet = random.randrange(0, 6)
        bot.send_message(event.conv, '*SPIN* Are you feeling lucky?')
        return
    if roulette._rouletteChamber == roulette._rouletteBullet:
        roulette._rouletteBullet = random.randrange(0, 6)
        roulette._rouletteChamber = random.randrange(0, 6)
        bot.send_message(event.conv, '*BANG*')
    else:
        bot.send_message(event.conv, '*click*')
        roulette._rouletteChamber += 1
        roulette._rouletteChamber %= 6

#TODO: move this to UtilBot or find a native replacement
def choice(iterable):
    if isinstance(iterable, (list, tuple)):
        return random.choice(iterable)
    else:
        n = 1
        m = types.ModuleType('') # Guaranteed unique value.
        ret = m
        for x in iterable:
            if random.random() < 1/n:
                ret = x
            n += 1
        if ret is m:
            raise IndexError
        return ret

def _checkTheBall(questionLength):
    if not hasattr(_checkTheBall, "_responses"):
        _checkTheBall._responses = {'positive': ['It is possible.', 'Yes!', 'Of course.',
                           'Naturally.', 'Obviously.', 'It shall be.',
                           'The outlook is good.', 'It is so.',
                           'One would be wise to think so.',
                           'The answer is certainly yes.'],
              'negative': ['In your dreams.', 'I doubt it very much.',
                           'No chance.', 'The outlook is poor.',
                           'Unlikely.', 'About as likely as pigs flying.',
                           'You\'re kidding, right?', 'NO!', 'NO.', 'No.',
                           'The answer is a resounding no.', ],
              'unknown' : ['Maybe...', 'No clue.', '_I_ don\'t know.',
                           'The outlook is hazy, please ask again later.',
                           'What are you asking me for?', 'Come again?',
                           'You know the answer better than I.',
                           'The answer is def-- oooh! shiny thing!'],
             } 
    if questionLength % 3 == 0:
        category = 'positive'
    elif questionLength % 3 == 1:
        category = 'negative'
    else:
        category = 'unknown'
    return choice(_checkTheBall._responses[category])

@DispatcherSingleton.register
def eightball(bot, event, *args):
    if len(args) > 0:
        bot.send_message(event.conv, _checkTheBall(len(' '.join(args))))
    else:
        bot.send_message(event.conv, _checkTheBall(random.randint(0, 2)))

@DispatcherSingleton.register
def source(bot, event, *args):
    if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*Source*
Usage: /source
Purpose: Links to the GitHub
""")
        bot.send_message_segments(event.conv, segments)
    else:
        url = 'https://github.com/ShaunOfTheLive/HangoutsBot'
        segments = [hangups.ChatMessageSegment(url,
                                               hangups.SegmentType.LINK,
                                               link_target=url)]
        bot.send_message_segments(event.conv, segments)
        
@DispatcherSingleton.register
def fliptext(bot, event, *args):
    if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*Flip Text*
Usage: /fliptext <text>
Purpose: Flips your message 180 degrees
""")
        bot.send_message_segments(event.conv, segments)
    else:
        args = ' '.join(args)
        output = ''.join([fliptextdict.get(letter, letter) for letter in args])
        output = output[::-1]
        bot.send_message(event.conv, output)
        
@DispatcherSingleton.register
def latex(bot, event, *args):
    if ''.join(args) == '?':
        segments = UtilBot.text_to_segments("""\
*LaTeX*
Usage: /latex <LaTeX code>
Purpose: Renders LaTeX code to an image and sends it
""")
        bot.send_message_segments(event.conv, segments)
    else:
        cmd = "texvc /tmp images '" + \
              ' '.join(args).replace("'", "'\\''") + \
              "' utf-8 'rgb 1.0 1.0 1.0'"
        print('args: ')
        print(cmd)
        output = subprocess.check_output(cmd, shell=True)
        output = output.decode(encoding='UTF-8')
        print(output)
        filename = output[1:33] + '.png'
        filename = os.path.join('images', filename)
        image_id = yield from UtilBot.upload_image(bot, filename)
        send_image(bot, event, image_id)

@DispatcherSingleton.register
def greentext(bot, event, *args):
    """
    *Greentext*
    Usage: /greentext <text>
    Purpose: makes your text green and adds an epic maymay arrow
    """
    filename = 'greentext.png'
    message = ' '.join(args)
    if message[0] == '>':
        message = message[1:]
    message = message.replace('>', '\n>')
    message = '>' + message
    print(message)
    cmd = ['convert',
           '-size',
           '164x',
           '-font',
           '/usr/share/fonts/truetype/windows/arial.ttf',
           '-pointsize',
           '13',
           '-fill',
           '#789922',
           '-background',
           '#ffffee',
           'caption:%s' % message,
           filename]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        output = output.decode(encoding='UTF-8')
        if output != '':
            bot.send_message(event.conv, output)
        image_id = yield from UtilBot.upload_image(bot, filename)
        send_image(bot, event, image_id)
        os.remove(filename)
    except subprocess.CalledProcessError as e:
        output = e.output.decode(encoding='UTF-8')
        if output != '':
            bot.send_message(event.conv, output)

@DispatcherSingleton.register
def colour(bot, event, *args):
    yield from color(bot, event, *args)
 
@DispatcherSingleton.register
def color(bot, event, *args):
    filename = 'color.png'
    cmd = ['convert',
           '-size',
           '500x500',
           'xc:%s' % ' '.join(args),
           filename]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        output = output.decode(encoding='UTF-8')
        if output != '':
            bot.send_message(event.conv, output)
        image_id = yield from UtilBot.upload_image(bot, filename)
        send_image(bot, event, image_id)
        os.remove(filename)
    except subprocess.CalledProcessError as e:
        output = e.output.decode(encoding='UTF-8')
        if output != '':
            bot.send_message(event.conv, output)

from pyvirtualdisplay import Display
from selenium import webdriver

def send_webpage_screenshot(bot, event, url, viewportsize='1280x1024'):
    filename = 'screenie.png'

    cliprectsize = '0x0x' + viewportsize;

    try:
        cmd = ['capturejs',
               '--uri',
               url,
               '--viewportsize',
               viewportsize,
               '--output',
               filename,
               '--cliprect',
               cliprectsize]

        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        output = output.decode(encoding='UTF-8')
        if output != '':
            bot.send_message(event.conv, output)

        image_id = yield from UtilBot.upload_image(bot, filename)
        send_image(bot, event, image_id)
        os.remove(filename)
    except http.client.BadStatusLine as e:
        display.stop()
        bot.send_message(event.conv, 'Error: BadStatusLine')

def path2url(path):
    return parse.urljoin(
      'file:', request.pathname2url(os.path.abspath(path)))

@DispatcherSingleton.register
def html(bot, event, *args):
    html = '<meta charset="utf-8" />' + ' '.join(args)

    with open('tmp.html', 'w') as f:
        f.write(html)

    yield from send_webpage_screenshot(bot, event, path2url('tmp.html'))

def is_valid_url(url):
    # thanks to dperini and adamrofer
    urlregex = re.compile(
        u"^"
        # protocol identifier
        u"(?:(?:https?|ftp)://)"
        # user:pass authentication
        u"(?:\s+(?::\s*)?@)?"
        u"(?:"
        # ip address exclusion
        # private & local networks
        u"(?!(?:10|127)(?:\.\d{1,3}){3})"
        u"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
        u"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
        # ip address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last ip address of each class)
        u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
        u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
        u"|"
        # host name
        u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # tld identifier
        u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
        u")"
        # port number
        u"(?::\d{2,5})?"
        # resource path
        u"(?:/\S*)?"
        u"$"
        , re.UNICODE)
    print(str(urlregex.match(url) is not None))
    return (urlregex.match(url) is not None)

@DispatcherSingleton.register
def webshot(bot, event, *args):
    if len(args) == 1:
        url = args[0]
        viewportsize = '1280x1024'
    elif len(args) > 1:
        url = args[0]
        viewportsize = args[1]

    if not is_valid_url(url):
        url = 'http://' + url
        if not is_valid_url(url):
            bot.send_message(event.conv, "Error: invalid URL.")
            return            

    yield from send_webpage_screenshot(bot, event, url, viewportsize)

@DispatcherSingleton.register
def subreddit(bot, event, *args):
    subreddit = args[0]
    reddit_url_prefix = 'https://www.reddit.com/r/'
    link_url = reddit_url_prefix + subreddit

    user_agent = 'python:HangoutsBot:r233 (by /u/shillbert)'
    res = requests.head(link_url, headers={'User-Agent': user_agent})
    if (res.status_code == 404 or
           (res.status_code == 302 and
            'subreddits/search' in res.headers.get('location'))):
        bot.send_message(event.conv, "That subreddit does not exist.")
    else:
        bot.send_message_segments(event.conv,
                                  [hangups.ChatMessageSegment(link_url,
                                                             hangups.SegmentType.LINK,
                                                             link_target=link_url)])

