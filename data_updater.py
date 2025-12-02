"""
数据更新模块 - 基于现有data目录结构的增量更新
"""
import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
from scipy.optimize import brentq
import os
import sys
import time

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from config import ETFS

# 数据路径 - 使用现有的data目录
DATA_DIR = os.path.join(parent_dir, 'data')

# 读取tusahre pro的token
token_path = os.path.join(parent_dir, 'ts_token.txt')
with open(token_path, 'r') as f:
    token = f.read().strip()

ts.set_token(token)
pro = ts.pro_api()

CONTRACT_UNIT = 10000
RISK_FREE_RATE = 0.03

# 只使用5个目标ETF
TARGET_ETFS = [
    {'code': '510050.SH', 'name': '50ETF'},
    {'code': '510300.SH', 'name': '300ETF_Huatai'},
    {'code': '510500.SH', 'name': '500ETF_Southern'},
    {'code': '588000.SH', 'name': 'STAR50_ChinaAMC'},
    {'code': '159915.SZ', 'name': 'ChiNext_EFund'}
]

def update_etf_history(code, name):
    """增量更新ETF历史数据到data/volatility目录"""
    print(f"更新 {name} 历史数据...")
    
    file_path = os.path.join(DATA_DIR, 'volatility', f'{code}_full_history.csv')
    
    # 确定起始日期
    if os.path.exists(file_path):
        existing = pd.read_csv(file_path)
        existing['trade_date'] = pd.to_datetime(existing['trade_date'])
        last_date = existing['trade_date'].max()
        start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
        print(f"  最后日期: {last_date.date()}, 从 {start_date} 开始更新")
    else:
        # 获取基金基本信息
        try:
            fund_info = pro.fund_basic(ts_code=code)
            if not fund_info.empty:
                start_date = fund_info.iloc[0]['list_date']
            else:
                start_date = '20170901'
        except:
            start_date = '20170901'
        print(f"  首次获取,从 {start_date} 开始")
        existing = pd.DataFrame()
    
    end_date = datetime.now().strftime('%Y%m%d')
    
    # 获取新数据
    try:
        new_data = pro.fund_daily(
            ts_code=code,
            start_date=start_date,
            end_date=end_date
        )
        
        if new_data.empty:
            print(f"  无新数据")
            return False
        
        new_data['trade_date'] = pd.to_datetime(new_data['trade_date']).dt.normalize()
        
        # 合并数据
        if not existing.empty:
            existing['trade_date'] = pd.to_datetime(existing['trade_date']).dt.normalize()
            updated = pd.concat([existing, new_data]).drop_duplicates(subset=['trade_date'])
        else:
            updated = new_data
        
        updated = updated.sort_values('trade_date')
        # 保存时只保留日期部分
        updated['trade_date'] = updated['trade_date'].dt.date
        updated.to_csv(file_path, index=False)
        
        print(f"  新增 {len(new_data)} 条数据")
        return True
        
    except Exception as e:
        print(f"  错误: {e}")
        return False

def calculate_historical_volatility(prices, windows=[20, 60, 252]):
    """计算历史波动率"""
    log_returns = np.log(prices / prices.shift(1))
    
    result = pd.DataFrame(index=prices.index)
    for window in windows:
        vol = log_returns.rolling(window=window).std() * np.sqrt(252)
        result[f'HV{window}'] = vol * 100
    
    return result

def update_hv(code, name):
    """更新历史波动率到data/volatility目录"""
    print(f"计算 {name} 历史波动率...")
    
    history_path = os.path.join(DATA_DIR, 'volatility', f'{code}_full_history.csv')
    
    if not os.path.exists(history_path):
        print(f"  历史数据不存在,跳过")
        return False
    
    try:
        df = pd.read_csv(history_path)
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()  # 只保留日期
        df = df.sort_values('trade_date').set_index('trade_date')
        
        # 计算HV
        hv = calculate_historical_volatility(df['close'])
        
        # 合并
        df_with_hv = pd.concat([df, hv], axis=1)
        
        # 重置索引以保存trade_date列
        df_with_hv = df_with_hv.reset_index()
        # 确保trade_date只有日期部分
        df_with_hv['trade_date'] = df_with_hv['trade_date'].dt.date
        
        # 保存
        output_path = os.path.join(DATA_DIR, 'volatility', f'{code}_with_hv.csv')
        df_with_hv.to_csv(output_path, index=False)
        
        print(f"  计算完成")
        return True
        
    except Exception as e:
        print(f"  错误: {e}")
        return False

