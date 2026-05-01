import time
import requests
import pandas as pd
import pandas_ta as ta
import ccxt
import uuid

# ==========================================
# 1. CONFIGURATION
# ==========================================
REXALGO_WEBHOOK_URL = "https://rexalgo-production.up.railway.app/api/webhooks/strategy/3aa4f390-6692-40a1-a88e-c85a56eaa342?secret=whsec_0163a759fd3191b13d52de1930747eacd1ebe02ddea00b921b6c644e0fb21163"

CCXT_SYMBOL = "BTC/USDT"
REXALGO_SYMBOL = "BTCUSDT"
TIMEFRAME = "5m"

# ==========================================
# 2. STRATEGY LOGIC (5M RSI HIGH WIN-RATE SCALPING)
# ==========================================
def fetch_data(symbol, timeframe, limit=100):
      """Fetches the latest OHLCV data from Binance."""
      exchange = ccxt.binance()
      ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
      df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
      df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
      df.set_index('timestamp', inplace=True)
      return df

def get_latest_signal(df):
      """Calculates RSI and returns 'open', 'close', or None."""

    df['rsi'] = ta.rsi(df['close'], length=14)

    # We look at the last closed candle
    prev = df.iloc[-2]

    if pd.isna(prev['rsi']):
              return None

    # LONG ENTRY CONDITIONS
    # Entry: Extreme oversold on 5m chart
    if prev['rsi'] < 30:
              return "open"

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
      print("Starting Pro RSI Scalp Sender...")
    try:
              df = fetch_data(CCXT_SYMBOL, TIMEFRAME)
              signal = get_latest_signal(df)
              latest_price = df.iloc[-2]['close']

        if signal:
                      print(f"SIGNAL DETECTED: {signal} at ${latest_price}")
                      send_webhook_to_rexalgo(signal, "LONG", REXALGO_SYMBOL, latest_price)
else:
            print("No new signal detected on the last closed candle.")

            # --- UNCOMMENT TO FORCE A TEST SIGNAL ---
            # send_webhook_to_rexalgo("open", "LONG", REXALGO_SYMBOL, latest_price)
except Exception as e:
        print(f"An error occurred: {e}")
