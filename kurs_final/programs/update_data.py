from repo import DataRepo
from parser import Parser
from models import Link, Api_var, Currency

from datetime import date


USD = Link.USD
EUR = Link.EUR
CNY = Link.CNY
CHF = Link.CHF  # Швейцарский франк

DAMP_FILE = "data_damp.txt"


def update_data(src: Link):
    data_repo = DataRepo()
    parser = Parser(True)

    bank_branches = parser.get_branch(src)

    for branch in bank_branches:
        data_repo.set_bank_branch(branch)
    
    return bank_branches


def date_check() -> bool:
    """
    Смотрит дату в файле data_damp.txt.
    Возвращает True, если дата совпадает с сегодняшней (данные актуальны).
    Возвращает False, если файла нет, он пуст или дата старая.
    """
    print('gg')
    try:
        with open(DAMP_FILE, "r", encoding="utf-8") as f:
            saved_date = f.read().strip()
        
        # Получаем сегодняшнюю дату в формате строки (например, '2023-10-25')
        today = str(date.today())
        
        # Если дата в файле совпадает с сегодняшней, значит обновлять не нужно
        return saved_date == today
        
    except FileNotFoundError:
        # Если файла еще нет, значит точно нужно обновлять
        return False
    except Exception as e:
        print(f"[WARNING] Ошибка чтения {DAMP_FILE}: {e}")
        return False


def set_update_date():
    """
    Записывает сегодняшнюю дату в файл data_damp.txt после успешного парсинга.
    """
    try:
        with open(DAMP_FILE, "w", encoding="utf-8") as f:
            f.write(str(date.today()))
    except Exception as e:
        print(f"[WARNING] Не удалось записать дату в {DAMP_FILE}: {e}")


def get_data(type: Link):
    if date_check():
        ans = update_data(type) 
        return ans 
    else:
        repo = DataRepo()
        repo.clear_database()
        parser = Parser(True)
        bank_branches = parser.get_branch(type)
        return bank_branches


def get_card(type: Link):
    # ЛОКАЛЬНЫЙ ИМПОРТ: вызывается только в момент создания карты
    from cart import ExchangeMap 
    
    map_builder = ExchangeMap(currency=type)
    map_builder.build()
    map_builder.save_and_open()


def format_for_tg(branches: list):
    """Форматирует данные для ТГ бота: топ 5 для покупки и топ 5 для продажи"""
    if not branches:
        return {"buy": [], "sell": []}

    # Фильтруем ветки по наличию курсов покупки/продажи
    buy_branches = []
    sell_branches = []

    for branch in branches:
        for rate in branch.exchange_rates:
            # Покупка: BYN -> Currency (нужна минимальная ставка)
            if rate.curr_from == Currency.BYN:
                buy_branches.append((branch, rate.rate))
            # Продажа: Currency -> BYN (нужна максимальная ставка)
            elif rate.curr_to == Currency.BYN:
                sell_branches.append((branch, rate.rate))

    # Сортируем и берем топ 5
    top_5_buy = sorted(buy_branches, key=lambda x: x[1])[:5]
    top_5_sell = sorted(sell_branches, key=lambda x: x[1], reverse=True)[:5]

    return {
        "buy": [branch for branch, _ in top_5_buy],
        "sell": [branch for branch, _ in top_5_sell]
    }


def get_back(var: Api_var, type: Link):
    """Единая точка входа для получения данных"""
    if var == Api_var.BOT:
        data = get_data(type)
        return format_for_tg(data)
    elif var == Api_var.CARD:
        return get_card(type)


def main():
    # Теперь все отработает корректно
    get_back(var=Api_var.CARD, type=Link.USD)

if __name__ == "__main__":
    main()