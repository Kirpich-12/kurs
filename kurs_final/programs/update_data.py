from repo import DataRepo
from parser import Parser
from models import Link, Api_var

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
        repo = DataRepo()
        return repo.list_bank_branches()
    else:
        repo = DataRepo()
        repo.clear_database()
        parser = Parser(True)
        bank_branches = parser.get_branch(type)
        for branch in bank_branches:
            repo.set_bank_branch(branch)
        set_update_date()
        return bank_branches


def get_card(type: Link):
    # ЛОКАЛЬНЫЙ ИМПОРТ: вызывается только в момент создания карты
    from cart import ExchangeMap 
    
    map_builder = ExchangeMap(currency=type)
    map_builder.build()
    map_builder.save_and_open()


def get_back(var: Api_var, type: Link):
    """Единая точка входа для получения данных"""
    if var == Api_var.BOT: 
        return get_data(type)
    elif var == Api_var.CARD:
        return get_card(type)


def main():
    # Теперь все отработает корректно
    get_back(var=Api_var.CARD, type=Link.USD)

if __name__ == "__main__":
    main()