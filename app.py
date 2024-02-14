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

# 失敗重試次數
MAX_RETRIES = 2
# API網站
API = 'https://urban.kinmen.gov.tw/kmgis/map/AcHandler.ashx'
# LOG檔命名規則
LOG_PATH = f'Logs/{datetime.today().strftime("%Y%m%d")}.log'
# 保存文件名稱
CSV_FILE = 'data.csv'
# 要寫入的欄位名稱
FIELDNAMES = ['FULL_ADDR', 'LATITUDE', 'LONGITUDE']
# 保存處理位置的文件名
RESUME_FILE = 'resume.txt'


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
    response = requests.post(API, data={'CMD': 'GETADDRROAD', 'VAL': town})
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
    response = requests.post(API, data={'CMD': 'GETADDRLANE', 'VAL': town, 'CODE': road})
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
    response = requests.post(API, data={'CMD': 'GETADDRALLEY', 'VAL': town, 'CODE': road, 'OTHER': lane})
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
    response = requests.post(API, data={'CMD': 'GETADDRDOOR', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley})
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
    response = requests.post(API, data={'CMD': 'GETXY', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley, 'THEN': door})
    try:
        # 使用.json()方法解析JSON數據
        json_data = response.json()
    except Exception as e:
        loguru.logger.error(f'Error decoding JSON: {e}.')
        loguru.logger.error(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            return getXY(town, road, lane, alley, door, retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            loguru.logger.error(f'town: {town} road: {road} lane: {lane} alley: {alley} door: {door}')
            return None
    return json_data[0] if json_data else None


def check_status(response, key, retry_count, callback):
    """
    檢查請求狀態的函數

    Parameters
    ----------
    response : requests.Response
        HTTP響應對象.
    key : str
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
        arr = [dist[key] for dist in json_data]
        loguru.logger.debug(arr)
        return arr
    except Exception as e:
        loguru.logger.error(f'Error decoding JSON: {e}.')
        loguru.logger.error(f'Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.info('10秒後再試一次')
            time.sleep(10)
            # 根據回調函數的不同來調用相應的函數
            return callback(retry_count + 1)
        else:
            loguru.logger.info('已達最大重試次數，放棄嘗試')
            return ['']


def read_resume():
    """
    從 resume.csv 文件中讀取所有處理的位置

    Returns
    -------
    result : set
        包含已處理位置的集合.

    """
    resume = set()
    if os.path.exists(RESUME_FILE):
        with open(RESUME_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                resume.add(','.join(row))
    return resume


def save_resume(town, road, lane, alley, door):
    """
    將當前處理的位置保存到 resume.csv 文件中

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
        
    Returns
    -------
    None

    """
    with open(RESUME_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([town, road, lane, alley, door])


if __name__ == '__main__':
    loguru.logger.add(LOG_PATH, rotation='1 day', level='ERROR')
    loguru.logger.info('Start get coordinates')
    
    # 讀取所有已處理的位置
    processed_positions = read_resume()
    towns = getTowns()
    
    for town in towns:
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
                        
                        dist = getXY(town, road, lane, alley, door)
                        if dist:
                            xy = Twd97ToWGS84(dist['X'], dist['Y'])
                            addr = {'FULL_ADDR': dist['FULL_ADDR'], 'LATITUDE': round(xy[0], 5), 'LONGITUDE': round(xy[1], 5)}
                            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
                                writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
                                # 如果文件不存在，寫入表頭
                                if file.tell() == 0:
                                    writer.writeheader()
                                writer.writerow(addr)
                            loguru.logger.debug(addr)
                        # 保存處理位置
                        save_resume(town, road, lane, alley, door)
    loguru.logger.info('Finish')