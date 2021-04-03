from time import sleep
from selenium import webdriver
from DeveloperScraper import DeveloperScraper


options = webdriver.chrome.options.Options()
options.headless = True
webdriver = webdriver.Chrome(options=options, executable_path='./chromedriver.exe')

scraper = DeveloperScraper(webdriver)

scraper.get_developer('12527 Bovet Ave')
