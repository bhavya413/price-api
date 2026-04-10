from flask import Flask, jsonify, request
import urllib.request, json, time

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_yahoo(ticker):
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        m = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
        price = m.get('regularMarketPrice')
        if price:
            prev = m.get('chartPreviousClose') or price
            return {
                'last_price': round(price, 2),
                'change': round(price - prev, 2),
                'percent_change': round((price - prev) / prev * 100, 2) if prev else 0,
                'previous_close': round(prev, 2),
            }
    except:
        pass
    return None

def get_price(symbol):
    sym = symbol.upper().strip()
    # Determine exchange from suffix
    if sym.endswith('.BO'):
        tickers = [sym, sym.replace('.BO', '.NS')]
        src = 'BSE'
    elif sym.endswith('.NS'):
        tickers = [sym, sym.replace('.NS', '.BO'), sym.replace('.NS', '-SM.NS'), sym.replace('.NS', '-SM.BO')]
        src = 'NSE'
    else:
        # Default: try NSE first then BSE then SME
        tickers = [sym + '.NS', sym + '.BO', sym + '-SM.NS', sym + '-SM.BO']
        src = 'NSE'
    
    for ticker in tickers:
        data = fetch_yahoo(ticker)
        if data:
            exchange = 'BSE' if '.BO' in ticker else ('NSE SME' if '-SM' in ticker else 'NSE')
            return {**data, 'symbol': sym.replace('.NS','').replace('.BO',''), 
                    'exchange': exchange, 'ticker': ticker}
    return None

def cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

@app.route('/')
def index():
    return cors(jsonify({'status': 'ok', 'message': 'Indian Stock Price API'}))

@app.route('/health')
def health():
    return cors(jsonify({'status': 'ok'}))

@app.route('/stock')
def stock():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return cors(jsonify({'status': 'error', 'message': 'symbol required'}))
    data = get_price(symbol)
    if data:
        return cors(jsonify({'status': 'success', 'data': data}))
    return cors(jsonify({'status': 'error', 'message': f'No data for {symbol}'}))

@app.route('/stock/list')
def stock_list():
    symbols = request.args.get('symbols', '')
    if not symbols:
        return cors(jsonify({'status': 'error', 'message': 'symbols required'}))
    syms = [s.strip() for s in symbols.split(',') if s.strip()]
    results = []
    for sym in syms:
        data = get_price(sym)
        if data:
            results.append(data)
        time.sleep(0.5)  # be nice to Yahoo
    return cors(jsonify({'status': 'success', 'count': len(results), 'stocks': results}))

@app.route('/prices', methods=['POST', 'OPTIONS'])
def prices():
    if request.method == 'OPTIONS':
        return cors(jsonify({}))
    body = request.get_json() or {}
    syms = [s.strip().upper() for s in body.get('symbols', []) if s.strip()]
    result = {}
    for sym in syms:
        data = get_price(sym)
        if data:
            result[sym] = {
                'price': data['last_price'],
                'change': data['change'],
                'changeP': data['percent_change'],
                'source': data['exchange'],
                'ticker': data['ticker']
            }
        time.sleep(0.3)
    return cors(jsonify({'prices': result, 'count': len(result)}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
