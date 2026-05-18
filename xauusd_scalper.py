import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime

# ==========================================
# SOZLAMALAR (SETTINGS)
# ==========================================
# MT5 Akkaunt ma'lumotlari (Rasmda berilgan demo hisob)
ACCOUNT = 5049922801
PASSWORD = "U!F3TxXs"
# SERVER = "Sizning-Server-Nomingiz"

SYMBOL = "XAUUSD" # Oltin belgisi.
TIMEFRAME = mt5.TIMEFRAME_M5

# Indikator parametrlari
EMA_FAST_PERIOD = 20
EMA_SLOW_PERIOD = 50
ATR_PERIOD = 14

def get_config():
    default_config = {
        "BOT_ACTIVE": True,
        "AI_AUTO_RISK": False,
        "LOT": 0.01,
        "SL_ATR_MULTIPLIER": 1.5,
        "TP_ATR_MULTIPLIER": 2.5
    }
    if not os.path.exists("config.json"):
        try:
            with open("config.json", "w") as f:
                json.dump(default_config, f)
        except: pass
        return default_config
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return default_config

# ==========================================
# FUNKSIYALAR
# ==========================================

def get_data(symbol, timeframe, n_candles=300):
    """Oxirgi sham ma'lumotlarini olish"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
    if rates is None:
        print(f"[{datetime.now()}] Ma'lumot olib bo'lmadi: {mt5.last_error()}")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_indicators(df):
    """Yangi Active XAUUSD indikatorlari"""
    # EMA 20 va 50
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # ATR (14)
    prev_close = df['close'].shift(1)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - prev_close).abs()
    tr3 = (df['low'] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR_14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    
    # ADX (14)
    up = df['high'] - df['high'].shift(1)
    down = df['low'].shift(1) - df['low']
    
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    
    # Wilder's Smoothing qulayligi uchun EMA(alpha=1/14) ishlatamiz
    plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/14, adjust=False).mean() / df['ATR_14'])
    minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/14, adjust=False).mean() / df['ATR_14'])
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1))
    df['ADX_14'] = dx.ewm(alpha=1/14, adjust=False).mean()
    
    # RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # Breakout (Highest High / Lowest Low oxirgi 5 sham)
    df['HH_5'] = df['high'].rolling(window=5).max()
    df['LL_5'] = df['low'].rolling(window=5).min()
    
    return df

def check_open_positions(symbol):
    """Ushbu simvol bo'yicha ochiq pozitsiyalar borligini tekshirish"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return False
    return len(positions) > 0

