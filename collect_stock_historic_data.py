from bs4 import BeautifulSoup
import urllib2
from xml.etree import ElementTree as ET

import json
import requests
import numpy as np
import datetime as dt
import pandas as pd
import logging
from os.path import join, exists
from os import makedirs
import sys
import socket
import exceptions

def fetch_fundamental(epic):
    url = 'http://shares.telegraph.co.uk/fundamentals/?epic=' + epic
    redo = True
    while(redo):
        # logging.info(epic)
        try:
            data = urllib2.urlopen(url, timeout=1).read()
            redo = False
        except urllib2.URLError as e:
            logging.info('URLError:' + e.message)
        except socket.timeout as e:
            logging.info('timeout:' + e.message)
    soup = BeautifulSoup(data, "lxml")

    table = soup.find_all('table', {'class': 'full vertical'})
    # print table[1]

    s = str(table[1])
    # print s
    n_table = ET.XML(s)
    rows = iter(n_table)
    info = dict()
    headers = [col.text for col in next(rows)]
    info[headers[0]] = headers[1]
    logging.info('Debug: ' + str(len(headers)) + ': ' + epic)
    logging.info('Debug: ' + headers[2])
    info[headers[2]] = headers[3]
    for row in rows:
        values = [col.text for col in row]
        info[values[0]] = values[1]
        info[values[2]] = values[3]

    s = str(table[0])
    n_table = ET.XML(s)
    rows = iter(n_table)
    for row in rows:
        values = [col.text for col in row]
        info[values[0]] = values[1].encode('latin-1')
        info[values[2]] = values[3]
    return info



# info = fetch_fundamental('BARC')
# for k in info.keys():
#     print "%s: %s" % (k, info[k])

def get_all_fundamental(list='ftse100.csv'):
    companys = pd.read_csv(join('data', list), sep='\t', header=0, index_col=0)
    info_col = ['Company Name',	'EPIC', 'DPS Growth (%)', 'P/E Ratio', 'Gross Gearing (%)', 'Dividend Yield (%)', 'Net Gearing (%)',
                'Price to book value', 'Share in issue (m)', 'Earning per share (p)', 'ROCE (%)', 'Market Capitalisation (m)',
                'Assets / Equity Ratio', 'Total dividends per share (p)', 'Latest Share Price (p)', 'Dividend cover (x)',
                'Debt-to-Equity Ratio', 'EPS Growth (%)', 'NAV per share (p)', 'Debt Ratio' '52 week high / low',
                'Cash / Equity Ratio', 'Sector', 'ISIN', 'Activites', 'Index']
    info_tbl = pd.DataFrame(0, index=companys.index, columns=info_col)
    for i in companys.index:
        if companys.loc[i, 'EPIC'] == 'LAD':
            continue
        info = fetch_fundamental(companys.loc[i, 'EPIC'])
        info_tbl.loc[i, 'Company Name'] = companys.loc[i, 'Company Name']
        info_tbl.loc[i, 'EPIC'] = companys.loc[i, 'EPIC']
        for k in info.keys():
            info_tbl.loc[i, k] = info[k]

    res_fn = list.split('.')[0] + '_' + str(dt.datetime.today().date()) + '.csv'
    info_tbl.to_csv(join('fundamental', res_fn), sep='\t', header=True, index=True)



