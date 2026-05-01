import pandas as pd
import pandas_ta as ta
import ccxt
import time

# Parameters
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"
CONTRACTS = 0.05 # Simulate trading 0.05 BTC per trade
DAYS_TO_FETCH = 120

def fetch_data():
      exchange = ccxt.binance()
      start_time = pd.Timestamp.now('UTC') - pd.Timedelta(days=DAYS_TO_FETCH)
      since = exchange.parse8601(start_time.isoformat())
      all_ohlcv = []

    while True:
              ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since=since, limit=1000)
              if len(ohlcv) == 0:
                            break
                        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        time.sleep(0.1) # Rate limiting
        if since >= exchange.milliseconds():
                      break

    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def generate_trades(df):
      df['rsi'] = ta.rsi(df['close'], length=14)

    in_position = False
    entry_price = 0
    trade_num = 0
    cumulative_profit = 0

    trades = []

    for i in range(20, len(df)):
              current = df.iloc[i]
        prev = df.iloc[i-1]

        # ENTRY: Extreme oversold on 5m chart
        if not in_position and prev['rsi'] < 30:
                      in_position = True
                      trade_num += 1
                      entry_price = current['open']

            date_time = df.index[i].strftime("%Y-%m-%d %H:%M")

            trades.append({
                              "Trade #": trade_num,
                              "Type": "Entry long",
                              "Date/Time": date_time,
                              "Price USDT": round(entry_price, 2),
                              "Contracts": CONTRACTS,
                              "Profit USDT": 0.00,
                              "Profit %": 0.00,
                              "Cumulative profit USDT": round(cumulative_profit, 2)
            })

elif in_position:
            exit_price = None

            # EXIT: 0.5% Tight Take Profit (High Frequency/High Win Rate)
            if current['high'] > entry_price * 1.005:
                              exit_price = entry_price * 1.005
                          # STOP LOSS: 5% Wide Stop Loss (Prevents getting wicked out)
elif current['low'] < entry_price * 0.95:
                exit_price = entry_price * 0.95

            if exit_price:
                              in_position = False
                              date_time = df.index[i].strftime("%Y-%m-%d %H:%M")

                profit_usdt = (exit_price - entry_price) * CONTRACTS
                profit_pct = (exit_price - entry_price) / entry_price * 100
                cumulative_profit += profit_usdt

                trades.append({
                                      "Trade #": trade_num,
                                      "Type": "Exit long",
                                      "Date/Time": date_time,
                                      "Price USDT": round(exit_price, 2),
                                      "Contracts": CONTRACTS,
                                      "Profit USDT": round(profit_usdt, 2),
                                      "Profit %": round(profit_pct, 2),
                                      "Cumulative profit USDT": round(cumulative_profit, 2)
                })

    return trades

if __name__ == "__main__":
      print("Generating High-Frequency Scalper backtest data...")
    df = fetch_data()
    trades = generate_trades(df)

    csv_lines = []
    csv_lines.append("Trade #,Type,Date/Time,Price USDT,Contracts,Profit USDT,Profit %,Cumulative profit USDT")

    for t in trades:
              line = f"{t['Trade #']},{t['Type']},{t['Date/Time']},{t['Price USDT']},{t['Contracts']},{t['Profit USDT']},{t['Profit %']},{t['Cumulative profit USDT']}"
        csv_lines.append(line)

    csv_output = "\n".join(csv_lines)

    with open("pro_scalp_export.csv", "w") as f:
              f.write(csv_output)

    print(f"Generated {len(trades)//2} trades over {DAYS_TO_FETCH} days!")
