# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig
import re

SITE_IDENTIFIER = '1kino_in'
SITE_NAME = '1Kino'
SITE_ICON = '1kino.png'

URL_MAIN = 'http://1kino.in/'
URL_KINO = URL_MAIN + 'kinofilme'
URL_FILME = URL_MAIN + 'filme'
URL_SHOWS = URL_MAIN + 'serien'
URL_PORN = URL_MAIN + 'porn'
URL_SEARCH = URL_MAIN + '?s=%s'
URL_DROP = URL_MAIN + 'drop.php'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_KINO)
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sCat', 'Filme')
    oGui.addFolder(cGuiElement('Filme Genre', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_SHOWS)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    if showAdult():
        params.setParam('sUrl', URL_PORN)
        oGui.addFolder(cGuiElement('Porn', SITE_IDENTIFIER, 'showEntries'), params)
        params.setParam('sCat', 'Porn')
        oGui.addFolder(cGuiElement('Porn Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = '>%s</a>\s*<ul[^>]*class="sub-menu"[^>]*>(.*?)</ul>' % params.getValue('sCat')
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<li>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*</li>'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    oRequestHandler = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequestHandler.request()

    sPattern = '<li>\s*<div[^>]*>.*?'  # container start
    sPattern += '<img[^>]*data-lazy="([^"]*)"[^>]*>.*?'  # thumbnail
    sPattern += '<div[^>]*class="ui-tile"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^"]*)(?:\((\d+)\))</a>.*?'  # url / name / year
    sPattern += '<div[^>]*class="ui11"[^>]*>\s*<a[^>]*href="%s([^"]+)"[^>]*>.*?' % URL_MAIN  # genreUrl
    sPattern += '<div[^>]*class="ui-des">(.*?)</div>.*?'
    sPattern += '</li>'  # container end
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    isShowAdult = showAdult()

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sGenreUrl, sDesc in aResult:
        isTvshow = True if "serien" in entryUrl else False
        if not isTvshow and "serien" in sGenreUrl:
            isTvshow = True

        if not isTvshow and (URL_SEARCH % '') in entryUrl:
            sSubHtmlContent = cRequestHandler(sUrl, ignoreErrors=(sGui is not False)).request()
            sPattern = '<option[^>]*value="(s(\d+))"[^>]*>([^<]+)</option>'
            isTvshow, aDummyResult = cParser.parse(sSubHtmlContent, sPattern)

        if not isShowAdult and 'porn' in sGenreUrl.lower():
            continue

        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)

        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('entryUrl', sUrl)
        params.setParam('isTvshow', isTvshow)
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sDesc', sDesc)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = '<a[^>]*class="nextpostslink"[^>]*rel="next"[^>]*href="([^"]+)"[^>]*>'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'serien' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sDesc = params.getValue('sDesc')

    sHtmlContent = cRequestHandler(entryUrl).request()

    pattern = 'var\s*postID\s*=\s*"([^"]+)"'
    isMatch, postID = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    params.setParam('postID', postID)

    pattern = '<option[^>]*value="(s(\d+))"[^>]*>([^<]+)</option>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sId, sSeasonNr, sSeasonTitle in aResult:
        oGuiElement = cGuiElement(sSeasonTitle, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setDescription(sDesc)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', sSeasonNr)
        params.setParam('sId', sId)
        oGui.addFolder(oGuiElement, params, True, total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sThumbnail = params.getValue('sThumbnail')
    sSeasonNr = params.getValue('sSeasonNr')
    sId = params.getValue('sId')
    postID = params.getValue('postID')
    sTVShowTitle = params.getValue('TVShowTitle')
    sDesc = params.getValue('sDesc')

    oRequest = cRequestHandler(URL_DROP)
    oRequest.addParameters('ceck', 'sec')
    oRequest.addParameters('option', sId)
    oRequest.addParameters('pid', postID)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()

    pattern = '<option[^>]*value="(s\d+_e(\d+))"[^>]*>([^<]+)</option>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for shID, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        oGuiElement.setMediaType('episode')
        params.setParam('shID', shID)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    isTvshowEntry = params.getValue('isTvshow')

    if isTvshowEntry == 'True':
        shID = params.getValue('shID')
        postID = params.getValue('postID')

        oRequest = cRequestHandler(URL_DROP)
        oRequest.addParameters('ceck', 'sec')
        oRequest.addParameters('option', shID)
        oRequest.addParameters('pid', postID)
        oRequest.setRequestType(1)
        sHtmlContent = oRequest.request()
    else:
        sUrl = params.getValue('entryUrl')
        sHtmlContent = cRequestHandler(sUrl).request()

    sPattern = '<li[^>]*class="stream"[^>]*>.*?'  # container start
    sPattern += '<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?'  # url / name
    sPattern += '</li>'  # container end
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        return []

    hosters = []
    for sUrl, sName in aResult:
        hosters.append({'link': sUrl, 'name': sName})
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('sUrl')

    refUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(sUrl, caching=False)
    oRequest.addHeaderEntry("Referer", refUrl)
    oRequest.request()

    return [{'streamUrl': oRequest.getRealUrl(), 'resolved': False}]


def showAdult():
    oConfig = cConfig()
    if oConfig.getSetting('showAdult') == 'true':
        return True
    return False


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
