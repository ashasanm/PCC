import csv
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
# import pandas as pd
from time import sleep


class PlaystoreApp:
    """
     Playstore app crawler by web playstore url of an app, only takes app's comments.
    the data output is name, post date, ratings, likes, and comment text itself.
     """
    def __init__(self, app_url):
        self.app_url = app_url
        self.driver = self.driver_init()


    def driver_setting(self):
        """ webdriver configuration
        Notes:
            playstore won't accept any request 
            from headless webdriver instance
        """
        options = Options()
        options.headless = False
        return options


    def driver_init(self):
        """ initiate chromedriver

        Return:
            webdriver instance
        """
        options = self.driver_setting()
        driver = Chrome(executable_path='driver/chromedriver.exe',options=options)
        return driver


    def load_page(self):
        """ load page url with current webdriver """
        self.driver.implicitly_wait(30)
        self.driver.get(self.app_url)


    def get_cards(self, lookback_limit=150):
        """ Extracts comment container/cards on current page and limits cards extraction.
        Args:
            lookback_limit (int, optional): traceback limit of loaded cards 

        Returns:
            list: it returns a list of card xpath
        """
        cards_xpath = '/html/body/div[1]/div[4]/c-wiz/div/div[2]/div/div/main/div/div[1]/div[2]/div/div'
        cards = self.driver.find_elements_by_xpath(cards_xpath)
        if len(cards) <= lookback_limit:
            return cards
        else:
            return cards[-lookback_limit:]


    def clean_ratings(self, rating):
        """ gets rid of unecessary text of rating.
        Args:
            rating (str): unprocessed rating text

        Returns:
            str: processed rating text 
        """
        rating = rating.lower()
        rating = rating.replace('diberi rating', '')
        rating = rating.replace('rated ', '')
        rating = rating.replace(' stars out of five stars', '')
        rating = rating.strip()
        return rating

    
    def clean_comment(self, com_text):
        com_text = com_text.replace('\n', ' ')
        com_text = com_text.strip()
        return com_text

    
    def get_comments(self, card):
        """ Extracts Name, post_date, ratings, likes, 
        and comment's text from current card/comment container.

        
        Returns:
            dict: a dict of comment with key(name, post_date, likes, ratings, text)
        """
        # get name
        try:
            name_xpath = './div/div[2]/div[1]/div[1]/span'
            name = card.find_element_by_xpath(name_xpath).text
        except NoSuchElementException:
            name = ''
        # get post date
        try:
            post_date_xpath = './div/div[2]/div[1]/div[1]/div/span[2]'
            post_date = card.find_element_by_xpath(post_date_xpath).text
        except NoSuchElementException:
            post_date = ''
        # get likes
        try:
            likes_xpath = './div/div[2]/div[1]/div[2]/div/div[1]/div[2]'
            likes = card.find_element_by_xpath(likes_xpath).text
        except NoSuchElementException:
            likes = ''
        # get rating
        try:
            rating_xpath = './div/div[2]/div[1]/div[1]/div/span[1]/div/div'
            rating = card.find_element_by_xpath(rating_xpath).get_attribute('aria-label')
            rating = self.clean_ratings(rating)
        except NoSuchElementException:
            rating = ''
        # get comment's text
        try:
            text_xpath = './div/div[2]/div[2]/span[1]'
            com_text = card.find_element_by_xpath(text_xpath).text
            com_text = self.clean_comment(com_text)
        except NoSuchElementException:
            com_text = ''

        comment = (name, post_date, likes, rating, com_text)
        if self.check_comment(comment):
            return comment
        else:
            pass


    def save_to_csv(self, app_name, records, mode='a+'):
        header = ['name','post_date','likes','ratings','comment']

        with open('./output/{}.csv'.format(app_name), mode=mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if mode == 'w':
                writer.writerow(header)
            if records:
                writer.writerow(records)


    def check_comment(self, comment):
        """ check if all comment value is not empty
        Args:
            comment (tuple): extracted comment's data
        """
        return any(comment)


    def generate_id(self, comment):
        return ''.join(comment)    


    def start_crawl(self):
        """ Starts crawl data out of playstore while scrolling to the bottom of the pages,
        data will be saved into csv file or mongoDB(later)
        """
        self.load_page()
        scrolling = True
        last_position = self.driver.execute_script("return window.pageYOffset;")
        app_name = self.driver.find_element_by_xpath('/html/body/div[1]/div[4]/c-wiz/div/div[2]/div/div/main/c-wiz/c-wiz[1]/div/div[2]/div/div[1]/c-wiz[1]/h1/span').text
        # create csv file
        self.save_to_csv(app_name, records=None, mode='w')
        unique_comments = set()

        while scrolling:
            cards = self.get_cards()
            for index, card in enumerate(cards):
                comment = self.get_comments(card)
                try:
                    comment_id = self.generate_id(comment)
                except TypeError:
                    pass
                if comment_id not in unique_comments:
                    print(index, ' ', comment)
                    unique_comments.add(comment_id)
                    self.save_to_csv(app_name, comment)
                else:
                    print('pass extraction: data already extracted')

            scroll_attempt = 0
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                curr_position = self.driver.execute_script("return window.pageYOffset;")
                sleep(3)
                if last_position == curr_position:
                    print('scroll attempts: ', scroll_attempt)
                    scroll_attempt += 1
                    sleep(2)
                    if scroll_attempt == 2:
                        break
                    try:
                        moreBtn = self.driver.find_element_by_xpath('/html/body/div[1]/div[4]/c-wiz/div/div[2]/div/div/main/div/div[1]/div[2]/div[2]/div/span')
                        moreBtn.click()
                    except NoSuchElementException:
                        if scroll_attempt == 2:
                            scrolling = False
                            break
                        else:
                            continue
                else:
                    last_position = curr_position

        self.driver.quit()


if __name__ == '__main__':
    app_url = 'https://play.google.com/store/apps/details?id=co.brainly&hl=en&gl=US&showAllReviews=true'
    crawl = PlaystoreApp(app_url)
    crawl.start_crawl()

