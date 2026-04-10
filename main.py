from flask import Flask, jsonify, request
import urllib.request, json, time
 
app = Flask(__name__)
 
def fetch_price(sym):
    sym = sym.upper().strip().replace('.NS','').replace('.BO','')
    suffixes = ['.NS', '.BO', '-SM.NS', '-SM.BO']
    src_map = {'.NS':'NSE', '.BO':'BSE', '-SM.NS':'NSE SME', '-SM.BO':'BSE SME'}
    
    for suffix in suffixes:
        ticker = sym + suffix
        # Try multiple Yahoo endpoints
        for base in ['https://query1.finance.yahoo.com', 'https://query2.finance.yahoo.com']:
            try:
                url = f'{base}/v8/finance/chart/{ticker}?interval=1d&range=1d'
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://finance.yahoo.com',
                    'Origin': 'https://finance.yahoo.com'
                })
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
                m = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                price = m.get('regularMarketPrice')
                if price:
                    prev = m.get('chartPreviousClose') or price
                    return {
                        'price': round(price, 2),
                        'change': round(price - prev, 2),
                        'changeP': round((price - prev) / prev * 100, 2) if prev else 0,
                        'source': src_map[suffix],
                        'ticker': ticker,
                        'time': time.strftime('%I:%M %p')
                    }
            except Exception as e:
                continue
    return None
 
def cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp
 
@app.route('/')
def index():
    return cors(jsonify({'status': 'ok'}))
 
@app.route('/health')
def health():
    return cors(jsonify({'status': 'ok'}))
 
@app.route('/prices', methods=['POST', 'OPTIONS'])
def prices():
    if request.method == 'OPTIONS':
        return cors(jsonify({}))
    body = request.get_json() or {}
    syms = [s.strip().upper() for s in body.get('symbols', []) if s.strip()]
    result = {}
    for sym in syms:
        p = fetch_price(sym)
        if p:
            result[sym] = p
        time.sleep(0.2)
    return cors(jsonify({'prices': result, 'count': len(result)}))
 
@app.route('/stock')
def stock():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return cors(jsonify({'status': 'error', 'message': 'symbol required'}))
    p = fetch_price(symbol)
    if p:
        return cors(jsonify({'status': 'success', 'data': p}))
    return cors(jsonify({'status': 'error', 'message': f'No data for {symbol}'}))
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
