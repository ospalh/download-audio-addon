#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Author: Roland, ospalh@gmail.com
# Inspiration and remaining code snippets: Tymon Warecki
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

'''
Store 
'''

import hashlib

import os, urllib


## CONFIGURATION SECTION


# Add sha256 hashes of files here that should not be added to cards.
# Remember to separate entries with commas.
BlacklistHashes = [
    # 'audio is not available' message as of 2012-03-05
    'ae6398b5a27bc8c0a771df6c907ade794be15518174773c58c7c7ddd17098906',
    'fa9d06dfdaac5736a4cbbdbe496589a4048b8399bc6bc683710168343dd895fc'
    ]


urlJDICT='http://assets.languagepod101.com/dictionary/japanese/audiomp3.php?'

def getFile(query_dict):
   qurl = urlJDICT + urllib.urlencode(query_dict)
   basename = unicode(query_dict['Kana'], 'utf-8')
   try:
      basename += u' ' + unicode(query_dict['Kanji'], 'utf-8')
   except KeyError:
      pass
   basename += u'.mp3'
   fno, retrieveheader = urllib.urlretrieve(qurl, basename)
   retrievedHash = hashlib.sha256(file(fno, 'r').read())
   if retrievedHash.hexdigest() in BlacklistHashes:
     os.remove(fno)
     raise ValueError('Retrieved blacklisted file.')


if __name__ == '__main__':
   import sys

   try:
      kana = sys.argv[1]
      qd = dict(Kana=kana)
   except IndexError:
      raise ValueError('Kana are required as first command line argument')
   try:
      kanji = unicode(sys.argv[2], 'utf-8')
      qd['Kanji'] = kanji
   except IndexError:
      pass
      
   getFile(qd)
