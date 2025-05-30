# أضف في بداية الملف
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, request, jsonify
from data_fetcher import StockDataFetcher
import pandas as pd
from datetime import datetime

app = Flask(__name__)
fetcher = StockDataFetcher()

# تعريف الأسهم والمؤشرات المطلوبة
SYMBOLS = {
    'NASDAQ': '^IXIC',
    'S&P 500': '^GSPC',
    'Dow Jones': '^DJI',
    'Apple': 'AAPL',
    'Microsoft': 'MSFT',
    'Amazon': 'AMZN',
    'Google': 'GOOGL',
    'Tesla': 'TSLA',
    'Nvidia': 'NVDA',
    'Meta': 'META'
}

@app.route('/')
def index():
    return render_template('index.html', symbols=SYMBOLS)

@app.route('/delta')
def delta_analysis():
    days = request.args.get('days', default=7, type=int)
    try:
        delta_data = fetcher.fetch_delta_data(SYMBOLS, days)
        if delta_data.empty:
            return render_template('error.html', message="لا توجد بيانات متاحة")
        
        return render_template('delta.html', 
                            data=delta_data.to_dict('records'),
                            days=days,
                            SYMBOLS=SYMBOLS)
    except Exception as e:
        return render_template('error.html', message=f"حدث خطأ: {str(e)}")

@app.route('/moving_avg')
def moving_avg_analysis():
    symbol = request.args.get('symbol', default='AAPL')
    days = request.args.get('days', default=365, type=int)

    try:
        analysis_data = fetcher.fetch_moving_averages(symbol, days)
        if not analysis_data:
            return render_template('error.html', message="رمز السهم غير صحيح")

        history_df = analysis_data['history'].reset_index()
        history_df['Date'] = history_df['Date'].dt.strftime('%Y-%m-%d')
        history_data = history_df.to_dict('records')

        # ✅ هنا ضع هذا السطر
        available_stocks = [{'symbol': symbol, 'name': name} for name, symbol in SYMBOLS.items()]

        return render_template('moving_avg.html',
                               symbol=symbol,
                               current_price=analysis_data['current_price'],
                               prev_close=analysis_data['prev_close'],
                               year_high=analysis_data['year_high'],
                               year_low=analysis_data['year_low'],
                               ma_50=analysis_data['ma_50'],
                               ma_200=analysis_data['ma_200'],
                               history_data=history_data,
                               days=days,
                               available_stocks=available_stocks,
                               SYMBOLS=SYMBOLS)
    except Exception as e:
        return render_template('error.html', message=f"حدث خطأ: {str(e)}")


@app.route('/get_stock_data')
def get_stock_data():
    symbol = request.args.get('symbol')
    days = request.args.get('days', default=365, type=int)
    try:
        data = fetcher.fetch_moving_averages(symbol, days)
        if data:
            return jsonify({
                'status': 'success',
                'data': {
                    'symbol': symbol,
                    'current_price': float(data['current_price']),
                    'ma_50': float(data['ma_50']),
                    'ma_200': float(data['ma_200'])
                }
            })
        return jsonify({'status': 'error', 'message': 'No data found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
# في نهاية الملف بدل app.run()
if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    serve(app, host='0.0.0.0', port=5000)
