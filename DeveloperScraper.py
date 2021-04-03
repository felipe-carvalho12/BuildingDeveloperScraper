import json
import re
from selenium.webdriver.common.keys import Keys


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DeveloperScraper:
    def __init__(self, webdriver):
        self.driver = webdriver
        self.developers_dict = {}


    def driver_quit_decorator(function):
        def wrapper(self, building):
            try:
                return function(self, building)
            finally:
                self.driver.quit()
        
        return wrapper


    def get_replaced_page_text(self, page_text):
        return (
            page_text
            .replace('Road', 'Rd')
            .replace('road', 'Rd')
            .replace('Avenue', 'Ave')
            .replace('avenue', 'Ave')
            .replace('Street', 'St')
            .replace('street', 'St')
            .replace('Court', 'Ct')
            .replace('court', 'Ct')
            .replace('West', 'W')
            .replace('west', 'W')
            .replace('East', 'E')
            .replace('East', 'E')
            .replace('North', 'N')
            .replace('north', 'N')
            .replace('South', 'S')
            .replace('South', 'S')
        )


    def scrape_from_page_text(self, page_text):
        patterns = [
            (r'[Bb]uilder(\(s\))?.\n?([A-Za-z][\w\s-]+)( at|,|\.|\n)', 2), # (query, index of the group containing the developer),

            (r'([Dd]eveloped|[Bb]uilt) by ([A-Za-z][\w\s-]+( at|in|,|\.|\n))', 2),

            (r'(of |,|\.|at|\n)([A-Za-z][\w\s-]+)[\s,]+(was the developer|developed the building)', 2),

            (r'[Dd]eveloper[-:\s]+([A-Z][\w\s-]+)( at|in|,|\.|\n)', 1),

            (r'([Ff]ully|[Cc]ompletely|[Ee]nterely) renovated in [12][0-9][0-9][0-9] by ([A-Za-z][\w\s-]+)( at|,|\.|\n)', 2)
        ]
        patterns_len = len(patterns)
        developer = None

        def get_cleaned_developer(developer):
            # removing remote letters from the beggining or end
            developer = ' '.join(list(filter(lambda string: len(string) > 1 or (string != developer[0] and string != developer[-1]), developer.split(' '))))

            # removing text after \n
            developer = developer.split('\n')[0]

            # removing prepositions from the beggining or end
            prepositions = ['in', 'at', 'on', 'by']
            for preposition in prepositions:
                splitted = developer.split(preposition)
                developer = splitted[-1 if preposition in splitted[0] else 0]

            return developer.strip()
        
        def scrape(i):
            nonlocal developer

            pattern = patterns[i]
            re_output = re.search(pattern[0], page_text)

            if re_output is None or len(re_output.group(pattern[1]).strip()) > 30:
                if i+1 < patterns_len:
                    scrape(i+1)
                else:
                    return
            else:
                developer = get_cleaned_developer(re_output.group(pattern[1]).strip())
        scrape(0)
        return developer

    
    def save_developer_to_db(self, building, developer):
        with open('db.json', 'w') as db:
            json.dump({ **self.developers_dict, building: developer }, db)


    def get_developer_from_db(self, building):
        with open('db.json', 'r') as db:
            self.developers_dict = json.load(db)
            if building in self.developers_dict.keys():
                return self.developers_dict[building]
            else:
                return None


    def make_google_search(self, query):
        self.driver.get('https://www.google.com')

        search_input = self.driver.find_element_by_xpath('/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/input')
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)

    
    def get_extra_developer_data(self, developer):
        self.make_google_search(f'{developer} site')
        site = self.driver.find_element_by_css_selector('.g .yuRUbf > a').get_attribute('href')
        return {
            'name': developer,
            'site': site
        }


    @driver_quit_decorator
    def get_developer(self, building):
        developer = self.get_developer_from_db(building)

        if developer is not None:
            return developer

        self.make_google_search(f'{building} developer')

        urls = list(map(lambda el: el.get_attribute('href'), self.driver.find_elements_by_css_selector('.g .yuRUbf > a')))

        for i, url in enumerate(urls):
            try:
                self.driver.get(url)
                print(f'{bcolors.OKBLUE}Opening link {i+1} ({bcolors.BOLD}{url}{bcolors.ENDC})...{bcolors.ENDC}')
            except:
                print(f'{bcolors.FAIL}Error. Skipping link ({url})...{bcolors.ENDC}')
                continue

            page_text = self.get_replaced_page_text(self.driver.find_element_by_css_selector('body').text)

            print(f'{bcolors.OKBLUE}Asserting page is about the building...{bcolors.ENDC}')
            if building not in page_text:
                print(f'{bcolors.OKCYAN}Page is not about the building.{bcolors.ENDC}')
                continue
            print(f'{bcolors.OKBLUE}Page is about the building. Searching for developer...{bcolors.ENDC}')

            developer = self.scrape_from_page_text(page_text)
            if developer is None:
                print(f'{bcolors.OKCYAN}No developer, trying again...{bcolors.ENDC}')
                continue

            print(f'{bcolors.OKGREEN}Developer found.{bcolors.ENDC}')
            
            developer = self.get_extra_developer_data(developer)

            self.save_developer_to_db(building, developer)

            return developer
        
        return None
