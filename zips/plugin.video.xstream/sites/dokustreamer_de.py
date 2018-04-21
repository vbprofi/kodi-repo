# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
import re

SITE_IDENTIFIER = 'dokustreamer_de'
SITE_NAME = 'Dokustreamer'
SITE_ICON = 'dokustreamer.png'

URL_MAIN = 'https://dokustreamer.de/'
URL_HDDOKU = URL_MAIN + 'category/doku/dokus/hd-doku-stream'
URL_BELIEBTE = URL_MAIN + 'beliebte-dokumentationen'
URL_SEARCH = URL_MAIN + '?s=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Dokus', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_HDDOKU)
    oGui.addFolder(cGuiElement('HD Dokus', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_BELIEBTE)
    oGui.addFolder(cGuiElement('Beliebte Dokumentationen', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Kategorien', SITE_IDENTIFIER, 'showKategorien'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showKategorien():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    isMatch, aResult = cParser.parse(sHtmlContent, '<li[^>]*class="cat-item.*?"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^"]+)</a>\s*\((\d+)\)')

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sNr in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement("%s (%s)" % (sName, sNr), SITE_IDENTIFIER, 'showEntries'), params, True, total)

    oGui.setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()

    pattern = '<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>\s*<img[^>]*src="([^"]*)"[^>]*>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        pattern = '<h\d[^>]*class="[^"]+entry-title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>()'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        sThumbnail = re.sub('-\d+x\d+\.', '.',sThumbnail)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        pattern = '<a[^>]*class="nextpostslink"[^>]*rel="next"[^>]*href="([^"]+)"[^>]*>'
        isMatch, aResult = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatch:
            params.setParam('sUrl', aResult)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<iframe[^>]*src="([^"]+)"[^>]*allowfullscreen[^>]*>'
    aResult = cParser.parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sUrl
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip() , oGui)
