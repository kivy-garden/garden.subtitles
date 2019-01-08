'''This Module implements a srt parsing and displaying for videos, the
idea is to position it on top of a Video or VideoPlayer widget, set its
source, and bind its position to the one of the video.

example ::

    FloatLayout:
        Video:
            id: video
            source: 'file.mp4'

        Subtitles:
            source: 'file.srt'
            y: video.y
            center_x: self.width and video.center_x
            position: video.position


You can override the caption class if you want to tweak the appearance,
the default implementation `CaptionLabel`, implements a trick to make
text look more crisp.
'''

from os.path import exists
from datetime import datetime
import codecs



from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty, DictProperty
from kivy.lang import Builder
from kivy.factory import Factory

TMFT = '%H:%M:%S,%f'


KV = '''
#:import RGBA kivy.utils.get_color_from_hex

<Subtitles>:
    orientation: 'vertical'
    size_hint: None, None
    size: self.minimum_size


<CaptionLabel@Label>:
    pos_hint: {'center_x': .5}
    size_hint: None, None
    color: RGBA('FFFFFF')
    halign: 'center'
    outline_width: 2
    outline_color: RGBA('333333')
    font_size: 40
    size: [wh * .5 for wh in self.texture_size]
    canvas.before:
        Scale:
            origin: self.center
            x: .5
            y: .5
'''


class Subtitles(BoxLayout):
    source = StringProperty()
    captions = ListProperty()
    caption_cls = 'CaptionLabel'
    caption_labels = ListProperty()
    position = NumericProperty()
    time_format = StringProperty(TMFT)

    def on_source(self, *args):
        source = self.source
        tmft = self.time_format
        if exists(source):
            origin = datetime.strptime('00:00:00,000', tmft)
            with codecs.open(source, encoding='utf8') as f:
                new = True
                captions = []
                cap = {}

                for line in f:
                    line = line.strip()
                    if new:
                        new = False
                        cap = {'id': int(line.strip(u'\ufeff'))}

                    elif not line:
                        new = True
                        captions.append(cap)
                        continue

                    elif '-->' in line:
                        begin, end = line.split('-->')
                        begin = begin.strip()
                        end = end.strip()

                        begin = datetime.strptime(begin, tmft)
                        end = datetime.strptime(end, tmft)
                        cap['start'] = (begin - origin).total_seconds()
                        cap['end'] = (end - origin).total_seconds()

                    else:
                        text = cap.get('text', '')
                        if text:
                            text += '\n'
                        text += line
                        cap['text'] = text

                captions.append(cap)

            self.captions = captions
        else:
            self.captions = []

    def on_captions(self, *args):
        labels = []
        cls = Factory.get(self.caption_cls)

        i = 0
        while self.caption_labels:
            lbl = self.caption_labels.pop()
            if i < len(self.captions):
                cap = self.captions[i]
                lbl.text = cap['text']
                labels.append(lbl)
                i += 1
            else:
                break

        for j in range(i, len(self.captions)):
            cap = self.captions[j]
            lbl = cls(text=cap['text'])
            labels.append(lbl)

        self.caption_labels = labels

    def on_position(self, *args):
        t = self.position
        display = []

        for i, cap in enumerate(self.captions):
            if cap['start'] < t < cap['end']:
                display.append(self.caption_labels[i])

        if display == self.children:
            return

        self.clear_widgets()
        for lbl in display:
            self.add_widget(lbl)


Builder.load_string(KV)