def find_n_working_days_ago_from_today(nwdays):
    today_list = str(dt.datetime.today().date()).split('-')
    weeks = np.floor(nwdays / 5)
    residual_days = nwdays % 5
    months = np.floor((weeks * 7) / 30)
    residual_days += (weeks * 7) % 30
    years = np.floor(months / 12)
    residual_months = months % 12

    new_date = [int(s) for s in today_list]
    if years > 0:
        new_date[0] -= years
    if new_date[1] <= residual_months:
        new_date[0] -= 1
        new_date[1] += 12
        new_date[1] -= residual_months
    else:
        new_date[1] -= residual_months

    days = residual_days
    if new_date[2] <= days:
        if new_date[1] == 1:
            new_date[0] -= 1
            new_date[1] = 12
        else:
            new_date[1] -= 1
        new_date[2] = new_date[2] + 30 - days
    else:
        new_date[2] -= days

    start = dt.date(int(today_list[0]), int(today_list[1]), int(today_list[2]))
    new_date = [int(s) for s in new_date]
    end = dt.date(int(new_date[0]), int(new_date[1]), int(new_date[2]))
    pred_wdays = np.busday_count(end, start)
    if pred_wdays == nwdays:
        return '-'.join([str(d) for d in new_date])
    else:
        delta = nwdays - pred_wdays
        if (new_date[2] - delta) < 0:
            if new_date[1] == 1:
                new_date[0] -= 1
                new_date[1] = 12
            else:
                new_date[1] -= 1
            new_date[2] = new_date[2] + 30 - delta
        else:
            new_date[2] += delta
        return '-'.join([str(d) for d in new_date])


def get_close_price(symbol='%27BARC.L%27', startDate='%272012-09-11%27', endDate='%272013-02-11%27'):
    query = 'http://query.yahooapis.com/v1/public/yql?q=select+*+from+yahoo.finance.historicaldata+where+'
    query += 'symbol+=+' + symbol + '+and+'
    query += 'startDate+=+' + startDate + '+and+'
    query += 'endDate+=+' + endDate
    query += '&format=json&diagnostics=true&env=store://datatables.org/alltableswithkeys'

    redo = True
    while(redo):
        try:
            r = requests.get(query)
            data = json.loads(r.text)
            redo = False
        except exceptions.ValueError as e:
            logging.info('ValueError:' + e.message)
        except requests.exceptions.ConnectionError as e:
            logging.info('requests.exceptions.ConnectionError')
    # r = requests.get(query)
    # data = json.loads(r.text)

    close_price = []
    volumns = []
    if data['query']['results'] is None:
        return None, None
    if type(data['query']['results']['quote']) is dict:
        close_price.append(data['query']['results']['quote']['Adj_Close'])
        volumns.append(data['query']['results']['quote']['Volume'])
    else:
        for k in data['query']['results']['quote']:
            close_price.append(k['Adj_Close'])
            volumns.append(k['Volume'])
    return close_price, volumns

# get_close_price('"AUTO.L"', '"2016-5-21"', '"2016-10-14"')
# get two N working days average price for current day and the day before
def get_n_days_average_price(symbol, n_days):
    endDate = str(dt.datetime.today().date())
    if len(endDate) != 10:
        tmp = endDate.split('-')
        if len(tmp[1]) != 2:
            tmp[1] = '0' + tmp[1]
        if len(tmp[2]) != 2:
            tmp[2] = '0' + tmp[2]
        endDate = tmp[0] + '-' + tmp[1] + '-' + tmp[2]
    endDate = '%27' + endDate + '%27'
    startDate = find_n_working_days_ago_from_today(n_days+1)
    if len(startDate) != 10:
        tmp = startDate.split('-')
        if len(tmp[1]) != 2:
            tmp[1] = '0' + tmp[1]
        if len(tmp[2]) != 2:
            tmp[2] = '0' + tmp[2]
        startDate = tmp[0] + '-' + tmp[1] + '-' + tmp[2]
    startDate = '%27' + startDate + '%27'
    tmp_cp, tmp_vol = get_close_price(symbol, startDate, endDate)
    if tmp_cp is None:
        return None
    cprice = [float(s) for s in tmp_cp]
    vol = [int(s) for s in tmp_vol]
    return [cprice[0], np.mean(cprice[0:n_days]), cprice[1], np.mean(cprice[1:n_days+1]), vol]

# get_n_days_average_price('"BARC.L"', 100)

