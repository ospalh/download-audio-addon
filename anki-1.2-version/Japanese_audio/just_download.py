# -*- coding: utf-8 -*-
# 
# Author: Roland, ospalh@gmail.com
# Inspiration and remaining code snippets: Tymon Warecki
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

'''
Store 
'''

import hashlib
from remove_kanji import removeKanji


import os, urllib


## CONFIGURATION SECTION

# Try to download as soon as a suitable card appears. (In this case
# errors are automatically ignored.)
AUTO_DOWNLOAD_AUDIO = False

# Ask the user every time before a pronunciation gets saved
ALWAYS_ASK_BEFORE_SAVE = False

# If this is not empty, that is, not [] only download when a fact has
# at least one of these tags. Use quotes, and commas to separate entries.
REQUIRED_TAGS = ['vocabulary']

# If this is not empty, do not download when a fact has this tag
EXCLUSION_TAGS = ['nodownload']


# Change these to mach the field names of your decks
ExpressionField = u"Expression"
ReadingField = u"Reading"
AudioField = u"Audio"

# Likely other names:
#ExpressionField = u"Japanese"
#ExpressionField = u"Kanji"
#ReadingField = u"Kana"
#AudioField = u"Sound"

# Add sha256 hashes of files here that should not be added to cards.
# Remember to separate entries with commas.
BlacklistHashes = [
    # 'audio is not available' message as of 2012-03-05
    'ae6398b5a27bc8c0a771df6c907ade794be15518174773c58c7c7ddd17098906',
    'fa9d06dfdaac5736a4cbbdbe496589a4048b8399bc6bc683710168343dd895fc'
    ]

## END CONFIGURATION SECTION

# Be careful about changes below this.

# Tag placed on cards where a download has been tried unsuccessfully
DOWNLOAD_FAILURE_TAG = 'bad_audio_download'
# Tag placed on cards where a download has worked
DOWNLOAD_SUCCESS_TAG = 'good_audio_download'

soundFileExtension = '.mp3'
downloadedFileExtension = '.php'

urlJDICT='http://assets.languagepod101.com/dictionary/japanese/audiomp3.php?'

# Code

class JapaneseAudioDownloader():
    """A class to download a pronunciation for the current card when
    certain conditions are met."""
    def __init__(self):
        self.card = mw.currentCard
        self.mediaDir = None
        self.kana = u''
        self.kanji = u''
        self.fileNameIn = u''
        self.fileNameOut = u''

    def maybeDownloadAudio(self):
        """Check whether we should download a pronunciation for this
        card and try to do so if that is the case. Then save add the
        pronunciation to the card"""
        if not self.cardCanUseAudio():
            return
        self.createKanaKanjiStrings()
        self.buildFileName()
        try:
            self.retrieveFile()
        except ValueError as ve:
            if str(ve).find('lacklist') > -1:
                # Clean up.
                os.remove(self.fileNameIn)
            # An reraise.
            raise ve
        self.updateCard()

    def cardCanUseAudio(self):
        """Check a number of conditions. Only when all are met return
        True. That means it makes sense to try to download the
        audio."""
        global kakasi
        if not self.card:
            # No card to operate on. The non-card very much can’t
            # store audio.
            return False
        if REQUIRED_TAGS:
            required_found = False
            for tag in REQUIRED_TAGS:
                if self.card.hasTag(tag):
                    required_found = True
                    break
            if not required_found:
                return False
        for tag in EXCLUSION_TAGS:
            if self.card.hasTag(tag):
                return False
        if self.card.hasTag(DOWNLOAD_FAILURE_TAG) \
                or self.card.hasTag(DOWNLOAD_SUCCESS_TAG):
            # Already tried this card.
            return False
        if self.card.hasTag(DOWNLOAD_FAILURE_TAG) \
                or self.card.hasTag(DOWNLOAD_SUCCESS_TAG):
            # Already tried this card.
            return False
        fields = [field.name for field in self.card.fact.fields]
        if not AudioField in fields:
            # No audio field. Nowhere to put downloaded file.
            return False
        if re.findall('\[sound:(.*?)]',self.card.fact[AudioField]):
            # Card already has some [sound:] in the Audio field.
            return False
        if (not ReadingField in fields) \
                or ((not ExpressionField in fields) or not kakasi):
            # No reading or no Expression or Expression but no way to
            # translate that to a reading.
            return False
        # Looks good so far.
        return True


    def createKanaKanjiStrings(self):
        global kakasi
        reading = self.card.fact[ReadingField]
        if (reading):
            self.kana = removeKanji(reading)
        self.kanji = self.card.fact[ExpressionField]
        if kakasi and self.kanji and (not self.kana):
            # No kana (yet), kanji and a way to translate
            self.kana = kakasi.reading(self.kanji)
        if self.kanji == self.kana:
            self.kanji = u''

    def buildFileName(self):
        self.mediaDir = self.card.deck.mediaDir(create=True)
        base_name = self.kana
        if self.kanji:
            base_name += u'_' + self.kanji
        fname = base_name + soundFileExtension
        if not os.path.exists(os.path.join(self.mediaDir, fname)):
            self.fileNameIn = os.path.join(self.mediaDir, fname)
            return
        # Try to find a valid name, give up after a somewhat arbitrary
        # number of tries
        for fname_offset in range(1, 2000):
            fname = base_name + str(fname_offset) + soundFileExtension 
            if not os.path.exists(os.path.join(self.mediaDir, fname)):
                self.fileNameIn = os.path.join(self.mediaDir, fname)
                return
        raise IOError('Cannot find unused file with name \'%s\'.' % base_name + soundExtension)
        
    def buildQueryUrl(self):
        qdict = {}
        if self.kanji:
            qdict['kanji'] = self.kanji.encode('utf-8')
        if self.kana:
            qdict['kana'] = self.kana.encode('utf-8')
        if not qdict:
            raise ValueError('No strings to build query from')
        return urlJDICT + urllib.urlencode(qdict)

    def retrieveFile(self):
        self.fileNameOut, retrieveHeader = urllib.urlretrieve(self.buildQueryUrl(), self.fileNameIn)
        retrievedHash = hashlib.sha256(file(self.fileNameOut, 'r').read())
        if retrievedHash.hexdigest() in BlacklistHashes:
            self.card.fact.tags = addTags(DOWNLOAD_FAILURE_TAG, self.card.fact.tags)
            self.card.fact.setModified(textChanged=True,deck=self.card.deck)
            self.card.deck.save()

            raise ValueError('Retrieved file is in Blacklist. (No pronunciation found.)')



    def updateCard(self):
        basename = os.path.basename(self.fileNameOut)
        if not basename:
            raise  IOError('No name to add to card found in \'%\'' % self.fileNameOut)
        self.card.fact[AudioField] += u"[sound:%s]" % basename
        self.card.fact.tags = addTags(DOWNLOAD_SUCCESS_TAG, self.card.fact.tags)
        self.card.fact.setModified(textChanged=True, deck=self.card.deck)
        self.card.deck.save()

    def processAudio(self):
        # todo: Add support for pySox, remove silence at the
        # beginning, normalize sound.
        pass
        



