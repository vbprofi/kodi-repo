# -*- coding: utf-8 -*-
import re

from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'szene-streams_com'
SITE_NAME = 'SzeneStreams'
SITE_ICON = 'szenestreams.png'

URL_MAIN = 'http://www.szene-streams.com/'
URL_MOVIES = URL_MAIN + 'publ/'
URL_SHOWS = URL_MAIN + 'load/'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMovieMenu'))
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showTvShowMenu'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showMovieMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('mediaTypePageId', 1)
    params.setParam('sUrl', URL_MOVIES)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showMovieSearch'))
    oGui.setEndOfDirectory()

def showTvShowMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('mediaTypePageId', 1)
    params.setParam('sUrl', URL_SHOWS)
    oGui.addFolder(cGuiElement('Alle Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showTvShowSearch'))
    oGui.setEndOfDirectory()

def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    oRequestHandler = cRequestHandler(params.getValue('sUrl'))
    sHtmlContent = oRequestHandler.request()
    # Get the URL
    pattern = '<a[^>]*?class="CatInf"[^>]*?href="(.*?)"[^>]*?>.*?'
     # Get the entry count
    pattern += '<div[^>]*?class="CatNumInf"[^>]*?>(\d+)</div>.*?'
    # Get the genre name
    pattern += '<div[^>]*?class="CatNameInf"[^>]*?>([^<>]+)</div>'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        return
    for sUrl, sNum, sName in aResult[1]:
        if not sUrl or not sNum or not sName: return
        oGuiElement = cGuiElement("%s (%d)" %(sName, int(sNum)), SITE_IDENTIFIER, 'showEntries')
        params.setParam('sUrl', sUrl)
        params.setParam('mediaTypePageId', 1)
        oGui.addFolder(oGuiElement, params)
    oGui.setEndOfDirectory()

def showEntries(sContent = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    sHtmlContent = ''
    if sContent:
        sHtmlContent = sContent
    else:
        sUrl = params.getValue('sUrl')
        if sUrl:
            oRequestHandler = cRequestHandler(sUrl, ignoreErrors = (sGui is not False))
            sHtmlContent = oRequestHandler.request()
    # Grab the thumbnail
    pattern = '<div class="screenshot".*?<a href="([^"]+)"'
    # Grab the name and link
    pattern += '.*?<a class="[^"]*?entryLink[^"]*?".*?href="([^"]+)">(.*?)</a>'
    # Grab the description
    pattern += '.*?<div class="MessWrapsNews2".*?>([^<>]+).*?</div>'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        return
    for sThumbnail, sUrl, sName, sDesc in aResult[1]:
        # Remove HTML tags from the name
        sName = re.sub('<[^<]+?>', '', sName)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc.strip())
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, bIsFolder = False)

    if not sGui:
        pattern = '<a class="swchItem" href="([^"]+)".*?><span>(\d+)</span></a>'
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0]:
            currentPage = int(params.getValue('mediaTypePageId'))
            for sUrl, sPage in aResult[1]:
                page = int(sPage)
                if page <= currentPage: continue
                params.setParam('sUrl', URL_MAIN + sUrl)
                params.setParam('mediaTypePageId', page)
                oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
                break

        oGui.setView('movies')
        oGui.setEndOfDirectory()

# Show the hosters dialog
def showHosters():
    params= ParameterHandler()
    oRequestHandler = cRequestHandler(params.getValue('entryUrl'))
    sHtmlContent = oRequestHandler.request()
    pattern = '<div class="inner" style="display:none;">'
    pattern += '.*?<a target="_blank" href="([^"]+)">'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        return
    hosters = []
    idx = 0
    previousName = ''
    for sUrl in aResult[1]:
        hoster = dict()
        hoster['link'] = sUrl
        hname = 'Unknown Hoster'
        try:
            hname = getHosterName(hoster['link'])
        except:
            pass
        if hname == 'linkcrypt.ws':
            resolveLinkcrypt(sUrl, hosters)
            continue
        if previousName != hname:
            idx = 1
        previousName = hname
        hname = "Part %d - %s" % (idx, hname)
        idx += 1

        hoster['name'] = previousName
        hoster['displayedName'] = hname
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

# Show the search dialog, return/abort on empty input
def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def showMovieSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    data = getSearchResult(sSearchText, URL_MOVIES)
    showEntries(data, oGui)
    oGui.setEndOfDirectory()

def showTvShowSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    data = getSearchResult(sSearchText, URL_SHOWS)
    showEntries(data, oGui)
    oGui.setEndOfDirectory()

def getHosterUrl(sUrl = False):
    oParams = ParameterHandler()
    if not sUrl:
        sUrl = oParams.getValue('url')
    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results

def getHosterName(name):
    return re.compile('^(?:https?:\/\/)?(?:www\.)?(?:[^@\n]+@)?([^:\/\n]+)', flags=re.I | re.M).findall(name)[0]

# Search using the requested string sSearchText
def _search(oGui, sSearchText):
    if not sSearchText: return
    data = getSearchResult(sSearchText, URL_MOVIES, (oGui is not False))
    data += getSearchResult(sSearchText, URL_SHOWS, (oGui is not False))
    showEntries(data, oGui)

def getSearchResult(sSearchText, url, ignoreErrors = False):
    oRequest = cRequestHandler(url, ignoreErrors = ignoreErrors)
    oRequest.addParameters('query', sSearchText)
    oRequest.addParameters('a', '2')
    return oRequest.request()

# Taken and modified from pyLoad module/plugins/crypter/LinkCryptWs.py
def resolveLinkcrypt(sUrl, hosters):
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = '<form action="http://linkcrypt.ws/out.html"[^>]*?>.*?'
    pattern += '<input[^>]*?value="(.+?)"[^>]*?name="file"'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        return

    for idx, weblink_id in enumerate(aResult[1]):
        try:
            oRequest = cRequestHandler("http://linkcrypt.ws/out.html")
            oRequest.addParameters('file', weblink_id)
            data = oRequest.request()
            link = re.compile("top.location.href=doNotTrack\('(.+?)'\)").findall(data)[0]
            hname = getHosterName(link)
            hname = "Part %d - %s" % (idx + 1, hname)
            logger.info("Resolved LinkCrypt link: %s" % link)
            hoster = dict()
            hoster['link'] = link
            hoster['name'] = hname
            hoster['displayedName'] = hname
            hosters.append(hoster)
        except Exception, detail:
            logger.info(detail)
            pass