def select_stocks(list='ftse100.csv' ):
    # ftse_symbols = 'ftse100.csv'
    companys = pd.read_csv(join('data', list), sep='\t', header=0, index_col=0)
    selected_1 = []
    selected_2 = []
    selected_3 = []
    selected_4 = []
    selected_5 = []
    for s in companys.index:
        symbol = '%27' + s + '%27'
        tmp = get_n_days_average_price(symbol, 100)
        if tmp is None:
            logging.info('Symbol: %s\tCompany: %s\tNONE' % (s, companys.loc[s, 'Company Name']))
        else:
            logging.info('Symbol: %s\tCompany: %s\tToday:\t%f\tAvr_T:\t%f\tYesterday:%f\tAvr_Y:\t%f' %
                         (s, companys.loc[s, 'Company Name'], tmp[0], tmp[1], tmp[2], tmp[3]))
            if (tmp[0] > tmp[1]) & (tmp[2] < tmp[3]):
                selected_1.append([s, companys.loc[s, 'Company Name']])
            if ((np.abs(tmp[0]-tmp[1])/tmp[0]) < 0.02) & (tmp[1] > tmp[3]):
                selected_2.append([s, companys.loc[s, 'Company Name']])
            if ((np.abs(tmp[0] - tmp[1]) / tmp[0]) < 0.02) & (tmp[1] <= tmp[3]):
                selected_3.append([s, companys.loc[s, 'Company Name']])
            volumns = tmp[4]
            if (volumns[0] > np.median(volumns[1:7]) * 3):
                selected_4.append([s, companys.loc[s, 'Company Name']])
            if (volumns[0] < np.median(volumns[1:21]) / 3):
                selected_5.append([s, companys.loc[s, 'Company Name']])
    return selected_1, selected_2, selected_3, selected_4, selected_5

# select_stocks()
def refine_ftse350():
    ftse100_symbols = 'ftse100.csv'
    ftse350_symbols = 'ftse350_2.csv'

    companys_100 = pd.read_csv(ftse100_symbols, sep='\t', header=0, index_col=0)
    companys_350 = pd.read_csv(ftse350_symbols, sep='\t', header=0, index_col=0)

    symbols = []
    for i in companys_350.index:
        tmp = i.split('.')
        if len(tmp) == 1:
            symbols.append(tmp[0] + '.L')
        else:
            if tmp[1] == '':
                symbols.append(tmp[0] + '.L')
            else:
                symbols.append(tmp[0] + '-' + tmp[1] + '.L')
    companys_350.index = symbols
    out_100 = [p for p in companys_350.index if p not in companys_100.index]
    out_100_companys = companys_350.loc[out_100, :]
    out_100_companys.to_csv('ftse_350_without_100.csv', sep='\t', header=True, index=True)


