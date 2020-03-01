import copy
import json
import pickle
import re
import sys
import time
from urllib.parse import urlencode

import requests
from tqdm import tqdm

from modules.variables import *


def update_exchange_rates():
    exchange_rates = {}
    for curr in ['RUB', 'USD', 'EUR']:
        exchange_rates[curr] = 1
    _ = do_requests_get(EX_URL)
    _rates = _.json()['rates']
    for curr in ['RUB', 'USD', 'EUR']:
        exchange_rates[curr] = _rates[curr]
    exchange_rates['RUR'] = exchange_rates.pop('RUB')
    return exchange_rates


def clean_tags(str_html):
    pattern = re.compile('<.*?>')
    result = re.sub(pattern, '', str_html)
    return result


def parse_salary(salary, exchange_rates):
    _s_range = {'from': None, 'to': None}
    if salary:
        _s_type = salary['gross']
        _s_currency = salary['currency']
        _s_factor = 0.87 if _s_type else 1
        for i in _s_range:
            if salary[i] is not None:
                _s_range[i] = int(_s_factor * salary[i] / exchange_rates[_s_currency])
    return _s_range['from'], _s_range['to']


def do_requests_get(_url, _params=None):
    if _params is None:
        _params = {}
    try:
        __response = requests.get(_url, params=_params, headers=HEADER, timeout=TIMEOUT)
        if __response.status_code == requests.codes.ok:
            return __response
        elif __response.status_code == 400:
            return None
    except requests.exceptions.HTTPError as err_h:
        print("Http Error:", err_h)
        sys.exit()
    except requests.exceptions.ConnectionError as err_c:
        print("Connecting Error:", err_c)
        sys.exit()
    except requests.exceptions.Timeout as err_t:
        print("Timeout Error:", err_t)
        sys.exit()
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
        sys.exit()


def get_vacancy(v_id, exchange_rates):
    _url = f'{API_BASE_URL}vacancies/{v_id}'
    _ = do_requests_get(_url)
    _response = _.json()
    _min_salary, _max_salary = parse_salary(_response['salary'], exchange_rates)
    return {
        'source': 'hh.ru',
        'vacancy_id': v_id,
        'vacancy_url': _url,
        'vacancy_name': _response['name'],
        'employer_name': _response['employer']['name'],
        'min_salary': _min_salary,
        'max_salary': _max_salary,
        'experience': _response['experience']['name'],
        'schedule': _response['schedule']['name'],
        'employment': _response['employment']['name'],
        'key_skills': [_key_skill['name'] for _key_skill in _response['key_skills']],
        'description': clean_tags(_response['description']),
    }


def get_vacancies(query, exchange_rates):
    _ids = []
    _parameters = {'text': query, **DEFAULT_PARAMETERS}
    _url = f'{API_BASE_URL}vacancies?{urlencode(_parameters)}'
    _ = do_requests_get(_url)
    _ = _.json()
    _num_vacancies = _['found']
    _nm_pages = _['pages']
    if _num_vacancies == 0:
        return None
    print(f'Найдено {_num_vacancies} вакансий.')
    for i in range(_nm_pages + 1):
        _ = do_requests_get(_url, {'page': i})
        if not _:
            break
        data = _.json()
        if 'items' not in data:
            break
        if data['items']:
            _ids.extend(x['id'] for x in data['items'])

    _vacancies = []
    for _id in tqdm(_ids):
        time.sleep(TIMEOUT)
        _vacancy = get_vacancy(_id, exchange_rates)
        _vacancies.append(_vacancy)
    return _vacancies


def get_area(v_area):
    _url = f'{API_BASE_URL}areas/'
    _ = do_requests_get(_url)
    _areas = _.text
    i = _areas.find(v_area)
    if i != -1:
        for j in range(i, 0, -1):
            if _areas[j] == '{':
                return re.search('\d+', _areas[j:i]).group()
    else:
        return None


def process_hhru(_vacancy_name, _area_name, _area_id):
    key_skills = {}
    vacancy_info = {}
    min_salary = []
    max_salary = []
    if _area_id is not None:
        DEFAULT_PARAMETERS['area'] = _area_id
    else:
        print(f'Регион {_area_name} не найден на HH.RU. Оставлем регион по умолчанию')
    file_pickle = f'HH_vacancies_{_vacancy_name.replace(" ", "_")}_area_{_area_id}.pkl'
    file_json = f'HH_vacancies_{_vacancy_name.replace(" ", "_")}_area_{_area_id}.json'
    exchange_rates = update_exchange_rates()
    print('Идет процесс обработки запроса...')
    _vacancies = get_vacancies(_vacancy_name, exchange_rates)
    if USE_FILE:
        with open(file_pickle, 'wb') as file:
            pickle.dump(_vacancies, file)
    if not _vacancies:
        return None, None
    print('Идет процесс обработки статистики...')
    time.sleep(TIMEOUT + 1)
    for vacancy in tqdm(_vacancies):
        for skill in vacancy['key_skills']:
            key_skills[skill] = key_skills.get(skill, 0) + 1
        min_salary.append(vacancy['min_salary'] if vacancy['min_salary'] else 0)
        max_salary.append(vacancy['max_salary'] if vacancy['max_salary'] else 0)
    min_salary = list(filter(lambda x: x != 0, min_salary))
    max_salary = list(filter(lambda x: x != 0, max_salary))
    cloud_skills = copy.deepcopy(key_skills)
    avg_min_salary = int(round(sum(min_salary) / len(min_salary), 0))
    avg_max_salary = int(round(sum(max_salary) / len(max_salary), 0))
    vacancy_info['1.keywords'] = _vacancy_name
    vacancy_info['2.count'] = len(_vacancies)
    vacancy_info['3.avg_min_salary'] = avg_min_salary
    vacancy_info['4.avg_max_salary'] = avg_max_salary
    vacancy_info['5.skills_quantity'] = len(key_skills)
    for skill in key_skills:
        key_skills[skill] = [key_skills.get(skill),
                             str(round(key_skills.get(skill)/vacancy_info['5.skills_quantity'] * 100, 2)) + '%']
    vacancy_info['6.requirements'] = key_skills
    if USE_FILE:
        with open(file_json, 'w', encoding='utf-8') as file:
            json.dump(vacancy_info, file, ensure_ascii=False, sort_keys=True)
    return vacancy_info, cloud_skills
