import requests 
import sqlite3
from bs4 import BeautifulSoup

url = 'https://quotes.toscrape.com/'
requests.get(url)