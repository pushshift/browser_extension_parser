#!/usr/bin/env python3

import sys
import ujson as json
import requests
import re
import html
import hashlib
from urllib.parse import unquote
from selectolax.parser import HTMLParser
import logging
logging.basicConfig(level=logging.INFO)



class BrowserExtensionParser:

    def __init__(self, **kwargs):
        '''Initialization Method'''
        self.contentHtml = None
        self.ft_keys = set()
        self.ft = {}
        self.parser = None


    def get_user_content(self):
        '''Parse user content from contentHtml using selectolax. This module is much more efficient compared to
        Beautifulsoup (bs4)
        '''
        user_content_div = self.parser.css("div.userContent")
        if len(user_content_div) > 1:
            ad_text = user_content_div[1].text()
            return ad_text
        else:
            logging.warning("Unable to parse the first user content piece from contentHtml")


    def get_user_content_wrapper(self):
        '''Parse user content wrapper from contentHtml. This is the full content of the ad text
        '''
        user_content_wrapper = self.parser.css("div.userContentWrapper")
        if user_content_wrapper:
            return user_content_wrapper[0].text()
        else:
            logging.warning("Unable to parse the user content or it is not present.")


    def get_story_attachment_image(self):
        '''Parse out the images from the ad within the contentHtml
        '''
        story_attachment_image = self.parser.css("div.fbStoryAttachmentImage")
        if story_attachment_image is not None:
            image_data = story_attachment_image[0].child.attributes
            return image_data

    def fetch_image(self, image_url):
        '''Method to fetch image data'''
        r = requests.get(image_url)
        if r.ok:
            return r.content
        else:
            logging.warning(f"Unable to fetch image at url: {image_url}.")

    def get_comment_count(self):
        m = re.search(r">(\d+) Comments</a>", self.contentHtml, re.MULTILINE)
        if m is not None:
            return m.group(1)
        else:
            logging.warning("Unable to extract the number of comments from contentHtml.")


    def get_share_count(self):
        m = re.search(r">(\d+) Shares</a>", self.contentHtml, re.MULTILINE)
        if m is not None:
            return m.group(1)
        else:
            logging.warning("Unable to extract the number of shares from contentHtml.")


    def load_contentHtml(self, html: str):
        self.contentHtml = html
        self.parser = HTMLParser(self.contentHtml)

    def extract_ft_values(self):
        '''Extract values for each ft element within the contentHtml field
        '''

        for ft_element in self.ft_keys:
            if ft_element == 'page_insights':
                objs = re.findall(r"ft\[page_insights\]\[\d+\](\[.*?\])=(.*?)(?:&)", self.contentHtml, re.MULTILINE)
                for obj in objs:
                    key = "page_insights" + obj[0].replace("][",".").replace("[",".").replace("]","") # Not very elegant
                    value = obj[1]
                    self.ft[key] = value
            else:
                value = re.search(f"ft\[{ft_element}\]=(.*?)(?:&)", self.contentHtml, re.MULTILINE)
                if value is not None:
                    self.ft[ft_element] = value.group(1)


    def extract_ft_keys(self):
        '''Extract individual fb elements. These elements start with ft and are followed by brackets
        for the corresponding key. For example, ft[qid] contains the Facebook advertisement id for the ad
        being parsed. A full list of fields can be extracted using regex (in this situation, regex can work
        well for a given HTML code piece with a known structure.
        '''

        '''This finds all of the corresponding ft elements within the contentHtml key that is returned by the
        browser extension. The purpose of many of these key fields is unknown, but it is worth extracting them
        anyway since they are available.'''

        ft_elements = re.findall(r"ft\[(.*?)\]", self.contentHtml, re.MULTILINE)

        for element in ft_elements:
            self.ft_keys.add(element)


##################################################################################
# Below are examples on using the Parser methods related to the contentHtml data #
##################################################################################


# Initialize Browser Extention Parser
bep = BrowserExtensionParser()

# Load sample contentHTML
contentHtml = open("contentHtml", "r").read()
contentHtml = unquote(html.unescape(contentHtml))
bep.load_contentHtml(contentHtml)

# Extract all ft keys present in contentHTML
bep.extract_ft_keys()

# Extract all values for all found ft keys
bep.extract_ft_values()

# Show found ft keys
print(bep.ft_keys)

# Dump ft values
print(bep.ft)

# Get Number of Comments
comment_count = bep.get_comment_count()
print(comment_count)

# Get Number of Shares
share_count = bep.get_share_count()
print(share_count)

# Get First User Content
first_user_content = bep.get_user_content()
print(first_user_content)

# Get User Content Wrapper
user_content_wrapper = bep.get_user_content_wrapper()
print(user_content_wrapper)

# Get Story Attachment Image
image_data = bep.get_story_attachment_image()
image_data_src = unquote(image_data['src'])
image_data_height = image_data['height']
image_data_width = image_data['width']
print(image_data_src, image_data_height, image_data_width)

# Fetch image data
image_file_data = bep.fetch_image(image_data_src)
image_md5_hash = hashlib.md5(image_file_data).hexdigest()
print(f"Image MD5 Hash: {image_md5_hash}")