def place_order(symbol, order_type, price, sl, tp, lot):
    """Buyurtma (order) ochish"""
    action = mt5.TRADE_ACTION_DEAL
    
    if order_type == mt5.ORDER_TYPE_BUY:
        type_str = "BUY"
    else:
        type_str = "SELL"
        
    request = {
        "action": action,
        "symbol": symbol,
        "volume": float(lot),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 999111,
        "comment": "XAUUSD ATR Scalper",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[{datetime.now()}] Xato, {type_str} ochilmadi: {result.retcode} - {result.comment}")
        return False
    
    print(f"[{datetime.now()}] Muvaffaqiyatli {type_str} ochildi! Narx: {price}, SL: {sl}, TP: {tp}")
    return True

# ==========================================
# ASOSIY SIKL (MAIN LOOP)
# ==========================================
def main():
    print("=======================================")
    print("XAUUSD (Oltin) Scalping Bot ishga tushirildi...")
    print("=======================================")
    
    # MT5 ga ulanish
    if not mt5.initialize():
        print(f"MT5 ga ulanib bo'lmadi, xato: {mt5.last_error()}")
        return
    
    account_info = mt5.account_info()
    if account_info is not None and account_info.login == ACCOUNT:
        print(f"Demo hisobga ({ACCOUNT}) allaqachon ulanilgan!")
    else:
        authorized = mt5.login(ACCOUNT, password=PASSWORD)
        if authorized:
            print(f"Demo hisobga ({ACCOUNT}) muvaffaqiyatli ulandi!")
        else:
            print(f"\n[DIQQAT] {ACCOUNT} hisobiga avtomatik ulanish imkonsiz: {mt5.last_error()}")
            print("-> Sababi: Server nomi noma'lum.")
            print("-> Yechim: O'zingiz MetaTrader 5 dasturiga kirib, login, parol va serverni tanlab kiring.")
            
            if account_info is not None:
                print(f"-> Bot hozir MT5 da ochiq turgan ({account_info.login}) hisobidan foydalanishda davom etadi!\n")
            else:
                print("MT5 da hech qanday hisob ochiq emas. Dasturni to'xtatyapman.")
                mt5.shutdown()
                return
    
    # Simvolni tekshirish
    if not mt5.symbol_select(SYMBOL, True):
        print(f"'{SYMBOL}' simvoli topilmadi. Uni 'Market Watch' bo'limiga qo'shing.")
        mt5.shutdown()
        return

    last_trade_time = 0

    while True:
        try:
            # 1. Ochiq pozitsiya borligini tekshirish
            if check_open_positions(SYMBOL):
                print(f"[{datetime.now()}] {SYMBOL} bo'yicha ochiq pozitsiya mavjud. Kutish rejimi...")
                time.sleep(60)
                continue
            
            # Konfiguratsiyani yuklash (veb paneldan o'zgargan bo'lsa yangilanadi)
            config = get_config()
            BOT_ACTIVE = config.get("BOT_ACTIVE", True)
            AI_AUTO_RISK = config.get("AI_AUTO_RISK", False)
            LOT = float(config.get("LOT", 0.01))
            SL_ATR_MULTIPLIER = float(config.get("SL_ATR_MULTIPLIER", 1.5))
            TP_ATR_MULTIPLIER = float(config.get("TP_ATR_MULTIPLIER", 2.5))
            
            if not BOT_ACTIVE:
                # Agar bot o'chirilgan bo'lsa, hech narsa qilmaymiz
                time.sleep(10)
                continue
            
            # 2. Ma'lumotlarni yuklab olish
            df = get_data(SYMBOL, TIMEFRAME)
            if df is None:
                time.sleep(10)
                continue
                
            # 3. Indikatorlarni hisoblash
            df = calculate_indicators(df)
            
            # Oxirgi yopilgan sham (index -2) va undan oldingi shamlar (breakout uchun)
            last_closed = df.iloc[-2]
            prev_closed = df.iloc[-3]
            
            price_close = last_closed['close']
            
            ema20 = last_closed['EMA_20']
            ema50 = last_closed['EMA_50']
            atr = last_closed['ATR_14']
            adx = last_closed['ADX_14']
            rsi = last_closed['RSI_14']
            
            # Pine Scriptdagi breakout logikasi: close > hh[1]
            hh_prev = prev_closed['HH_5'] # o'tgan shamgacha bo'lgan eng baland narx
            ll_prev = prev_closed['LL_5'] # o'tgan shamgacha bo'lgan eng past narx
            
            # Bozordagi hozirgi narxlar
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick is None:
                time.sleep(10)
                continue
                
            ask = tick.ask
            bid = tick.bid
            
            # ==========================================
            # STRATEGIYA LOGIKASI (PINE SCRIPT asosida)
            # ==========================================
            # 1. Trend
            trend_up = price_close > ema20 and ema20 > ema50
            trend_down = price_close < ema20 and ema20 < ema50
            
            # 2. ADX (Strong trend)
            strong_trend = adx > 15
            
            # 3. Session
            hour = datetime.now().hour
            session_ok = (5 <= hour <= 19)
            
            # 4. Breakout
            long_breakout = price_close > hh_prev
            short_breakout = price_close < ll_prev
            
            # 5. RSI filter
            long_signal = long_breakout and rsi > 51
            short_signal = short_breakout and rsi < 49
            
            # 6. Final Signal
            long_entry = long_signal and trend_up and strong_trend and session_ok
            short_entry = short_signal and trend_down and strong_trend and session_ok
            
            # 7. AI Signal Bahosi (0 dan 10 gacha ball)
            buy_score_val = 0
            if trend_up: buy_score_val += 3
            if strong_trend: buy_score_val += 3
            if rsi > 51: buy_score_val += 2
            if long_breakout: buy_score_val += 2
            
            sell_score_val = 0
            if trend_down: sell_score_val += 3
            if strong_trend: sell_score_val += 3
            if rsi < 49: sell_score_val += 2
            if short_breakout: sell_score_val += 2
            
            # Dashboard uchun ma'lumotlar
            status_data = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price": price_close,
                "ask": ask,
                "bid": bid,
                "ema50": round(ema20, 2), # Veb panel EMA50 deb o'qiydi, biz 20 jo'natamiz
                "ema200": round(ema50, 2), # Veb panel EMA200 deb o'qiydi, biz 50 jo'natamiz
                "stoch_k": round(rsi, 2), # RSI ni Stoch o'rniga jo'natamiz
                "stoch_d": round(adx, 2), # ADX ni Stoch D o'rniga jo'natamiz
                "atr": round(atr, 2),
                "trend": "Up" if trend_up else "Down" if trend_down else "Neutral",
                "liquidity": f"ADX: {round(adx,1)} | RSI: {round(rsi,1)}",
                "buy_score": buy_score_val,
                "sell_score": sell_score_val
            }
            try:
                with open("market_status.json", "w") as f:
                    json.dump(status_data, f)
            except Exception:
                pass
            
            # --- RISK MANAGEMENT VA SESSION FILTER ---
            
            # 1. Session Filter: 05:00 dan 19:00 gacha
            if not session_ok:
                time.sleep(60)
                continue
                
            # 2. Overtradingni kesish: har 5 daqiqada (300 sek) ko'pi bilan 1 ta trade
            if time.time() - last_trade_time < 300:
                time.sleep(10)
                continue
                
            # 3. Daily Loss Limit (-3%)
            account_info = mt5.account_info()
            if account_info is None:
                continue
            balance = account_info.balance
            
            today_start = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
            deals = mt5.history_deals_get(today_start, datetime.now())
            daily_profit = 0
            if deals:
                for deal in deals:
                    if deal.symbol == SYMBOL:
                        daily_profit += deal.profit
            
            if daily_profit < - (balance * 0.03):
                print(f"[{datetime.now()}] Kunlik limit (-3%) ga yetildi! Zarar: {daily_profit}$. Bot to'xtatildi.")
                config["BOT_ACTIVE"] = False
                try:
                    with open("config.json", "w") as f:
                        json.dump(config, f)
                except:
                    pass
                time.sleep(60)
                continue
                
            # 4. Risk va Lot Management
            # Agar AI Auto-Risk yoqilgan bo'lsa
            if AI_AUTO_RISK:
                risk = balance * 0.01 # 1% risk per trade
                calculated_lot = risk / (atr * 100) if atr > 0 else 0.01
                calculated_lot = round(calculated_lot, 2)
                
                # Dinamik SL va TP (ADX kuchiga qarab)
                if adx > 25:
                    # Katta trend - foydani ko'proq ushlaymiz
                    SL_ATR_MULTIPLIER = 1.5
                    TP_ATR_MULTIPLIER = 3.5
                else:
                    # Kuchsizroq trend - tezroq yopamiz
                    SL_ATR_MULTIPLIER = 1.2
                    TP_ATR_MULTIPLIER = 2.0
            else:
                calculated_lot = LOT
                
            # Broker ruxsat bergan minimum/maksimum lotni tekshirish
            symbol_info = mt5.symbol_info(SYMBOL)
            if symbol_info:
                if calculated_lot < symbol_info.volume_min:
                    calculated_lot = symbol_info.volume_min
                elif calculated_lot > symbol_info.volume_max:
                    calculated_lot = symbol_info.volume_max
            
            # 4. BUY Signali
            if long_entry:
                sl = ask - (atr * SL_ATR_MULTIPLIER) # 1.5 default
                tp = ask + (atr * TP_ATR_MULTIPLIER) # 2.5 default
                print(f"[{datetime.now()}] BUY (Active Trend Breakout)! Narx: {ask}, Lot: {calculated_lot}")
                if place_order(SYMBOL, mt5.ORDER_TYPE_BUY, ask, sl, tp, calculated_lot):
                    last_trade_time = time.time()
                time.sleep(10)
                continue
                    
            # 5. SELL Signali
            elif short_entry:
                sl = bid + (atr * SL_ATR_MULTIPLIER) # 1.5 default
                tp = bid - (atr * TP_ATR_MULTIPLIER) # 2.5 default
                print(f"[{datetime.now()}] SELL (Active Trend Breakout)! Narx: {bid}, Lot: {calculated_lot}")
                if place_order(SYMBOL, mt5.ORDER_TYPE_SELL, bid, sl, tp, calculated_lot):
                    last_trade_time = time.time()
                time.sleep(10)
                continue
            
            # Keyingi tekshiruvgacha 60 soniya kutish
            # Oltin M15 da ishlayotgani uchun har daqiqada tekshirib turish yetarli
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] Xatolik yuz berdi: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
