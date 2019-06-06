import datetime
import math
import random
import time

import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from dateutil.parser import parse
from tabulate import tabulate

ERGAST_CALENDAR = 'http://ergast.com/api/f1/current.json'
PREDICTOR_URL = 'http://www.f1-predictor.com/api-next-race-prediction/'
RETRIES = 10


def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(math.floor(n/10) % 10 != 1)*(n % 10 < 4)*n % 10::4])


def rename_drivers(name):
    new_name = name.lower()
    if (new_name == 'verstappen'):
        new_name = 'max_' + new_name
    elif (new_name == 'magnussen'):
        new_name = 'kevin_' + new_name
    return new_name


def raname_race_name(name, season):
    new_name = name.replace('Grand Prix', 'GP')
    new_name += ' ' + season
    return new_name


def get_json(url):
    retries_cnt = 0
    with requests.session() as session:
        cached = CacheControl(session,
                              cache=FileCache('.webcache'))
        while retries_cnt < RETRIES:
            retries_cnt += 1
            response = cached.get(url)
            if response.status_code == 200:
                return response.json()
            time.sleep(random.randint(1, 5))
    return None


def main(output):
    calendar = get_json(ERGAST_CALENDAR)
    now = datetime.datetime.now(datetime.timezone.utc)

    # print(calendar)
    race_next = None
    for race in sorted(calendar['MRData']['RaceTable']['Races'], key=lambda x: int(x['round'])):
        race_dt = parse(race['date'] + ' ' + race['time'])
        if race_dt > now:
            race_next = race
            break
    # print(race_dt)
    # print(race_next)

    data = get_json(PREDICTOR_URL)
    if data['race_name'] != raname_race_name(race_next['raceName'], race_next['season']):
        print("Race Name Mismatch between predictor and ergast:",
              end=' ', file=output)
        print(data['race_name'], "!=", raname_race_name(
            race_next['raceName'], race_next['season']), file=output)
        return

    print("Next Race:", data['race_name'], file=output)
    print(file=output)
    for part in ['qualifying', 'race']:
        print('%s Ranking: \n' % (part.capitalize()), file=output)
        order_keys = sorted(
            list(data[part]['ranking'].keys()), key=lambda x: data[part]['ranking'][x])
        for driver in order_keys:
            print("\t%s. %s" %
                  (ordinal(data[part]['ranking'][driver]), driver), file=output)

        half_size = len(order_keys) // 2

        table_1 = []
        table_1.append(['^row ^vs ^col'] + [driver[0:3].upper()
                                            for driver in order_keys[:half_size]])
        table_2 = []
        table_2.append(['^row ^vs ^col'] + [driver[0:3].upper()
                                            for driver in order_keys[half_size:]])

        for driver_1 in order_keys:
            row_1 = [driver_1[0:3].upper()]
            row_2 = [driver_1[0:3].upper()]
            for i, driver_2 in enumerate(order_keys):
                prob = ''
                for probs in data[part]['pairwise_probabilities']:
                    if ((rename_drivers(driver_1) == probs['driver_1']) and
                            (rename_drivers(driver_2) == probs['driver_2'])):
                        prob = '{:.0%}'.format(probs['probability'])
                if i < half_size:
                    row_1.append(prob)
                else:
                    row_2.append(prob)
            table_1.append(row_1)
            table_2.append(row_2)

        colalign = tuple(["left"] + ["right" for i in range(half_size)])

        print(file=output)
        print('%s Pairwise Probabilities (Part I):\n' %
              (part.capitalize()), file=output)
        print(tabulate(table_1, headers="firstrow",
                       tablefmt="pipe", colalign=colalign), file=output)
        print('\n', file=output)
        print('%s Pairwise Probabilities (Part II):\n' %
              (part.capitalize()), file=output)
        print(tabulate(table_2, headers="firstrow",
                       tablefmt="pipe", colalign=colalign), file=output)
        print('\n', file=output)
        return


if __name__ == "__main__":
    import io
    with io.open('output.md', 'w', encoding='utf-8') as f_obj:
        main(f_obj)
