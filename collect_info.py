from yahoo_fin.stock_info import *
import pandas as pd
import numpy as np
import logging
from datetime import date
import time



today = date.today()

logging.basicConfig(filename='log/collect-{}.log'.format(today), format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%H:%M:%S')

def convert_str_num(string):
    if (type(string) == int) | (type(string) == float) | (type(string) == np.int64) | (type(string) == np.float64):
        return float(string)
    if 'M' in string:
        num = float(string[:-1]) * 1e6
    elif 'B' in string:
        num = float(string[:-1]) * 1e9
    elif 'T' in string:
        num = float(string[:-1]) * 1e12
    elif '%' in string:
        num = float(string.replace(',', '')[:-1]) / 100
    else:
        num = float(string[:-1])
        
    return num

columns = ['Sector', 'industry', 'Market Cap', 'Enterprise Value', 'Shares Outstanding', 'PEG Ratio', 
           'Price/Book', 'Price/Sales', 'Forward P/E', 'Trailing P/E', 'Quarterly Revenue Growth', 
           'Average Dividend Yield', 'Held by Insiders', 'Held by Institutions', 'Gross Profit', 'EBITDA', 'EBIT_Q', 
           'EBIT_Y', 'Quarterly Earnings Growth', 'Total Cash', 'Diluted EPS', 'Quarterly Cash Growth', 'Cash',
           'Net Income Q', 'Net Income Y']

all_tickers_file = 'data/all_tickers.csv'
all_tickers_df = pd.read_csv(all_tickers_file)
tickers = list(all_tickers_df.Symbol.unique())
all_tickers_df.index = tickers

all_info = pd.DataFrame(np.nan, index=tickers, columns=columns)

for ticker in tickers:
    logging.info("Extracting {}".format(ticker))
    all_info.loc[ticker, 'Sector'] = all_tickers_df.loc[ticker, 'Sector']
    all_info.loc[ticker, 'industry'] = all_tickers_df.loc[ticker, 'industry']
    try:
        qsheet = get_balance_sheet(ticker, yearly=False)
        if qsheet is not None:
            if qsheet.shape[0] != 0:
                qsheet = qsheet.iloc[:,:2]
                qsheet.columns = ["Recent", "Previous"]
                # ysheet = get_balance_sheet(ticker)

                all_info.loc[ticker.upper(), 'Quarterly Cash Growth'] = (convert_str_num(qsheet.loc[qsheet.index.str.contains('cash'), 'Recent'].values[0]) - convert_str_num(qsheet.loc[qsheet.index.str.contains('cash'), 'Previous'].values[0])) / (convert_str_num(qsheet.loc[qsheet.index.str.contains('cash'), 'Previous'].values[0]))
                all_info.loc[ticker.upper(), 'Cash'] = convert_str_num(qsheet.loc[qsheet.index.str.contains('cash'), 'Recent'].values[0])
    except ValueError:
        logging.info('ValueError occurs in {}: {}'.format('get_balance_sheet', ticker))
    except IndexError:
        logging.info('IndexError occurs in {}: {}'.format('get_balance_sheet', ticker))
    except:
        logging.info('Unexpected errorin {}: {}'.format('get_balance_sheet', ticker))
    
    time.sleep(3)
    try: 
        stats_val = get_stats_valuation(ticker)
        if stats_val.shape[0] != 0:
            stats_val = stats_val.iloc[:,:2]
            stats_val.columns = ["Attribute", "Recent"]
            all_info.loc[ticker.upper(), 'Market Cap'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Market Cap'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Enterprise Value'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Enterprise Value'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'PEG Ratio'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('PEG Ratio'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Price/Book'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Price/Book'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Price/Sales'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Price/Sales'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Forward P/E'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Forward P/E'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Trailing P/E'] = convert_str_num(stats_val.loc[stats_val.Attribute.str.contains('Trailing P/E'), 'Recent'].values[0])
    except ValueError:
        logging.info('ValueError occurs in {}: {}'.format('get_stats_valuation', ticker))
    except IndexError:
        logging.info('IndexError occurs in {}: {}'.format('get_stats_valuation', ticker))
    except:
        logging.info('Unexpected errorin {}: {}'.format('get_stats_valuation', ticker))
    
    time.sleep(3)
    try:
        stats = get_stats(ticker)
        if stats.shape[0] != 0:
            stats = stats.dropna(how='all')
            all_info.loc[ticker.upper(), 'Shares Outstanding'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Shares Outstanding'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Quarterly Revenue Growth'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Quarterly Revenue Growth'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Average Dividend Yield'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Average Dividend Yield'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Held by Insiders'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Held by Insiders'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Held by Institutions'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Held by Institutions'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Gross Profit'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Gross Profit'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'EBITDA'] = convert_str_num(stats.loc[stats.Attribute.str.contains('EBITDA'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Quarterly Earnings Growth'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Quarterly Earnings Growth'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Total Cash'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Total Cash'), 'Value'].values[0])
            all_info.loc[ticker.upper(), 'Diluted EPS'] = convert_str_num(stats.loc[stats.Attribute.str.contains('Diluted EPS'), 'Value'].values[0])
    except ValueError:
        logging.info('ValueError occurs in {}: {}'.format('get_stats', ticker))
    except IndexError:
        logging.info('IndexError occurs in {}: {}'.format('get_stats', ticker))
    except:
        logging.info('Unexpected errorin {}: {}'.format('get_stats', ticker))
    
    time.sleep(3)
    try:
        instate_q = get_income_statement(ticker, yearly=False)
        if instate_q.shape[0] != 0:
            instate_q = instate_q.iloc[:, :1]
            instate_q.columns = ['Recent']
            all_info.loc[ticker.upper(), 'EBIT_Q'] = convert_str_num(instate_q.loc[instate_q.index.str.contains('ebit'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Net Income Q'] = convert_str_num(instate_q.loc[instate_q.index.str.contains('netIncome'), 'Recent'].values[0])
    except ValueError:
        logging.info('ValueError occurs in {}: {}'.format('get_income_statement, quarterly', ticker))
    except IndexError:
        logging.info('IndexError occurs in {}: {}'.format('get_income_statement, quarterly', ticker))
    except:
        logging.info('Unexpected errorin {}: {}'.format('get_income_statement, quarterly', ticker))
    
    time.sleep(3)
    try:
        instate_y = get_income_statement(ticker)
        if instate_y.shape[0] != 0:
            instate_y = instate_y.iloc[:, :1]
            instate_y.columns = ['Recent']
            all_info.loc[ticker.upper(), 'EBIT_Y'] = convert_str_num(instate_y.loc[instate_y.index.str.contains('ebit'), 'Recent'].values[0])
            all_info.loc[ticker.upper(), 'Net Income Y'] = convert_str_num(instate_y.loc[instate_y.index.str.contains('netIncome'), 'Recent'].values[0])
    except ValueError:
        logging.info('Error occurs in {}: {}'.format('get_income_statement, yearly', ticker))
    except IndexError:
        logging.info('IndexError occurs in {}: {}'.format('get_income_statement, yearly', ticker))
    except:
        logging.info('Unexpected errorin {}: {}'.format('get_income_statement, yearly', ticker))
    
    all_info.to_csv('report/all_info_{}.csv'.format(today))
    time.sleep(3)
