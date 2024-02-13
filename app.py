# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 12:08:32 2024

@author: Alex
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import loguru
from datetime import datetime
import time
import requests
import csv
from pyproj import Proj, transform

MAX_RETRIES = 2

def Twd97ToWGS84(ox, oy):
    p1 = Proj(init='EPSG:3825')
    p2 = Proj(init='EPSG:4326')
    pointDest = transform(p1, p2, ox, oy)
    return pointDest


def open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 啟動無頭模式
    options.add_argument("--log-level=1")
    options.add_argument("--disable-tmp-usage")
    driver = webdriver.Chrome(options=options)
    return driver

    
def getTowns():
    loguru.logger.info('取得鄉鎮')
    driver = open_browser()
    driver.get('https://urban.kinmen.gov.tw/kmgis/map/publicMap')
    # 點擊快速定位
    driver.find_element(By.ID, 'alink').click()
    # 等待頁面完全載入
    time.sleep(2)
    # 選取定位方式為門牌定位
    Select(driver.find_element(By.ID, 'selZoomType')).select_by_visible_text('門牌定位')
    # 取得所有鄉鎮
    options = Select(driver.find_element(By.ID, 'selZoom3Town')).options
    option_values = [option.get_attribute("value").strip() for option in options if option.get_attribute("value")]
    loguru.logger.info(option_values)
    return option_values
    

def getRoads(town):
    loguru.logger.info(f'取得路 鄉鎮：{town}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(api, data={'CMD': 'GETADDRROAD', 'VAL': town})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    roads = [dist['ROAD'] for dist in json_data if dist['ROAD'] != '無']
    loguru.logger.info(roads)
    return roads


def getLanes(town, road):
    loguru.logger.info(f'取得巷 鄉鎮：{town} 門牌：{road}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(api, data={'CMD': 'GETADDRLANE', 'VAL': town, 'CODE': road})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    lanes = [dist['LANE'] for dist in json_data]
    loguru.logger.info(lanes)
    return lanes


def getAlleys(town, road, lane):
    loguru.logger.info(f'取得弄 鄉鎮：{town} 門牌：{road} 巷：{lane}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(api, data={'CMD': 'GETADDRALLEY', 'VAL': town, 'CODE': road, 'OTHER': lane})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    alleys = [dist['ALLEY'] for dist in json_data]
    loguru.logger.info(alleys)
    return alleys


def getDoors(town, road, lane, alley):
    loguru.logger.info(f'取得號 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(api, data={'CMD': 'GETADDRDOOR', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley})
    # 使用.json()方法解析JSON數據
    json_data = response.json()
    doors = [dist['NUMBER'] for dist in json_data]
    loguru.logger.info(doors)
    return doors


def getXY(town, road, lane, alley, door, retry_count=0):
    loguru.logger.info(f'取得座標 鄉鎮：{town} 門牌：{road} 巷：{lane} 弄：{alley} 號：{door}')
    # 定義POST請求的URL和payload（要發送的數據）
    # 發送POST請求
    response = requests.post(api, data={'CMD': 'GETXY', 'VAL': town, 'CODE': road, 'OTHER': lane, 'MORE': alley, 'THEN': door})
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
    api = 'https://urban.kinmen.gov.tw/kmgis/map/AcHandler.ashx'
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
                                addr = {'FULL_ADDR': dist['FULL_ADDR'], 'LATITUDE': round(xy[1], 5), 'LONGITUDE': round(xy[0], 5)}
                                writer.writerow(addr)
                                loguru.logger.info(addr)