def main():
    '''
    This is the main process, which will be run daily base. The purpose is to find some companies that may be in the
    good position for buying. There are few rules to find these companies.
    Once the companies are found, the fundamental of them will be saved in the report.
    '''

    log_file  = 'log/StockCallection_' + str(dt.datetime.today().date()) + '.log'
    logging.basicConfig(filename=log_file, format='%(asctime)s %(message)s', level=logging.INFO)
    # The first part, the fundamental of all FTSE 350 companies will be saved in local, if them are not found
    logging.info('Dowloading Fundamental! ')
    if not exists(join('fundamental', 'ftse100_' + str(dt.datetime.today().date()) + '.csv')):
        get_all_fundamental(list='ftse100.csv')
    if not exists(join('fundamental', 'ftse350_' + str(dt.datetime.today().date()) + '.csv')):
        get_all_fundamental(list='ftse350.csv')
    logging.info('Fundamental has bee downloaded! ')

    # check if the report exists
    report_dir = 'report/' + str(dt.datetime.today().date())
    if exists(report_dir):
        print 'Today''s report already exists, please find it in folder %s' % report_dir
        sys.exit()
    makedirs(report_dir)

    selected_1_100, selected_2_100, selected_3_100, selected_4_100, selected_5_100 = select_stocks('ftse100.csv')

    # Creating the report for today
    logging.info('Creating report for today! ')
    f_100 = pd.read_csv(join('fundamental', 'ftse100_' + str(dt.datetime.today().date()) + '.csv'),
                        sep='\t', header=0, index_col=0)

    selected_1_100_i = [s[0] for s in selected_1_100]
    selected_2_100_i = [s[0] for s in selected_2_100]
    selected_3_100_i = [s[0] for s in selected_3_100]
    selected_4_100_i = [s[0] for s in selected_4_100]
    selected_5_100_i = [s[0] for s in selected_5_100]

    f_100_s1 = f_100.loc[selected_1_100_i, :]
    f_100_s2 = f_100.loc[selected_2_100_i, :]
    f_100_s3 = f_100.loc[selected_3_100_i, :]
    f_100_s4 = f_100.loc[selected_4_100_i, :]
    f_100_s5 = f_100.loc[selected_5_100_i, :]

    f_100_s1.to_csv(join(report_dir, 'Selected_1_FTSE_100_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_100_s2.to_csv(join(report_dir, 'Selected_2_FTSE_100_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_100_s3.to_csv(join(report_dir, 'Selected_3_FTSE_100_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_100_s4.to_csv(join(report_dir, 'Selected_4_FTSE_100_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_100_s5.to_csv(join(report_dir, 'Selected_5_FTSE_100_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)

    selected_1_350, selected_2_350, selected_3_350, selected_4_350, selected_5_350 = select_stocks('ftse350.csv')
    selected_1 = selected_1_100
    selected_1.extend(selected_1_350)
    selected_2 = selected_2_100
    selected_2.extend(selected_2_350)
    selected_3 = selected_3_100
    selected_3.extend(selected_3_350)
    selected_4 = selected_4_100
    selected_4.extend(selected_4_350)
    selected_5 = selected_5_100
    selected_5.extend(selected_5_350)

    logging.info('Searching is done!')
    if len(selected_1) == 0:
        logging.info('No stock found in Criteria 1!')
    else:
        for s in selected_1:
            logging.info('Selected 1: Symbol: %s\tCompany: %s' % (s[0], s[1]))
    if len(selected_2) == 0:
        logging.info('No stock found in Criteria 2!')
    else:
        for s in selected_2:
            logging.info('Selected 2: Symbol: %s\tCompany: %s' % (s[0], s[1]))
    if len(selected_3) == 0:
        logging.info('No stock found in Criteria 3!')
    else:
        for s in selected_3:
            logging.info('Selected 3: Symbol: %s\tCompany: %s' % (s[0], s[1]))
    if len(selected_4) == 0:
        logging.info('No stock found in Criteria 4!')
    else:
        for s in selected_4:
            logging.info('Selected 4: Symbol: %s\tCompany: %s' % (s[0], s[1]))
    if len(selected_5) == 0:
        logging.info('No stock found in Criteria 5!')
    else:
        for s in selected_5:
            logging.info('Selected 5: Symbol: %s\tCompany: %s' % (s[0], s[1]))

    f_350 = pd.read_csv(join('fundamental', 'ftse350_' + str(dt.datetime.today().date()) + '.csv'),
                        sep='\t', header=0, index_col=0)

    selected_1_350_i = [s[0] for s in selected_1_350]
    selected_2_350_i = [s[0] for s in selected_2_350]
    selected_3_350_i = [s[0] for s in selected_3_350]
    selected_4_350_i = [s[0] for s in selected_4_350]
    selected_5_350_i = [s[0] for s in selected_5_350]

    f_350_s1 = f_350.loc[selected_1_350_i, :]
    f_350_s2 = f_350.loc[selected_2_350_i, :]
    f_350_s3 = f_350.loc[selected_3_350_i, :]
    f_350_s4 = f_350.loc[selected_4_350_i, :]
    f_350_s5 = f_350.loc[selected_5_350_i, :]

    f_350_s1.to_csv(join(report_dir, 'Selected_1_FTSE_350_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_350_s2.to_csv(join(report_dir, 'Selected_2_FTSE_350_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_350_s3.to_csv(join(report_dir, 'Selected_3_FTSE_350_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_350_s4.to_csv(join(report_dir, 'Selected_4_FTSE_350_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    f_350_s5.to_csv(join(report_dir, 'Selected_5_FTSE_350_' + str(dt.datetime.today().date()) + '.csv'),
                    sep='\t', header=True, index=True)
    logging.info('Report is ready! ')


def calc_sector_average(year='2016'):
    fundamental_file = 'ftse_100_250_' + year + '.csv'
    fund_data = pd.read_csv(join('fundamental', fundamental_file), sep='\t', header=0, index_col=0)
    all_sectors = list(set(list(fund_data.loc[:, 'Sector'])))
    columns = ['Ave ROCE (%)']
    aver_sector = pd.DataFrame(0, index=all_sectors, columns=columns)
    for s in all_sectors:
        # eps = [float(v) for v in fund_data.loc[fund_data.loc[:, 'Sector'] == s,
        #                                        'Earning per share (p)'].values if v != 'n/a']
        # aver_sector.loc[s, 'Ave EPS (p)'] = np.mean(eps)
        # if s == 'Media':
        #     a = 0
        roce = [float(v) for v in fund_data.loc[fund_data.loc[:, 'Sector'] == s, 'ROCE (%)'].values if v != 'n/a']
        aver_sector.loc[s, 'Ave ROCE (%)'] = np.median(roce)
    aver_sector.to_csv(join('sectors', 'Sector_Average_' + year + '.csv'), sep='\t', header=True, index=True)

# l = ['ADM.L', 'ALM.L', 'EMG.L', 'IGG.L', 'INCH.L', 'TALK.L', 'TCG.L', 'WMH.L']
# f_350 = pd.read_csv(join('fundamental', 'ftse350_2_' + str(dt.datetime.today().date()) + '.csv'),
#                     sep='\t', header=0, index_col=0)
# f_350_s1 = f_350.loc[l, :]
# selected_1_100, selected_2_100, selected_3_100 = select_stocks('ftse100.csv')
# selected_1_100_i = [s[0] for s in selected_1_100]
# f_100 = pd.read_csv(join('fundamental', 'ftse100_2_' + str(dt.datetime.today().date()) + '.csv'),
#                     sep='\t', header=0, index_col=0)
# f_100_s1 = f_100.loc[selected_1_100_i, :]
# log_file  = 'log/StockCallection_' + str(dt.datetime.today().date()) + '.log'
# logging.basicConfig(filename=log_file, format='%(asctime)s %(message)s', level=logging.INFO)
# get_all_fundamental(list='ftse350_2.csv')
# fetch_fundamental('NBLS')

# calc_sector_average()
# refine_ftse350()

def get_google_data(symbol, period, window):
    url_root = 'http://www.google.com/finance/getprices?i='
    url_root += str(period) + '&p=' + str(window)
    url_root += 'd&f=d,o,h,l,c,v&df=cpct&q=' + symbol
    response = urllib2.urlopen(url_root)
    data = response.read().split('\n')
    #actual data starts at index = 7
    #first line contains full timestamp,
    #every other line is offset of period from timestamp
    parsed_data = []
    anchor_stamp = ''
    end = len(data)
    for i in range(7, end):
        cdata = data[i].split(',')
        if 'a' in cdata[0]:
            #first one record anchor timestamp
            anchor_stamp = cdata[0].replace('a', '')
            cts = int(anchor_stamp)
        else:
            try:
                coffset = int(cdata[0])
                cts = int(anchor_stamp) + (coffset * period)
                parsed_data.append((dt.datetime.fromtimestamp(float(cts)), float(cdata[1]), float(cdata[2]),
                                    float(cdata[3]), float(cdata[4]), float(cdata[5])))
            except:
                pass # for time zone offsets thrown into data
    df = pd.DataFrame(parsed_data)
    df.columns = ['ts', 'o', 'h', 'l', 'c', 'v']
    df.index = df.ts
    del df['ts']
    return df

if __name__ == "__main__":
    # main()
    df = get_google_data("BARC.L",  60, 1)
    print df