def getLogoFile(fileName):
    logoFile = os.path.join(mw.config.configPath,'plugins/Japanese_audio',fileName)   
    return logoFile
    
def downloadAudio():
    japaneseDownloader = JapaneseAudioDownloader()
    try:
        japaneseDownloader.maybeDownloadAudio()
    except ValueError as ve:
            utils.showInfo('JapaneseAudioDownload reported a problem: \'%s\'' \
                               %str(ve))
    except IOError as ioe:
        utils.showInfo('JapaneseAudioDownload reported an IO problem: \'%s\'' % str(ioe))
       


def toggleDownloadAction():
    japaneseDownloader = JapaneseAudioDownloader()
    mw.mainWin.actionJapaneseAudioDownload.setEnabled(japaneseDownloader.cardCanUseAudio())

def enableDownloadAction():
    mw.mainWin.actionJapaneseAudioDownload.setEnabled(True)


def disableDownloadAction():
    mw.mainWin.actionJapaneseAudioDownload.setEnabled(False)


def addActionToMenu(action):
    mw.mainWin.toolBar.addSeparator()
    mw.mainWin.toolBar.addAction(action)    
    mw.mainWin.menuEdit.addSeparator()
    mw.mainWin.menuEdit.addAction(action)    


def init():
    mw.mainWin.actionJapaneseAudioDownload = QAction(mw)
    icon = QIcon()
    icon.addPixmap(QPixmap(getLogoFile(u"AudioDownload.png")),QIcon.Normal,QIcon.Off)
    mw.mainWin.actionJapaneseAudioDownload.setIcon(icon)
    mw.mainWin.actionJapaneseAudioDownload.setIconText(u"Audio Download")
    mw.mainWin.actionJapaneseAudioDownload.setEnabled(False)
    mw.connect(mw.mainWin.actionJapaneseAudioDownload,SIGNAL("triggered()"),downloadAudio)
    # I really want to jiggle the action for each new card/question.
    # mw.connect(mw,SIGNAL("nextCard()"),toggleDownloadAction)

    if not AUTO_DOWNLOAD_AUDIO:
        addActionToMenu(mw.mainWin.actionJapaneseAudioDownload)

    addHook('disableCardMenuItems', disableDownloadAction)
    addHook('enableCardMenuItems', enableDownloadAction)




init()
