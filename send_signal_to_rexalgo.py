import time
import requests
import pandas as pd
import pandas_ta as ta
import ccxt
import uuid

# ==========================================
# 1. CONFIGURATION
# ==========================================
REXALGO_WEBHOOK_URL = "https://rexalgo-production.up.railway.app/api/webhooks/strategy/9dd99757-83f4-4aec-932e-c5d4f7479c70?secret=whsec_fe86dcd645fa960f6b4a1417b205602db16e5735dc07ca771a15190ae598f471"

# Strategy Parameters
CCXT_SYMBOL = "BTC/USDT"
REXALGO_SYMBOL = "BTCUSDT"
TIMEFRAME = "1h"

# ==========================================
# 2. STRATEGY LOGIC (SUPERTREND 1H)
# ==========================================
def fetch_data(symbol, timeframe, limit=100):
      exchange = ccxt.binance()
      ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
      df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
      df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
      return df

def get_latest_signal(df):
      # SUPERTREND Strategy (Length 10, Multiplier 2.0)
      st = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=2.0)
      df = df.join(st)
      dir_col = 'SUPERTd_10_2.0'

    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # Supertrend flips to 1 (GREEN/UP)
    if prev[dir_col] == 1 and prev2[dir_col] == -1:
              return "open"

    # Supertrend flips to -1 (RED/DOWN)
elif prev[dir_col] == -1 and prev2[dir_col] == 1:
          return "close"

    return None

# ==========================================
# 3. WEBHOOK SENDER
# ==========================================
def send_webhook_to_rexalgo(action, side, symbol, price):
      payload = {
                "action": action,      
                "side": side,          
                "symbol": symbol,      
                "price": price,
                "trigger_type": "MARKET",
                "idempotency_key": str(uuid.uuid4())
      }
      headers = {"Content-Type": "application/json"}

    print(f"Sending {action} signal for {symbol} to RexAlgo...")
    try:
              response = requests.post(REXALGO_WEBHOOK_URL, json=payload, headers=headers)
              if response.status_code in [200, 201]:
                            print("Successfully sent test signal to RexAlgo!")
                            print("Response:", response.text)
    else:
            print(f"Failed to send signal. Status Code: {response.status_code}")
                  print("Error Details:", response.text)
except Exception as e:
        print(f"Error connecting to webhook: {e}")

# ==========================================
# 4. MAIN EXECUTION LOOP
# ==========================================
if __name__ == "__main__":
      print("Starting Pro Supertrend Sender...")
    try:
              df = fetch_data(CCXT_SYMBOL, TIMEFRAME)
              signal = get_latest_signal(df)
              latest_price = df.iloc[-2]['close']

        if signal:
                      print(f"SIGNAL DETECTED: {signal} at ${latest_price}")
                      send_webhook_to_rexalgo(signal, "LONG", REXALGO_SYMBOL, latest_price)
else:
            print("No new signal detected on the last closed candle.")
except Exception as e:
        print(f"An error occurred: {e}")
