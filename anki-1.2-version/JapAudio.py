# -*- coding: utf-8 -*-
#!/usr/bin/env python
# 
# original author: Tymon Warecki
# changes: Roland, ospalh@gmail.com
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from ankiqt import mw

def init():
    import Japanese_audio.download


mw.registerPlugin(u"Japanese audio download", 1)

from anki.hooks import addHook
addHook("init", init)

