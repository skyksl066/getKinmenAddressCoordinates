# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 12:08:32 2024

@author: Alex
"""

import loguru
from datetime import datetime
import time
import requests
import csv
from pyproj import Proj, Transformer
from bs4 import BeautifulSoup
import os
import threading
import json

# 失敗重試次數
MAX_RETRIES = 2
# API網站
API = 'https://urban.kinmen.gov.tw/kmgis/map/AcHandler.ashx'
# LOG檔命名規則
LOG_PATH = f'Logs/{datetime.today().strftime("%Y%m%d")}.log'
# 每次處理兩個鄉鎮
BATCH_SIZE = 2


def Twd97ToWGS84(ox, oy):
    """
    定義TWD97轉換為WGS84座標系統的函數

    Parameters
    ----------
    ox : float
        TWD97座標的X值.
    oy : float
        TWD97座標的Y值.

    Returns
    -------
    pointDest : tuple
        包含WGS84座標的元組.

    """
    p1 = Proj('EPSG:3825')
    p2 = Proj('EPSG:4326')
    transformer = Transformer.from_proj(p1, p2)
    pointDest = transformer.transform(ox, oy)
    return pointDest


def getTowns():
    """
    取得鄉鎮名稱的函數

    Returns
    -------
    towns : list
        包含鄉鎮名稱的列表.

    """
    loguru.logger.info('取得鄉鎮')
    response = requests.get('https://urban.kinmen.gov.tw/kmgis/map/publicMap')
    # 使用Beautiful Soup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    # 找到指定ID的select元素
    select_element = soup.find('select', id='selZoom3Town')
    options = select_element.find_all('option')
    towns = [option.get('value') for option in options if option.get('value')]
    loguru.logger.debug(towns)
    return towns


def searchRoads(txt='', retry_count=0):
    loguru.logger.info(f'搜尋路 查詢條件：{txt}')
    response = requests.post(API, data={'CMD': 'GETROADLIST', 'VAL': txt})
    return check_status(response, 'ROAD', retry_count, lambda count: searchRoads(txt, count))


def getMarkMainClassList(retry_count=0):
    loguru.logger.info('取得主分類')
    response = requests.post(API, data={'CMD': 'GETMARKMAINCLASSLIST'})
    return check_status(response, ['Type', 'TypeId'], retry_count, lambda count: getMarkMainClassList(count))


def getMarkSubClassList(main, retry_count=0):
    loguru.logger.info(f'取得次分類 主分類:{main}')
    response = requests.post(API, data={'CMD': 'GETMARKSUBCLASSLIST', 'VAL': main})
    return check_status(response, ['SubType', 'SubTypeId'], retry_count, lambda count: getMarkSubClassList(main, count))


def getMarkList(main, sub, retry_count=0):
    loguru.logger.info(f'取得地標 主分類:{main} 次分類:{sub}')
    response = requests.post(API, data={'CMD': 'GETMARKLIST', 'VAL': main, 'CODE': sub})
    try:
        # 使用.json()方法解析JSON數據
        json_data = response.json()
    except Exception as e:
        loguru.logger.debug(f'Error decoding JSON: {e}.')
        loguru.logger.debug(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            return getMarkList(main, sub, retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            loguru.logger.error(f'mainType: {main} subType: {sub}')
            return None
    return json_data if json_data else None


def getSubLmCode(type, retry_count=0):
    # type 1~15
    loguru.logger.info(f'取得小類 大類：{type}')
    response = requests.post(API, data={'CMD': 'GETSUBLMCODE', 'VAL': type})
    return check_status(response, 'SubType', retry_count, lambda count: getSubLmCode(type, count))


def getLandMarkList(type, subtype, retry_count=0):
    loguru.logger.info(f'取得地標 大類：{type} 小類:{subtype}')
    response = requests.post(
        API, data={'CMD': 'GETLANDMARKLIST', 'VAL': type, 'CODE': subtype})
    try:
        # 使用.json()方法解析JSON數據
        json_data = response.json()
    except Exception as e:
        loguru.logger.debug(f'Error decoding JSON: {e}.')
        loguru.logger.debug(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            return getLandMarkList(type, subtype, retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            loguru.logger.error(f'type: {type} subtype: {subtype}')
            return None
    return json_data if json_data else None


def getRoads(town, retry_count=0):
    """
    取得道路名稱的函數

    Parameters
    ----------
    town : str
        鄉鎮名稱.
    retry_count : int, optional
        失敗重試次數. The default is 0.

    Returns
    -------
    result : list
        包含道路名稱的列表.

    """
    loguru.logger.info(f'取得路 鄉鎮：{town}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = session.post(API, data={'CMD': 'GETADDRROAD', 'VAL': town})
    return check_status(response, 'ROAD', retry_count, lambda count: getRoads(town, count))


def getLanes(town, road, retry_count=0):
    """
    取得巷名稱的函數

    Parameters
    ----------
    town : str
        鄉鎮名稱.
    road : str
        道路名稱.
    retry_count : int, optional
        失敗重試次數. The default is 0.

    Returns
    -------
    result : list
        包含巷名稱的列表.

    """
    loguru.logger.info(f'取得巷 鄉鎮：{town} 門牌：{road}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = session.post(
        API, data={'CMD': 'GETADDRLANE', 'VAL': town, 'CODE': road})
    return check_status(response, 'LANE', retry_count, lambda count: getLanes(town, road, count))


def getAlleys(town, road, lane, retry_count=0):
    """
    取得弄名稱的函數

    Parameters
    ----------
    town : str
        鄉鎮名稱.
    road : str
        道路名稱.
    lane : str
        巷名稱.
    retry_count : int, optional
        失敗重試次數. The default is 0.

    Returns
    -------
    result : list
        包含弄名稱的列表.

    """
    loguru.logger.info(f'取得弄 鄉鎮：{town} 門牌：{road} 巷：{lane}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = session.post(
        API, data={'CMD': 'GETADDRALLEY', 'VAL': town, 'CODE': road, 'OTHER': lane})
    return check_status(response, 'ALLEY', retry_count, lambda count: getAlleys(town, road, lane, count))


def getDoors(town, road, lane, alley, retry_count=0):
    """
    取得號碼的函數

    Parameters
    ----------
    town : str
        鄉鎮名稱.
    road : str
        道路名稱.
    lane : str
        巷名稱.
    alley : str
        弄名稱.
    retry_count : int, optional
        失敗重試次數. The default is 0.

    Returns
    -------
    result : list
        包含號碼的列表.

    """
    loguru.logger.info(f'取得號 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = session.post(API, data={
                            'CMD': 'GETADDRDOOR', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley})
    return check_status(response, 'NUMBER', retry_count, lambda count: getDoors(town, road, lane, alley, count))


def getXY(town, road, lane, alley, door, retry_count=0):
    """
    取得座標的函數

    Parameters
    ----------
    town : str
        鄉鎮名稱.
    road : str
        道路名稱.
    lane : str
        巷名稱.
    alley : str
        弄名稱.
    door : str
        號碼.
    retry_count : int, optional
        重試次數. The default is 0.

    Returns
    -------
    result : dict or None
        包含座標信息的字典，如果失敗則返回None.

    """
    loguru.logger.info(f'取得座標 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley} 號：{door}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = session.post(API, data={
                            'CMD': 'GETXY', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley, 'THEN': door})
    try:
        # 使用.json()方法解析JSON數據
        json_data = response.json()
    except Exception as e:
        loguru.logger.debug(f'Error decoding JSON: {e}.')
        loguru.logger.debug(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            return getXY(town, road, lane, alley, door, retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            loguru.logger.error(
                f'town: {town} road: {road} lane: {lane} alley: {alley} door: {door}')
            return None
    return json_data[0] if json_data else None


def check_status(response, key, retry_count, callback):
    """
    檢查請求狀態的函數

    Parameters
    ----------
    response : requests.Response
        HTTP響應對象.
    key : str or list
        JSON數據中要提取的鍵.
    retry_count : int
        失敗重試次數.
    callback : function
        失敗時要調用的回調函數.

    Returns
    -------
    result : list
        根據鍵提取的值列表或空列表.

    """
    try:
        # 使用.json()方法解析JSON數據
        json_data = response.json()
        if type(key) == list:
            obj = {}
            for d in json_data:
                obj.update({d[key[1]]: d[key[0]]})
            loguru.logger.debug(obj)
            return obj
        else:
            arr = [obj[key] for obj in json_data]
            loguru.logger.debug(arr)
            return arr
    except Exception as e:
        loguru.logger.debug(f'Error decoding JSON: {e}.')
        loguru.logger.debug(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            # 根據回調函數的不同來調用相應的函數
            return callback(retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            return {} if type(key) == list else []


def read_data(file_name, start, end):
    """
    從文件中讀取所有處理的位置

    Parameters
    ----------
    file_name : str
        檔案名稱.
    start : int
        欄位開始位置.
    end : int
        欄位結束位置.

    Returns
    -------
    csv_file : set
        包含已處理位置的集合.

    """
    csv_file = set()
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                csv_file.add(','.join(row[start:end]))
    return csv_file


def svae_data(file_name, field_names, obj):
    """
    將當前處理的位置保存到文件中

    Parameters
    ----------
    file_name : str
        檔案名稱.
    field_names : list
        欄位名稱.
    obj : dict
        資料集.

    Returns
    -------
    None.

    """
    with open(file_name, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        # 如果文件不存在，寫入表頭
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(obj)
        loguru.logger.debug(obj)


def csv_to_json(file_name, output_name):
    loguru.logger.info(f'資料集轉成JSON input:{file_name} ouput:{output_name}')
    data = []
    with open(file_name, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            data.append(row)
    with open(rf'data/{output_name}', 'w', encoding='utf-8') as json_file:
        json.dump({"data": data}, json_file, ensure_ascii=False, indent=4)


def process_towns(town):
    roads = getRoads(town)
    for road in roads:
        lanes = getLanes(town, road)
        for lane in lanes:
            alleys = getAlleys(town, road, lane)
            for alley in alleys:
                doors = getDoors(town, road, lane, alley)
                for door in doors:
                    # 如果已處理過此位置，則跳過
                    position = ','.join([town, road, lane, alley, door])
                    if position in processed_positions:
                        loguru.logger.info(f'{door} 已下載跳過')
                        continue

                    obj = getXY(town, road, lane, alley, door)
                    if obj:
                        xy = Twd97ToWGS84(obj['X'], obj['Y'])
                        # 要寫入的欄位名稱
                        field_names = ['ADDR', 'LATITUDE', 'LONGITUDE', 'TOWN', 'ROAD', 'LANE', 'ALLEY', 'DOOR']
                        my_dict = {'ADDR': obj['FULL_ADDR'], 'LATITUDE': xy[0], 'LONGITUDE': xy[1],
                                   'TOWN': town, 'ROAD': road, 'LANE': lane, 'ALLEY': alley, 'DOOR': door}
                        svae_data('address.csv', field_names, my_dict)


if __name__ == '__main__':
    loguru.logger.add(LOG_PATH, rotation='1 day', level='ERROR')
    loguru.logger.info('Start get coordinates')
    session = requests.Session()
    # 讀取所有已處理的位置
    processed_positions = read_data('address.csv', 3, 8)
    towns = getTowns()
    for i in range(0, len(towns), BATCH_SIZE):
        batch_towns = towns[i:i + BATCH_SIZE]
        threads = []
        for town in batch_towns:
            thread = threading.Thread(target=process_towns, args=(town,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
    csv_to_json('address.csv', 'address.json')
    processed_positions = read_data('mark.csv', 3, 5)
    mains = getMarkMainClassList()
    for main in mains:
        subs = getMarkSubClassList(main)
        for sub in subs.keys():
            # 如果已處理過此位置，則跳過
            position = ','.join([mains[main], subs[sub]])
            if position in processed_positions:
                loguru.logger.info(f'main: {mains[main]} sub:{subs[sub]} 已下載跳過')
                continue
            mark_list = getMarkList(main, sub)
            if mark_list:
                for mark in mark_list:
                    xy = Twd97ToWGS84(mark['X'], mark['Y'])
                    field_names = ['NAME', 'LATITUDE', 'LONGITUDE', 'MAIN', 'SUB']
                    my_dict = {'NAME': mark['LMarkName'], 'LATITUDE': xy[0], 'LONGITUDE': xy[1],
                               'MAIN': mains[main], 'SUB': subs[sub]}
                    svae_data('mark.csv', field_names, my_dict)
    csv_to_json('mark.csv', 'mark.json')
    loguru.logger.info('Finish')
