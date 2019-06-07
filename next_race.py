import datetime
import math
import random
import time

import requests
import requests_cache
from dateutil.parser import parse
from fake_useragent import UserAgent
from tabulate import tabulate

from driver_synonyms import initials_for_driver, rename_drivers

ERGAST_CALENDAR = 'http://ergast.com/api/f1/current.json'
PREDICTOR_URL = 'http://www.f1-predictor.com/api-next-race-prediction/'
RETRIES = 10


def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(math.floor(n/10) % 10 != 1)*(n % 10 < 4)*n % 10::4])


def raname_race_name(name, season):
    new_name = name.replace('Grand Prix', 'GP')
    new_name += ' ' + season
    return new_name


def get_json(url):
    retries_cnt = 0
    ua = UserAgent()
    headers = {'user-agent': ua.random}
    expire_after = datetime.timedelta(minutes=5)
    with requests_cache.CachedSession(expire_after=expire_after) as session:
        session.headers.update(headers)
        while retries_cnt < RETRIES:
            retries_cnt += 1
            response = session.get(url)
            if response.status_code == 200:
                return response.json()
            print("%s try: %s [%d]" %
                  (ordinal(retries_cnt), url, response.status_code))
            time.sleep(random.randint(1, 5))
    return None


def get_prediction():
    result = {}
    calendar = get_json(ERGAST_CALENDAR)

    # Error getting f1 calendar
    if not calendar:
        return result

    now = datetime.datetime.now(datetime.timezone.utc)
    race_next = None
    valid_period = False
    for race in sorted(calendar['MRData']['RaceTable']['Races'], key=lambda x: int(x['round'])):
        race_dt = parse(race['date'] + ' ' + race['time'])
        if race_dt > now:
            race_next = race
            valid_period = True
            break

    # The f1 calendar is stale
    if not valid_period:
        return result

    data = get_json(PREDICTOR_URL)

    # The f1-predictor fails to return meaningful data
    if not data:
        return result

    if data['race_name'] != raname_race_name(race_next['raceName'], race_next['season']):
        print("Race Name Mismatch between predictor and ergast:",
              end=' ')
        print(data['race_name'], "!=", raname_race_name(
            race_next['raceName'], race_next['season']))
        return result

    result['race_name'] = data['race_name']

    for part in ['qualifying', 'race']:
        result[part] = {}
        order_keys = sorted(
            list(data[part]['ranking'].keys()), key=lambda x: data[part]['ranking'][x])
        result[part]['ranking'] = order_keys
        result[part]['ranking_string'] = ""
        for driver in order_keys:
            result[part]['ranking_string'] += "%s. %s  \\\n" % (
                ordinal(data[part]['ranking'][driver]), driver)

        if result[part]['ranking_string']:
            result[part]['ranking_string'] = result[part]['ranking_string'][:-2]

        # Create 2 markdown tables
        half_size = len(order_keys) // 2

        table_1 = []
        table_1.append(['^row ^vs ^col'] + [initials_for_driver(driver)
                                            for driver in order_keys[:half_size]])
        table_2 = []
        table_2.append(['^row ^vs ^col'] + [initials_for_driver(driver)
                                            for driver in order_keys[half_size:]])

        for driver_1 in order_keys:
            row_1 = [initials_for_driver(driver_1)]
            row_2 = [initials_for_driver(driver_1)]
            for i, driver_2 in enumerate(order_keys):
                prob = ''
                for probs in data[part]['pairwise_probabilities']:
                    if ((rename_drivers(driver_1) == probs['driver_1']) and
                            (rename_drivers(driver_2) == probs['driver_2'])):
                        prob = '{:.1%}'.format(probs['probability'])
                if i < half_size:
                    row_1.append(prob)
                else:
                    row_2.append(prob)
            table_1.append(row_1)
            table_2.append(row_2)

        colalign = tuple(["left"] + ["right" for i in range(half_size)])

        result[part]['probabilities_table_1'] = tabulate(
            table_1, headers="firstrow", tablefmt="pipe", colalign=colalign)
        result[part]['probabilities_table_2'] = tabulate(
            table_2, headers="firstrow", tablefmt="pipe", colalign=colalign)

    return result


if __name__ == "__main__":
    prediction = get_prediction()
    print(prediction)