def black_scholes_price(S, K, T, r, sigma, option_type='C'):
    """Black-Scholes期权定价"""
    if T <= 0:
        return max(S - K, 0) if option_type == 'C' else max(K - S, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'C':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    return price

def implied_volatility(market_price, S, K, T, r, option_type='C'):
    """计算隐含波动率"""
    if T <= 0:
        return np.nan
    
    intrinsic = max(S - K, 0) if option_type == 'C' else max(K - S, 0)
    if market_price <= intrinsic:
        return np.nan
    
    try:
        def objective(sigma):
            return black_scholes_price(S, K, T, r, sigma, option_type) - market_price
        
        iv = brentq(objective, 0.01, 5.0, maxiter=100)
        return iv
    except:
        return np.nan

def calculate_vix_for_date(day_options, underlying_price):
    """计算单日VIX"""
    # 筛选30天左右到期的Call期权
    candidates = day_options[(day_options['dte'] >= 20) & (day_options['dte'] <= 40)]
    
    if candidates.empty:
        return np.nan
    
    calls = candidates[candidates['call_put'] == 'C'].copy()
    
    if calls.empty:
        return np.nan
    
    # 选择ATM附近的期权
    calls['moneyness'] = abs(calls['exercise_price'] - underlying_price) / underlying_price
    atm_calls = calls.nsmallest(5, 'moneyness')
    
    if atm_calls.empty:
        return np.nan
    
    # 计算隐含波动率
    ivs = []
    weights = []
    
    for _, row in atm_calls.iterrows():
        T = row['dte'] / 365.0
        iv = implied_volatility(
            market_price=row['close'],
            S=underlying_price,
            K=row['exercise_price'],
            T=T,
            r=RISK_FREE_RATE,
            option_type='C'
        )
        
        if not np.isnan(iv) and 0.01 < iv < 3.0:
            ivs.append(iv)
            weight = 1.0 / (1.0 + row['moneyness'])
            weights.append(weight)
    
    if not ivs:
        return np.nan
    
    weights = np.array(weights)
    weights = weights / weights.sum()
    vix = np.average(ivs, weights=weights) * 100
    
    return vix

def update_vix(code, name):
    """增量更新VIX到data/vix目录(只计算新日期的VIX)"""
    print(f"更新 {name} VIX...")
    
    processed_path = os.path.join(DATA_DIR, 'multi_etf', f'{code}_processed.csv')
    vix_path = os.path.join(DATA_DIR, 'vix', f'{code}_vix.csv')
    
    if not os.path.exists(processed_path):
        print(f"  处理后的期权数据不存在,跳过")
        return False
    
    try:
        # 加载期权数据
        opt_df = pd.read_csv(processed_path, low_memory=False)
        opt_df['trade_date'] = pd.to_datetime(opt_df['trade_date']).dt.normalize()
        
        # 确定需要计算的日期
        if os.path.exists(vix_path):
            existing_vix = pd.read_csv(vix_path)
            existing_vix['trade_date'] = pd.to_datetime(existing_vix['trade_date']).dt.normalize()
            last_vix_date = existing_vix['trade_date'].max()
            dates_to_calc = opt_df[opt_df['trade_date'] > last_vix_date]['trade_date'].unique()
            print(f"  最后VIX日期: {last_vix_date.date()}")
        else:
            dates_to_calc = opt_df['trade_date'].unique()
            existing_vix = pd.DataFrame()
            print(f"  首次计算VIX")
        
        if len(dates_to_calc) == 0:
            print(f"  无新日期需要计算")
            return False
        
        print(f"  计算 {len(dates_to_calc)} 个新日期的VIX...")
        
        # 计算新日期的VIX
        new_vix_data = []
        for date in sorted(dates_to_calc):
            day_options = opt_df[opt_df['trade_date'] == date]
            
            if day_options.empty:
                continue
            
            underlying_price = day_options.iloc[0]['underlying_price']
            vix = calculate_vix_for_date(day_options, underlying_price)
            
            new_vix_data.append({
                'trade_date': pd.Timestamp(date).date(),  # 只保留日期
                'VIX': vix
            })
        
        # 合并数据
        new_vix_df = pd.DataFrame(new_vix_data)
        
        if not existing_vix.empty:
            existing_vix['trade_date'] = existing_vix['trade_date'].dt.date
            updated_vix = pd.concat([existing_vix, new_vix_df]).drop_duplicates(subset=['trade_date'])
        else:
            updated_vix = new_vix_df
        
        updated_vix = updated_vix.sort_values('trade_date')
        updated_vix.to_csv(vix_path, index=False)
        
        print(f"  新增 {len(new_vix_data)} 个VIX数据点")
        return True
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_all_data():
    """更新所有ETF的数据到现有data目录"""
    results = []
    
    for etf in TARGET_ETFS:
        code = etf['code']
        name = etf['name']
        
        print(f"\n{'='*60}")
        print(f"处理 {name} ({code})")
        print(f"{'='*60}")
        
        # 1. 更新ETF历史数据
        etf_updated = update_etf_history(code, name)
        
        # 2. 更新历史波动率
        hv_updated = update_hv(code, name)
        
        # 3. 更新VIX(增量) - 依赖现有的processed数据
        vix_updated = update_vix(code, name)
        
        results.append({
            'ETF': name,
            'ETF数据': '✓' if etf_updated else '×',
            'HV': '✓' if hv_updated else '×',
            'VIX': '✓' if vix_updated else '×'
        })
    
    print(f"\n{'='*60}")
    print("更新完成!")
    print(f"{'='*60}")
    
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    return results_df

if __name__ == '__main__':
    update_all_data()
