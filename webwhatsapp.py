from selenium import webdriver
from dateutil.parser import *
import time
import os
from bs4 import BeautifulSoup
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class WhatsAPIDriver():
    URL="http://web.whatsapp.com"
    SELECTORS = {
        'firstrun':"#wrapper",
        'qrCode':"#window > div.entry-main > div.qrcode > img",
        'mainPage':".app.two",
        'chatList':".infinite-list-viewport",
        'messageList':"#main > div > div:nth-child(1) > div > div.message-list",
        'unreadMessageBar':"#main > div > div:nth-child(1) > div > div.message-list > div.msg-unread",
        'searchBar':"#side > div.search-container > div > label > input",
        'searchCancel':".icon-search-morph",
        'chats':".infinite-list-item",
        'chatBar':'div.input',
        'sendButton':'button.icon:nth-child(3)',
        'LoadHistory':'.btn-more',
        'UnreadBadge':'.icon-meta',
        'UnreadChatBanner':'.message-list',
        'ReconnectLink':'.action',
        'WhatsappQrIcon':'span.icon:nth-child(2)',
        'QRReloader':'.qr-container',
    }
    CLASSES = {
        'unreadBadge':'icon-meta',
        'messageContent':"message-text",
        'messageList':"msg"
    }

    driver = None

    def __init__(self, username):
        "Initialises the browser"
        self.driver = webdriver.Firefox()
        self.username = username
        self.driver.get(self.URL)
        self.driver.implicitly_wait(10)

    def firstrun(self):
        "Sends QRCode if not registered"
        if "CLICK TO RELOAD QR" in self.driver.page_source:
            self.reloadQRCode()
        WebDriverWait(self.driver, 30).until(\
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.SELECTORS['WhatsappQrIcon'])))
        self.driver.save_screenshot('media/%s.png' %(self.username))

    def press_send(self):
        "Presses the send button"
        self.driver.find_element_by_css_selector(self.SELECTORS['sendButton']).click()

    def enter_message(self, message):
        "Enters the message onto the chat bar"
        self.driver.find_element_by_css_selector(self.SELECTORS['chatBar']).send_keys(message)

    def select_contact(self, contact, entry = None):
        """
        Searches for the contact, as either name or number. If multiple exists, returns the
        'entry'th contact. If entry is not sent, return all the rows.
        """

        # Focusing before sending keys solves many problems
        self.driver.find_element_by_css_selector(self.SELECTORS['searchBar']).click()

        element = self.driver.find_element_by_css_selector(self.SELECTORS['searchBar']).send_keys(contact)
        time.sleep(1)

        try:
            result = self.get_user_list()
        except NoSuchElementException:
            return False

        # To get the most recent chat first, we reverse it
        contacts = result.find_elements_by_css_selector(self.SELECTORS['chats'])[::-1]
        time.sleep(1)

        if len(contacts) == 1:
            result.find_elements_by_css_selector(self.SELECTORS['chats'])[0].click()
        elif entry is None:
            self.driver.find_element_by_css_selector(self.SELECTORS['searchCancel']).click()
            return contacts
        else:
            contacts[entry].click()
        return True

    def get_user_list(self):
        element = self.driver.find_element_by_css_selector(self.SELECTORS['chatList'])
        return element

    def send_message(self, contact, message, entry=None):
        val = self.select_contact(contact, entry)
        if val != True:
            return val
        self.enter_message(message)
        self.press_send()
        return True
        pass

    def view_unread(self):
        script = '''
        var Chats = Store.Chat.models;
        if (!('last_read' in window)) {
            this.last_read = {};
            for (chat in Chats) {
                window.last_read[Chats[chat]._values.formattedTitle] = Math.floor(Date.now() / 1000);
            }
        }
        var Output = [];
        for (chat in Chats) {
            var temp = {};
            temp.contact = Chats[chat]._values.formattedTitle;
            temp.messages = [];
            var messages = Chats[chat].msgs.models;
            for (var i=messages.length-1;i>=0;i--) {
                if (messages[i]._values.t <= last_read[Chats[chat]._values.formattedTitle]) {
                    break;
                } else {
                    temp.messages.push(
                        {
                            message: messages[i]._values.body,
                            timestamp: messages[i]._values.t
                        }
                    );
                }
            }
            last_read[Chats[chat]._values.formattedTitle] = messages[messages.length-1]._values.t;
            if(temp.messages.length>0)
                Output.push(temp);
        }
        return Output;
        '''
        Store =  self.driver.execute_script(script)
        return Store

    def __unicode__(self):
        return self.username

    def __str__(self):
        return self.__unicode__()

    def reloadQRCode(self):
        self.driver.find_element_by_css_selector(self.SELECTORS['QRReloader']).click()