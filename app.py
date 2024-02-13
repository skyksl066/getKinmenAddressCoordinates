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

MAX_RETRIES = 2
API = 'https://urban.kinmen.gov.tw/kmgis/map/AcHandler.ashx'

# 定義TWD97轉換為WGS84座標系統的函數
def Twd97ToWGS84(ox, oy):
    p1 = Proj('EPSG:3825')
    p2 = Proj('EPSG:4326')
    transformer = Transformer.from_proj(p1, p2)
    pointDest = transformer.transform(ox, oy)
    return pointDest


# 取得鄉鎮名稱的函數
def getTowns():
    loguru.logger.info('取得鄉鎮')
    response = requests.get('https://urban.kinmen.gov.tw/kmgis/map/publicMap')
    # 使用Beautiful Soup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    # 找到指定ID的select元素
    select_element = soup.find('select', id='selZoom3Town')
    options = select_element.find_all('option')
    towns = [option.get('value') for option in options if option.get('value')]
    loguru.logger.info(towns)
    return towns
    

# 取得道路名稱的函數
def getRoads(town):
    loguru.logger.info(f'取得路 鄉鎮：{town}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(API, data={'CMD': 'GETADDRROAD', 'VAL': town})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    roads = [dist['ROAD'] for dist in json_data if dist['ROAD'] != '無']
    loguru.logger.info(roads)
    return roads


# 取得巷名稱的函數
def getLanes(town, road):
    loguru.logger.info(f'取得巷 鄉鎮：{town} 門牌：{road}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(API, data={'CMD': 'GETADDRLANE', 'VAL': town, 'CODE': road})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    lanes = [dist['LANE'] for dist in json_data]
    loguru.logger.info(lanes)
    return lanes


# 取得弄名稱的函數
def getAlleys(town, road, lane):
    loguru.logger.info(f'取得弄 鄉鎮：{town} 門牌：{road} 巷：{lane}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(API, data={'CMD': 'GETADDRALLEY', 'VAL': town, 'CODE': road, 'OTHER': lane})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    alleys = [dist['ALLEY'] for dist in json_data]
    loguru.logger.info(alleys)
    return alleys


# 取得號碼的函數
def getDoors(town, road, lane, alley):
    loguru.logger.info(f'取得號 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(API, data={'CMD': 'GETADDRDOOR', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    doors = [dist['NUMBER'] for dist in json_data]
    loguru.logger.info(doors)
    return doors


# 取得座標的函數
def getXY(town, road, lane, alley, door, retry_count=0):
    loguru.logger.info(f'取得座標 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley} 號：{door}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(API, data={'CMD': 'GETXY', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley, 'THEN': door})
    # 使用.json()方法解析JSON數據
    try:
        json_data = response.json()
    except Exception as e:
        loguru.logger.error(f'Error decoding JSON: {e}. Response text: {response.text}')
        if retry_count < MAX_RETRIES:
            loguru.logger.error('10秒後再試一次')
            time.sleep(10)
            return getXY(town, road, lane, alley, door, retry_count + 1)
        else:
            loguru.logger.error('已達最大重試次數，放棄嘗試')
            return None
    return json_data[0]


if __name__ == '__main__':
    log_path = f'Logs/{datetime.today().strftime("%Y%m%d")}.log'
    loguru.logger.add(log_path, rotation='1 day', level='ERROR')
    loguru.logger.info('Start get coordinates')
    towns = getTowns()
    # 寫入CSV檔案
    # 指定CSV檔案的名稱
    csv_file = 'data.csv'
    # 要寫入的欄位名稱
    fieldnames = ['FULL_ADDR', 'LATITUDE', 'LONGITUDE']  
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for town in towns:
            roads = getRoads(town)
            for road in roads:
                lanes = getLanes(town, road)
                for lane in lanes:
                    alleys = getAlleys(town, road, lane)
                    for alley in alleys:
                        doors = getDoors(town, road, lane, alley)
                        for door in doors:
                            dist = getXY(town, road, lane, alley, door)
                            if dist:
                                xy = Twd97ToWGS84(dist['X'], dist['Y'])
                                addr = {'FULL_ADDR': dist['FULL_ADDR'], 'LATITUDE': round(xy[0], 5), 'LONGITUDE': round(xy[1], 5)}
                                writer.writerow(addr)
                                loguru.logger.info(addr)