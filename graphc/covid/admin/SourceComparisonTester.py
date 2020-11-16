from graphc.covid.admin import AuthorityData2
from graphc.covid.admin import DataEngine
import pprint
import json


def compare_cases_by_date_and_postcode():
    l0 = AuthorityData2.CasesByDateAndPostcode().records()
    l1 = DataEngine.CasesByDateAndPostcode().records()

    d0 = {}
    for item in l0:
        key = '{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'))
        d0[key] = item['Cases']

    d1 = {}
    for item in l1:
        key = '{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'))
        d1[key] = item['Cases']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, 'No Match'), 'd1': d1.get(key, 'No Match')}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\cases_by_date_and_postcode_diffs.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


def compare_cases_by_date_and_state():
    l0 = AuthorityData2.CasesByDateAndState2().records()
    l1 = DataEngine.CasesByDateAndState().records()

    d0 = {}
    for item in l0:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d0[key] = item['Cases']

    d1 = {}
    for item in l1:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d1[key] = item['Cases']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, 'No Match'), 'd1': d1.get(key, 'No Match')}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\cases_by_date_and_state.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


def compare_cases_by_date_postcode_and_source():
    l0 = AuthorityData2.CasesByDatePostcodeSource().records()
    l1 = DataEngine.CasesByDatePostcodeAndSource().records()

    d0 = {}
    for item in l0:
        key = '{}_{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'), item['LikelySource'])
        d0[key] = item['Cases']

    d1 = {}
    for item in l1:
        key = '{}_{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'), item['LikelySource'])
        d1[key] = item['Cases']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, None), 'd1': d1.get(key, None)}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\cases_by_date_postcode_and_source.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


def compare_deaths_by_date_and_state():
    l0 = AuthorityData2.DeathsByDateAndState2().records()
    l1 = DataEngine.DeathsByDateAndState().records()

    d0 = {}
    for item in l0:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d0[key] = item['Deaths']

    d1 = {}
    for item in l1:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d1[key] = item['Deaths']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, 'No Match'), 'd1': d1.get(key, 'No Match')}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\deaths_by_date_and_state.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


def compare_tests_by_date_and_state():
    l0 = AuthorityData2.TestsByDateAndState2().records()
    l1 = DataEngine.TestsByDateAndState().records()

    d0 = {}
    for item in l0:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d0[key] = item['Tests']

    d1 = {}
    for item in l1:
        key = '{}_{}'.format(item['State'], item['Date'].strftime('%Y%m%d'))
        d1[key] = item['Tests']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, 'No Match'), 'd1': d1.get(key, 'No Match')}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\tests_by_date_and_state.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


def compare_tests_by_date_and_postcode():
    l0 = AuthorityData2.TestsByDateAndPostcode().records()
    l1 = DataEngine.TestsByDateAndPostcode().records()

    d0 = {}
    for item in l0:
        key = '{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'))
        d0[key] = item['Tests']

    d1 = {}
    for item in l1:
        key = '{}_{}'.format(item['Postcode'], item['Date'].strftime('%Y%m%d'))
        d1[key] = item['Tests']

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))

    keys = list(d0.keys())
    for key in keys:
        if key in d1:
            if d0[key] == d1[key]:
                d0.pop(key)
                d1.pop(key)

    print('d0 length: {}'.format(len(d0)))
    print('d1 length: {}'.format(len(d1)))
    if d0 or d1:
        if d0:
            keys = list(d0.keys())
        else:
            keys = []

        if d1:
            keys.extend(d1.keys())

        ids = set(keys)

        results = {}
        for key in ids:
            results[key] = {'d0': d0.get(key, 'No Match'), 'd1': d1.get(key, 'No Match')}

        print('unmatched items')
        pprint.pprint(results)

        with open(r'E:\Documents2\tmp\tests_by_date_and_postcode.json', 'w') as file:
            file.write(json.dumps(results, indent=4))


compare_cases_by_date_and_postcode()
compare_cases_by_date_and_state()
compare_cases_by_date_postcode_and_source()
compare_deaths_by_date_and_state()
compare_tests_by_date_and_state()
compare_tests_by_date_and_postcode()