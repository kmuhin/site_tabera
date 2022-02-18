#!venv\Scripts\python.exe

# Получаю каталог кофе таберы в табличном виде с расчетом цен за 1кг
from sys import argv
from datetime import datetime
import re
from jinja2 import Environment, FileSystemLoader

from bs4 import BeautifulSoup
import requests
from pathlib import Path

import my_csv

workdir = Path(__file__).parent.absolute()
templates_dir = workdir.joinpath('templates')
reports_dir = workdir.joinpath('reports')

# каталог кофе таберы
url = 'https://www.taberacoffee.ru/catalog/svezheobzharennyy-kofe/#title'
url_domain = 'www.taberacoffee.ru'
# 15%
discount_percent = 15
discount = 1 - (discount_percent / 100)

vols_equality = {'200': 200, '500': 500, '1': 1000}
discount_exclusions = ['Бразильеро']


def get_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'cache - control': 'max - age = 0',
        "referer": "https://www.taberacoffee.ru/"
    }
    return headers


def get_html() -> BeautifulSoup:
    """
    получить из интернета страницу в формате BeautifulSoup
    :return:
    """
    headers = get_headers()
    req = requests.get(url, headers=headers)
    return BeautifulSoup(req.text, 'html.parser')


def gen_html_full_list(data):
    env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template('coffee_list.html')
    html = template.render(
        data=data,
        dt=datetime.now(),
        discount_percent=discount_percent
    )
    return html


def gen_html_uniq_list(data):
    env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template('coffee_list_uniq.html')
    html = template.render(
        data=data,
        dt=datetime.now(),
        discount_percent=discount_percent
    )
    return html


def save_html(file_prefix, html_data):
    """
    Отчет в формате html в папку reports с именем "file_prefix+Дата.html"
    :param file_prefix: начало имени фала
    :param html_data: html
    :return:
    """
    file_date = datetime.now().date().isoformat()
    file_name = f'{file_prefix}-{file_date}.html'
    file_path = reports_dir.joinpath(file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(html_data))
    print(file_path)


def grab_price(text: str):
    """
    Выдираю из строки данные объем, цена, скидка
    :param text: str
    :return: {'volume' - объем упаковки в граммах,
              'price' - цена за упаковку,
              'strike' - скидка,
              'price_1'- цена в пересчете за 1кг}
    """
    result = {'volume': 0, 'price': 0, 'strike': 0, 'price_1': 0}
    # рег для выдирания объема и цены
    re_vol_price = re.compile(r'([\d]+) ..\. \((.+) руб.')
    # рег для выдирания цены без скидки
    re_strike = re.compile(r' +(\d.+) руб.\)')
    match_vol_price = re_vol_price.search(text)
    if match_vol_price:
        result['volume'] = match_vol_price[1]
        # привожу объем к общим единицам к граммам
        result['volume'] = vols_equality[result['volume']]
        result['price'] = int(match_vol_price[2].replace(' ', ''))
        # расчитываю цену за 1 кг.
        result['price_1'] = result['price'] / result['volume'] * 1000
    match_strike = re_strike.search(text)
    if match_strike:
        result['strike'] = match_strike[1].replace(' ', '')
    return result


def get_data_vol_prices() -> list:
    """
    разбираю страницу в формате BeautifulSoup
    формирую список с данными по кофе
    {'title' - заголовок,
     'description' - описание (состав кофе и прочее),
     'href' - относительная ссылка на страницу,
     'vol_price' - объемы с ценами одной строкой без парсинга
    }
    :return: list of data
    """
    html = get_html()
    with open(workdir.joinpath('test.html'), 'w', encoding='utf-8') as f:
        f.write(str(html))
    cof_data = []
    # блоки с кофе
    tl_cof_div = html.find_all('div', attrs={'class': 'overlay_hover'})
    for t_cof_div in tl_cof_div:
        t_title = t_cof_div.find('p', attrs={'class': 'title'})
        # название
        title = t_title.text
        # описание
        description = t_cof_div.span.text
        # ссылка без домена
        href = t_title['onclick'].split('=')[1].strip("'")
        # объемы с ценами одной строкой без парсинга
        t_div_checkboxes = t_cof_div.find_all('div', attrs={'class': 'checkboxes'})
        tl_label_vols = []
        if len(t_div_checkboxes) > 0:
            tl_label_vols = t_div_checkboxes[1].find_all('label')
        for t_label_vol in tl_label_vols:
            vol_prices = t_label_vol.text.strip()
            cof = {'title': title, 'description': description, 'href': href, 'vol_price': vol_prices}
            if cof:
                cof_data.append(cof)
    return cof_data


def save_csv(data):
    """
    Отчет в формате CSV в папку со скриптом c именем
    "Имя скрипта+Дата.csv"
    :param data:
    :return:
    """

    file_date = datetime.now().date().isoformat()
    file_name = f'{Path(__file__).stem}-{file_date}.csv'
    file_path = workdir.joinpath(file_name)
    with my_csv.csv_dictwriter(file_path, data[0].keys()) as dw:
        for row in data:
            my_csv.convert_fields_float_to_str(row, fields=['price', 'price_1', 'discount', 'discount_1'])
            # strip new line and multiple spaces
            for key, value in row.items():
                if not isinstance(value, str):
                    continue
                row[key] = ' '.join(value.split())
            dw.writerow(row)
    print(file_path)


def get_data():
    """
    беру таблицу с данными по кофе.
    провожу преобразования: получаю отдельно цены и объем из строки,
        к ссылке добавляю домен
    :return:
    """
    data = get_data_vol_prices()
    for row in data:
        prices = grab_price(row['vol_price'])
        row.update(prices)
        # добавляю скидку, если наименования нет в исключениях и скидка еще не действует(strike=0)
        row['discount'] = 0
        row['discount_1'] = 0
        if row['title'] not in discount_exclusions and not row['strike']:
            row['discount'] = row['price'] * discount
            row['discount_1'] = row['price_1'] * discount
        # добавляю к ссылке домен
        row['href'] = f'https://{url_domain}{row["href"]}'
    return data


def get_uniq_title_min_price(data):
    # словарь с без повторов наименований, оставляю объем с минимальной ценой за 1кг
    data_new = {}
    for row in data:
        # выбираю минимальную цену наименования
        row_new = data_new.get(row['title'])
        if not row_new:
            data_new[row['title']] = row
        else:
            if row['price_1'] < row_new['price_1']:
                data_new[row['title']] = row
    return data_new


def main():
    b_csv = False
    if len(argv) > 1:
        if argv[1].lower() == 'csv':
            b_csv = True
        else:
            print(f'Usage: csv')
            return
    data = get_data()
    for row in sorted(data, key=lambda x: x['price_1']):
        print(f'{row["title"]:30} {row["volume"]:5} {row["price"]:5} {row["price_1"]:7}')
    if b_csv:
        save_csv(data)

    html_full = gen_html_full_list(data)
    save_html('coffee_tabera_list', html_full)

    data_uniq = get_uniq_title_min_price(data)
    html_uniq = gen_html_uniq_list(data_uniq)
    save_html('coffee_tabera_uniq', html_uniq)


if __name__ == '__main__':
    main()
