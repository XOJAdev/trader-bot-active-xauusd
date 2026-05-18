from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# MT5 Akkaunt ma'lumotlari (Rasmda berilgan demo hisob)
ACCOUNT = 5049922801
PASSWORD = "U!F3TxXs"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    # MT5 ga ulanishni tekshirish
    if not mt5.initialize():
        return jsonify({"status": "offline", "error": "MT5 not connected"})
    
    account_info = mt5.account_info()
    
    # Agar boshqa hisobda turgan bo'lsa yoki umuman ulanmagan bo'lsa, avtomatik kiradi
    if account_info is None or account_info.login != ACCOUNT:
        mt5.login(ACCOUNT, password=PASSWORD)
        account_info = mt5.account_info()
        
    if account_info is None:
        return jsonify({"status": "offline", "error": "No account info"})

    # Ochiq pozitsiyalarni olish
    positions = mt5.positions_get(symbol="XAUUSD")
    pos_data = []
    if positions:
        for p in positions:
            pos_data.append({
                "ticket": p.ticket,
                "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": p.volume,
                "price_open": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit
            })

    # Bozorni tahlil qilish ma'lumotlarini o'qish
    market_data = None
    if os.path.exists("market_status.json"):
        try:
            with open("market_status.json", "r") as f:
                market_data = json.load(f)
        except Exception:
            pass

    # Tarixni olish (oxirgi 7 kun)
    date_from = datetime.now() - timedelta(days=7)
    date_to = datetime.now() + timedelta(days=1)
    history_deals = mt5.history_deals_get(date_from, date_to)
    
    hist_data = []
    if history_deals:
        deals_list = list(history_deals)
        deals_list.sort(key=lambda x: x.time, reverse=True)
        for d in deals_list:
            if d.symbol == "XAUUSD" and d.entry in (mt5.DEAL_ENTRY_IN, mt5.DEAL_ENTRY_OUT):
                if d.type not in (mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL):
                    continue
                
                deal_type_str = "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL"
                dt_str = datetime.fromtimestamp(d.time).strftime("%Y-%m-%d %H:%M:%S")
                entry_str = "Kirish (IN)" if d.entry == mt5.DEAL_ENTRY_IN else "Chiqish (OUT)"
                
                hist_data.append({
                    "ticket": d.ticket,
                    "time": dt_str,
                    "type": deal_type_str,
                    "entry": entry_str,
                    "volume": d.volume,
                    "price": d.price,
                    "profit": d.profit
                })
            if len(hist_data) >= 15:
                break

    return jsonify({
        "status": "online",
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin_free": account_info.margin_free,
        "profit": account_info.profit,
        "open_positions": pos_data,
        "market": market_data,
        "history": hist_data
    })

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    config_file = "config.json"
    default_config = {
        "BOT_ACTIVE": True,
        "AI_AUTO_RISK": False,
        "LOT": 0.01,
        "SL_ATR_MULTIPLIER": 1.5,
        "TP_ATR_MULTIPLIER": 2.5
    }
    
    if request.method == 'GET':
        if not os.path.exists(config_file):
            return jsonify(default_config)
        try:
            with open(config_file, "r") as f:
                return jsonify(json.load(f))
        except:
            return jsonify(default_config)
            
    elif request.method == 'POST':
        try:
            data = request.json
            with open(config_file, "w") as f:
                json.dump(data, f)
            return jsonify({"success": True, "message": "Sozlamalar saqlandi"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

@app.route('/api/close_all', methods=['POST'])
def close_all():
    if not mt5.initialize():
        return jsonify({"success": False, "error": "MT5 not connected"})
    
    positions = mt5.positions_get(symbol="XAUUSD")
    if not positions:
        return jsonify({"success": True, "message": "Ochiq pozitsiyalar yo'q"})
        
    closed_count = 0
    for pos in positions:
        tick = mt5.symbol_info_tick("XAUUSD")
        if not tick: continue
        
        type_dict = {
            mt5.ORDER_TYPE_BUY: mt5.ORDER_TYPE_SELL,
            mt5.ORDER_TYPE_SELL: mt5.ORDER_TYPE_BUY
        }
        price_dict = {
            mt5.ORDER_TYPE_BUY: tick.bid,
            mt5.ORDER_TYPE_SELL: tick.ask
        }
        
        request_data = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": type_dict[pos.type],
            "price": price_dict[pos.type],
            "deviation": 20,
            "magic": pos.magic,
            "comment": "Web Close All",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request_data)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            closed_count += 1
            
    return jsonify({"success": True, "message": f"{closed_count} ta pozitsiya yopildi"})

@app.route('/api/close_profitable', methods=['POST'])
def close_profitable():
    if not mt5.initialize():
        return jsonify({"success": False, "error": "MT5 not connected"})
    
    positions = mt5.positions_get(symbol="XAUUSD")
    if not positions:
        return jsonify({"success": True, "message": "Ochiq pozitsiyalar yo'q"})
        
    closed_count = 0
    for pos in positions:
        if pos.profit > 0:
            tick = mt5.symbol_info_tick("XAUUSD")
            if not tick: continue
            
            type_dict = {
                mt5.ORDER_TYPE_BUY: mt5.ORDER_TYPE_SELL,
                mt5.ORDER_TYPE_SELL: mt5.ORDER_TYPE_BUY
            }
            price_dict = {
                mt5.ORDER_TYPE_BUY: tick.bid,
                mt5.ORDER_TYPE_SELL: tick.ask
            }
            
            request_data = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": type_dict[pos.type],
                "price": price_dict[pos.type],
                "deviation": 20,
                "magic": pos.magic,
                "comment": "Web Close Profitable",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request_data)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                
    if closed_count > 0:
        return jsonify({"success": True, "message": f"{closed_count} ta daromaddagi pozitsiya yopildi"})
    else:
        return jsonify({"success": True, "message": "Foydadagi pozitsiyalar topilmadi"})

