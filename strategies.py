import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import logging

logger = logging.getLogger(__name__)


class TradingStrategy:
    def __init__(self, name):
        self.name = name
        
    def analyze(self, klines):
        raise NotImplementedError("Strategy must implement analyze method")


class SimpleMAStrategy(TradingStrategy):
    def __init__(self, short_period=20, long_period=50):
        super().__init__("Simple Moving Average")
        self.short_period = short_period
        self.long_period = long_period
    
    def analyze(self, klines):
        if len(klines) < self.long_period:
            return 'HOLD', 0.0
        
        df = self._klines_to_df(klines)
        
        sma_short = SMAIndicator(close=df['close'], window=self.short_period)
        sma_long = SMAIndicator(close=df['close'], window=self.long_period)
        
        df['sma_short'] = sma_short.sma_indicator()
        df['sma_long'] = sma_long.sma_indicator()
        
        current_price = df['close'].iloc[-1]
        sma_short_value = df['sma_short'].iloc[-1]
        sma_long_value = df['sma_long'].iloc[-1]
        
        if sma_short_value > sma_long_value and current_price > sma_short_value:
            signal = 'BUY'
            confidence = min((sma_short_value - sma_long_value) / sma_long_value * 100, 100)
        elif sma_short_value < sma_long_value and current_price < sma_short_value:
            signal = 'SELL'
            confidence = min((sma_long_value - sma_short_value) / sma_long_value * 100, 100)
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return signal, confidence
    
    def _klines_to_df(self, klines):
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['open'] = pd.to_numeric(df['open'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        return df


class RSIStrategy(TradingStrategy):
    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__("RSI Strategy")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def analyze(self, klines):
        if len(klines) < self.period + 1:
            return 'HOLD', 0.0
        
        df = self._klines_to_df(klines)
        
        rsi = RSIIndicator(close=df['close'], window=self.period)
        df['rsi'] = rsi.rsi()
        
        current_rsi = df['rsi'].iloc[-1]
        
        if current_rsi < self.oversold:
            signal = 'BUY'
            confidence = (self.oversold - current_rsi) / self.oversold * 100
        elif current_rsi > self.overbought:
            signal = 'SELL'
            confidence = (current_rsi - self.overbought) / (100 - self.overbought) * 100
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return signal, confidence
    
    def _klines_to_df(self, klines):
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['close'] = pd.to_numeric(df['close'])
        return df


class BollingerBandsStrategy(TradingStrategy):
    def __init__(self, period=20, std_dev=2):
        super().__init__("Bollinger Bands")
        self.period = period
        self.std_dev = std_dev
    
    def analyze(self, klines):
        if len(klines) < self.period:
            return 'HOLD', 0.0
        
        df = self._klines_to_df(klines)
        
        bb = BollingerBands(close=df['close'], window=self.period, window_dev=self.std_dev)
        
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        current_price = df['close'].iloc[-1]
        upper_band = df['bb_upper'].iloc[-1]
        lower_band = df['bb_lower'].iloc[-1]
        middle_band = df['bb_middle'].iloc[-1]
        
        band_width = upper_band - lower_band
        
        if current_price <= lower_band:
            signal = 'BUY'
            confidence = min((lower_band - current_price) / band_width * 100, 100)
        elif current_price >= upper_band:
            signal = 'SELL'
            confidence = min((current_price - upper_band) / band_width * 100, 100)
        else:
            signal = 'HOLD'
            confidence = 0.0
        
        return signal, confidence
    
    def _klines_to_df(self, klines):
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['close'] = pd.to_numeric(df['close'])
        return df


class CombinedStrategy(TradingStrategy):
    def __init__(self):
        super().__init__("Combined Strategy")
        self.strategies = [
            SimpleMAStrategy(),
            RSIStrategy(),
            BollingerBandsStrategy()
        ]
    
    def analyze(self, klines):
        signals = []
        confidences = []
        
        for strategy in self.strategies:
            signal, confidence = strategy.analyze(klines)
            signals.append(signal)
            confidences.append(confidence)
        
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count and buy_count >= 2:
            final_signal = 'BUY'
            final_confidence = np.mean([c for s, c in zip(signals, confidences) if s == 'BUY'])
        elif sell_count > buy_count and sell_count >= 2:
            final_signal = 'SELL'
            final_confidence = np.mean([c for s, c in zip(signals, confidences) if s == 'SELL'])
        else:
            final_signal = 'HOLD'
            final_confidence = 0.0
        
        return final_signal, final_confidence