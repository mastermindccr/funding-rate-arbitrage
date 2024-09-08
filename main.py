import ccxt
import time
import signal
import sys
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

future = ccxt.binance({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

spot = ccxt.binance({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('SECRET'),
    'enableRateLimit': True
})

token = ''
threshold = 0.0

spot.load_markets()
markets = [x['symbol'] for x in spot.markets.values() if x['contract']==False and x['symbol'].endswith('USDT')]

def open_position(symbol):
    # transfer all USDT balance from future to spot
    amount = future.fetch_balance()['USDT']['free']
    if amount!=0:
        future.transfer('USDT', amount, 'future', 'spot')

    # set leverage
    future.set_leverage(3, symbol)

    # transfer half USDT balance from spot to future
    amount = spot.fetch_balance()['USDT']['free'] / 2
    spot.transfer('USDT', amount, 'spot', 'future')

    amount*=0.95
    price = future.fetch_ticker(symbol)['last']
    spot.create_market_buy_order(symbol, amount/price)
    future.create_market_sell_order(symbol, amount/price*0.999)
    print("open position: spent USDT amount: {USDT_amount}, get {symbol} amount: {symbol_amount}.".format(USDT_amount=amount, symbol=symbol.replace('/USDT', ''), symbol_amount=amount/price*0.999))
    send_message("open position: spent USDT amount: {USDT_amount}, get {symbol} amount: {symbol_amount}.".format(USDT_amount=amount, symbol=symbol.replace('/USDT', ''), symbol_amount=amount/price*0.999))

def close_position(symbol):
    _symbol = symbol.replace('/', '')
    future_amount = abs(float([x for x in future.fetch_balance()['info']['positions'] if x['symbol'] == _symbol][0]['positionAmt']))
    spot_amount = spot.fetch_balance()[symbol.split('/')[0]]['free']
    future.create_market_buy_order(symbol, future_amount, {"reduceOnly": True})
    spot.create_market_sell_order(symbol, spot_amount)
    print("close position:", symbol)
    send_message("close position: {symbol}, position closed successfully.".format(symbol=symbol))

def exit_gracefully(signum, frame):
    if token!='':
        close_position(token)
    send_message("the program exited gracefully.")
    sys.exit(1)

def start():
    global token, threshold
    while True:
        try:
            # if position is not empty
            if token!='':
                # if liquidation price is reached or funding rate is too low
                if future.fetch_ticker(token)['close']>=threshold:
                    close_position(token)
                    token = ''
                    threshold = 0
                else:
                    time.sleep(60)
                    continue

            hour = datetime.now().hour
            minute = datetime.now().minute
            # if time is 3:58, 7:58, 11:58, 15:58, 19:58, 23:58
            if hour%4==3 and minute==58:
                if future.fetch_funding_rate(token)['fundingRate']<0.0001:
                    close_position(token)
                    token = ''
                    threshold = 0
                token_name = ''
                max_funding_rate = 0
                remaining_time = 0
                for name, value in future.fetch_funding_rates().items():
                    name = name.replace(':USDT', '')
                    if name not in markets:
                        continue
                    tmp_time = int(value['info']['nextFundingTime']) - value['timestamp']
                    if tmp_time > 0:
                        if value['fundingRate'] > max_funding_rate:
                            max_funding_rate = value['fundingRate']
                            token_name = name
                            remaining_time = tmp_time/1000
                if max_funding_rate < 0.0001 or remaining_time > 120:
                    time.sleep(60)
                    continue
                print("[{hour}:{minute}] {token_name}: {funding_rate}".format(hour="%02d" % hour, minute="%02d" % minute, token_name=token_name, funding_rate=max_funding_rate))
                send_message("[{hour}:{minute}] {token_name}: {funding_rate}.".format(hour="%02d" % hour, minute="%02d" % minute, token_name=token_name, funding_rate=max_funding_rate))
                open_position(token_name)
                token = token_name

                # update token and threshold
                position = future.fetch_positions([token])[0]
                liquidation_price = float(position['info']['liquidationPrice'])
                entry_price = float(position['info']['entryPrice'])
                threshold = (liquidation_price-entry_price)*0.8 + entry_price
                print("threshold:", threshold)
                send_message("threshold: {threshold}.".format(threshold=threshold))

            time.sleep(60)
        except Exception as e:
            print(e)
            send_message(e.__str__()+'.')
            time.sleep(60)

def send_message(message):
    requests.post('https://notify-api.line.me/api/notify?',
                  params = {
                      'message': message
                      },
                  headers = {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'Authorization': f'Bearer {os.getenv("LINE_NOTIFY_TOKEN")}'
                      })

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_gracefully)
    start()
    