# data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Union, Optional

# إعداد نظام التسجيل (logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        """تهيئة كائن جلب بيانات الأسهم"""
        self.today = datetime.today()
        self.cache = {}  # ذاكرة تخزين مؤقت للبيانات
        
    def _get_cached_data(self, key: str) -> Optional[pd.DataFrame]:
        """استرجاع البيانات من الذاكرة المؤقتة"""
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < 300:  # 5 دقائق صلاحية
                return cached_data
        return None
    
    def _set_cache_data(self, key: str, data: pd.DataFrame) -> None:
        """تخزين البيانات في الذاكرة المؤقتة"""
        self.cache[key] = (data, datetime.now())
    
    def fetch_delta_data(self, symbols: Dict[str, str], days: int = 7) -> pd.DataFrame:
        """
        جلب بيانات الدلتا للأسهم والمؤشرات
        
        Args:
            symbols (Dict[str, str]): قامة برموز الأسهم وأسمائها
            days (int): عدد الأيام للفترة الزمنية
        
        Returns:
            pd.DataFrame: بيانات الدلتا
        """
        try:
            start_date = self.today - timedelta(days=days)
            cache_key = f"delta_{'_'.join(symbols.values())}_{days}"
            
            # التحقق من الذاكرة المؤقتة
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                logger.info("استرجاع بيانات الدلتا من الذاكرة المؤقتة")
                return cached_data
            
            logger.info(f"جلب بيانات الدلتا من Yahoo Finance للفترة {days} يوم")
            data = yf.download(
                list(symbols.values()),
                start=start_date,
                end=self.today,
                group_by='ticker'
            )
            
            if data.empty:
                logger.warning("لا توجد بيانات متاحة")
                return pd.DataFrame()
            
            results = []
            for name, symbol in symbols.items():
                if symbol in data:
                    adj_close = data[symbol]['Adj Close']
                    if not adj_close.empty:
                        delta = ((adj_close.iloc[-1] - adj_close.iloc[0]) / adj_close.iloc[0]) * 100
                        results.append({
                            'Symbol': symbol,
                            'Name': name,
                            'Delta (%)': round(delta, 2),
                            'Last Price': round(adj_close.iloc[-1], 2),
                            'Start Date': start_date.strftime('%Y-%m-%d'),
                            'End Date': self.today.strftime('%Y-%m-%d')
                        })
            
            df = pd.DataFrame(results).sort_values('Delta (%)', ascending=False)
            self._set_cache_data(cache_key, df)
            return df
            
        except Exception as e:
            logger.error(f"حدث خطأ في جلب بيانات الدلتا: {str(e)}")
            return pd.DataFrame()
    
    def fetch_moving_averages(self, symbol: str, days: int = 365) -> Optional[Dict]:
        """
        جلب بيانات المتوسطات المتحركة للسهم
        
        Args:
            symbol (str): رمز السهم
            days (int): عدد الأيام للفترة الزمنية
        
        Returns:
            Optional[Dict]: بيانات التحليل أو None إذا فشل
        """
        try:
            start_date = self.today - timedelta(days=days)
            cache_key = f"ma_{symbol}_{days}"
            
            # التحقق من الذاكرة المؤقتة
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                logger.info("استرجاع بيانات المتوسطات من الذاكرة المؤقتة")
                return cached_data
            
            logger.info(f"جلب بيانات المتوسطات المتحركة للسهم {symbol}")
            stock_data = yf.download(
                symbol,
                start=start_date,
                end=self.today,
                progress=False
            )
            
            if stock_data.empty:
                logger.warning(f"لا توجد بيانات للسهم {symbol}")
                return None
            
            # حساب المتوسطات المتحركة
            stock_data['MA_50'] = stock_data['Close'].rolling(window=50, min_periods=1).mean()
            stock_data['MA_200'] = stock_data['Close'].rolling(window=200, min_periods=1).mean()
            
            latest = stock_data.iloc[-1]
            prev_close = stock_data.iloc[-2]['Close'] if len(stock_data) > 1 else latest['Close']
            
            result = {
                'symbol': symbol,
                'current_price': latest['Close'],
                'prev_close': prev_close,
                'year_high': stock_data['High'].max(),
                'year_low': stock_data['Low'].min(),
                'ma_50': latest['MA_50'],
                'ma_200': latest['MA_200'],
                'history': stock_data,
                'start_date': start_date,
                'end_date': self.today
            }
            
            self._set_cache_data(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"حدث خطأ في جلب بيانات المتوسطات المتحركة: {str(e)}")
            return None