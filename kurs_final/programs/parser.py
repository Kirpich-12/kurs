from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep

from models import (
    BankBranch,
    Coords,
    ExchangeRate,
    BankOrg,
    Currency
)


USD = 'https://myfin.by/currency/usd'

class Parser:
    def __init__(
            self,
            debug_flag: bool = False):
        try:
            options = webdriver.ChromeOptions()
            self.debug_flag = debug_flag

            if not self.debug_flag:
                options.add_argument('--headless')

            self.driver = webdriver.Chrome(
                options=options
            )
        except ValueError:
            print(f'Ошибка доступа к сайту \n Ошибка:{self.status_code}')
        except Exception as e:
            print(f'Ошибка при создании драйвера: {e}')
        
    def _get_page(self, url) -> webdriver.Chrome:
        '''Запрос страницы'''
        self.driver.get(url)
        return self.driver
    
    def _press_button(self, button_xPath:str):
        '''Нажимаем кнопки по переданному XPath, debug_flag - выводит что нажали'''
        try:
            button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, button_xPath))
            )
            button.click()
            if self.debug_flag:
                print('=====================================')
                print(f'Нажата кнопка со следующим путем {button_xPath}')
                print('=====================================')
        except Exception as e:
            print('=====================================')
            print(f'Кнопка {button_xPath} не была нажата')
            print(e)
            print('=====================================')
        
    def get_branch(self, url:str, now_open:bool = True)-> list[BankBranch]:
        driver = self._get_page(url)
        answer = []
        self._press_button('/html/body/div[4]/div/div[3]/button[1]')  # Жмакает на куки
        sleep(2)
        self._press_button('//*[@id="deposit-rate-tabs"]/li[2]/a')  # Жмакает на режим отделений
        if now_open:  # Жмакает кнопку 'Отделения, которые работают сейчас'
            self._press_button('//*[@id="deposit-rate-tabs"]/li[2]/a')
        sleep(3)
        table = driver.find_element(By.XPATH, '//*[@id="currency-table-filials"]/table')  # Берем таблицу
        sleep(7)

        i = 2
        while True:
            try:
                if i % 20 == 0:
                    self._press_button('//*[@id="load-more-filials"]')
                    sleep(2)

                el = table.find_element(By.ID, f'bank-row-{i}')
                courses = el.find_elements(By.CLASS_NAME, 'currencies-courses__currency-cell')
                print(f'bank-row-{i}')
                tds = el.find_elements(By.TAG_NAME, 'td')
                adress = tds[0].find_element(By.CLASS_NAME, 'currencies-courses__branch-name').text
                bank_name = tds[0].find_element(By.CLASS_NAME, 'currencies-courses__bank-name').text
                sell_course = courses[0].text.strip()
                buy_course = courses[1].text.strip()

                if not sell_course or not buy_course:
                    print(f'  Пропуск: пустые курсы')
                    i += 2
                    continue

                coords = tds[7].get_attribute("data-fillial-coords")
                lat, lon = coords.replace('"', '').replace('[', '').replace(']', '').split(',')
                ans = BankBranch( bank_org= BankOrg(bank_name),
                                address= adress,
                                coords=Coords(lon, lat),
                                exchange_rates=(
                                    ExchangeRate(
                                        curr_from=Currency.BYN,
                                        curr_to=Currency.USD,
                                        rate=buy_course
                                    ),
                                    ExchangeRate(
                                        curr_from=Currency.USD,
                                        curr_to=Currency.BYN,
                                        rate=sell_course
                                    )
                                    ),
                )
                answer.append(ans)
                i += 2

            except Exception as e:
                print(f'Закончились отделения. Всего загружено: {len(answer)}')
                break

        return answer
    
    def __del__(self):
        print('Parser stoped')


if __name__ == "__main__":
    par = Parser()
    res = par.get_branch(USD)
    print(res)