@app.route('/api/trade', methods=['POST'])
def manual_trade():
    if not mt5.initialize():
        return jsonify({"success": False, "error": "MT5 not connected"})
        
    data = request.json
    trade_type_str = data.get('type')
    lot = float(data.get('lot', 0.01))
    
    symbol = "XAUUSD"
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return jsonify({"success": False, "error": "Bozor narxi olinmadi"})
        
    sl = 0.0
    tp = 0.0
    
    config_file = "config.json"
    sl_mult = 1.5
    tp_mult = 2.5
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f)
                sl_mult = float(cfg.get("SL_ATR_MULTIPLIER", 1.5))
                tp_mult = float(cfg.get("TP_ATR_MULTIPLIER", 2.5))
    except: pass
    
    atr = 0.0
    try:
        if os.path.exists("market_status.json"):
            with open("market_status.json", "r") as f:
                ms = json.load(f)
                atr = float(ms.get("atr", 0))
    except: pass
    
    if trade_type_str == 'buy':
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        if atr > 0:
            sl = price - (atr * sl_mult)
            tp = price + (atr * tp_mult)
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        if atr > 0:
            sl = price + (atr * sl_mult)
            tp = price - (atr * tp_mult)
            
    request_data = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 999222,
        "comment": "Web Manual Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    if sl > 0: request_data['sl'] = sl
    if tp > 0: request_data['tp'] = tp
    
    result = mt5.order_send(request_data)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return jsonify({"success": False, "error": f"Xatolik: {result.retcode} - {result.comment}"})
        
    return jsonify({"success": True, "message": f"{trade_type_str.upper()} buyurtmasi ochildi!"})

if __name__ == '__main__':
    print("Web dashboard ishga tushirildi! Brauzeringizda http://127.0.0.1:5000 manzilini oching.")
    app.run(debug=True, port=5000, use_reloader=False)
