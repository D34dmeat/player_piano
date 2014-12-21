#!/bin/env python2.7
# -*- coding: utf-8 -*-

from scrapy import Spider, Item, Field
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor

import requests
import base64

class Artist(Item):
    url = Field()
    playlists = Field()

class PianomidiDeSpider(CrawlSpider):
    name = 'pianomidi_de'
    allowed_domains = ['piano-midi.de']
    start_urls = ['http://www.piano-midi.de/midi_files.htm']
    
    rules = (
        Rule(LinkExtractor(restrict_xpaths="//table[@class='midi']"), follow=False, callback='parse_artist'),)

    def parse_artist(self, response):
        artist = Artist()
        artist['url'] = response.url
        playlists = []
        for sel in response.xpath("//h2"):
            playlist_title = sel.xpath("text()").extract()[0]
            entries_table = sel.xpath("following-sibling::table")[0]
            tracks = []
            for row in entries_table.xpath("tr")[1:]:
                track = {}
                cols = row.xpath("td")
                track['title'] = cols[0].xpath('a/text()').extract()[0]
                track['midi_url'] = cols[0].xpath('a/@href').extract()[0]
                try:
                    track['tempo'] = cols[1].xpath('text()').extract()[0]
                except:
                    pass
                track['duration'] = cols[2].xpath('text()').extract()[0]
                track['midi_url_format0'] = cols[5].xpath('a/@href').extract()[0]
                tracks.append(track)
                
                # r = requests.get("http://www.piano-midi.de/"+track['midi_url'])
                # track['midi'] = base64.b64encode(r.text.encode("utf-8"))
                # r = requests.get("http://www.piano-midi.de/"+track['midi_url_format0'])
                # track['midi_format0'] = base64.b64encode(r.text.encode("utf-8"))

            playlists.append({'title':playlist_title, 'tracks':tracks})
        artist['playlists'] = playlists
        return artist
