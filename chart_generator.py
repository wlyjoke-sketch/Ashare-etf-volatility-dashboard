"""
图表生成模块 - 使用Plotly生成交互式图表
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# 数据路径
DATA_DIR = os.path.join(parent_dir, 'data')

def load_etf_data(code):
    """加载ETF历史数据"""
    file_path = os.path.join(DATA_DIR, 'volatility', f'{code}_full_history.csv')
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()  # 只保留日期部分
    df = df.sort_values('trade_date').set_index('trade_date')
    return df

def load_hv_data(code):
    """加载历史波动率数据"""
    file_path = os.path.join(DATA_DIR, 'volatility', f'{code}_with_hv.csv')
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()  # 只保留日期部分
    df = df.set_index('trade_date')
    return df

def load_vix_data(code):
    """加载VIX数据"""
    file_path = os.path.join(DATA_DIR, 'vix', f'{code}_vix.csv')
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()  # 只保留日期部分  
    df = df.set_index('trade_date')
    return df

def generate_price_chart(code, name):
    """生成价格走势图"""
    df = load_etf_data(code)
    
    if df is None or df.empty:
        return None
    
    # 计算百分位
    current_price = df.iloc[-1]['close']
    
    # 全历史百分位
    all_percentile = (df['close'] < current_price).sum() / len(df) * 100
    
    # 过去一年百分位
    one_year_ago = df.index[-1] - pd.Timedelta(days=365)
    df_1y = df[df.index >= one_year_ago]
    if len(df_1y) > 0:
        year_percentile = (df_1y['close'] < current_price).sum() / len(df_1y) * 100
    else:
        year_percentile = all_percentile
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['close'],
        mode='lines',
        name='收盘价',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 添加当前价格水平线
    fig.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="red",
        opacity=0.5,
        annotation_text=f"当前: {current_price:.3f}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=f'{name} 价格走势 | 当前百分位: 全历史 {all_percentile:.1f}% / 过去一年 {year_percentile:.1f}%',
        xaxis_title='日期',
        yaxis_title='价格 (元)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def generate_hv_chart(code, name):
    """生成历史波动率图"""
    df = load_hv_data(code)
    
    if df is None or df.empty:
        return None
    
    # 计算HV20百分位
    current_hv20 = df.iloc[-1]['HV20']
    
    # 全历史百分位
    all_percentile = (df['HV20'].dropna() < current_hv20).sum() / df['HV20'].dropna().count() * 100
    
    # 过去一年百分位
    one_year_ago = df.index[-1] - pd.Timedelta(days=365)
    df_1y = df[df.index >= one_year_ago]
    if len(df_1y) > 0 and df_1y['HV20'].dropna().count() > 0:
        year_percentile = (df_1y['HV20'].dropna() < current_hv20).sum() / df_1y['HV20'].dropna().count() * 100
    else:
        year_percentile = all_percentile
    
    fig = go.Figure()
    
    # HV20
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['HV20'],
        mode='lines',
        name='HV20 (月度)',
        line=dict(color='#1f77b4', width=1.5)
    ))
    
    # HV60
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['HV60'],
        mode='lines',
        name='HV60 (季度)',
        line=dict(color='#ff7f0e', width=1.5)
    ))
    
    # HV252
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['HV252'],
        mode='lines',
        name='HV252 (年度)',
        line=dict(color='#2ca02c', width=1.5)
    ))
    
    # 添加当前HV20水平线
    fig.add_hline(
        y=current_hv20,
        line_dash="dash",
        line_color="blue",
        opacity=0.5,
        annotation_text=f"当前HV20: {current_hv20:.1f}%",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=f'{name} 历史波动率 | HV20百分位: 全历史 {all_percentile:.1f}% / 过去一年 {year_percentile:.1f}%',
        xaxis_title='日期',
        yaxis_title='年化波动率 (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def generate_vix_chart(code, name):
    """生成VIX vs HV对比图 (2023至今)"""
    vix_df = load_vix_data(code)
    hv_df = load_hv_data(code)
    
    if vix_df is None or hv_df is None:
        return None
    
    # 合并数据
    df = pd.concat([vix_df['VIX'], hv_df[['HV20', 'HV252']]], axis=1).dropna()
    
    # 筛选2023年至今
    df = df[df.index >= '2023-01-01']
    
    if df.empty:
        return None
    
    # 计算VIX百分位(使用全部VIX数据,不只是2023年)
    current_vix = df.iloc[-1]['VIX']
    
    # 全历史百分位(使用完整VIX数据)
    full_vix = vix_df['VIX'].dropna()
    all_percentile = (full_vix < current_vix).sum() / len(full_vix) * 100
    
    # 过去一年百分位
    one_year_ago = vix_df.index[-1] - pd.Timedelta(days=365)
    vix_1y = vix_df[vix_df.index >= one_year_ago]['VIX'].dropna()
    if len(vix_1y) > 0:
        year_percentile = (vix_1y < current_vix).sum() / len(vix_1y) * 100
    else:
        year_percentile = all_percentile
    
    fig = go.Figure()
    
    # VIX
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['VIX'],
        mode='lines',
        name='VIX (隐含波动率)',
        line=dict(color='red', width=2)
    ))
    
    # HV20
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['HV20'],
        mode='lines',
        name='HV20 (历史波动率)',
        line=dict(color='#1f77b4', width=1.5, dash='dot')
    ))
    
    # HV252
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['HV252'],
        mode='lines',
        name='HV252 (年度波动率)',
        line=dict(color='#2ca02c', width=1.5, dash='dash')
    ))
    
    # 添加当前VIX水平线
    fig.add_hline(
        y=current_vix,
        line_dash="dash",
        line_color="red",
        opacity=0.5,
        annotation_text=f"当前VIX: {current_vix:.1f}%",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=f'{name} VIX vs 历史波动率 (2023至今) | VIX百分位: 全历史 {all_percentile:.1f}% / 过去一年 {year_percentile:.1f}%',
        xaxis_title='日期',
        yaxis_title='波动率 (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def get_latest_stats(code):
    """获取最新统计数据"""
    hv_df = load_hv_data(code)
    vix_df = load_vix_data(code)
    etf_df = load_etf_data(code)
    
    if hv_df is None or vix_df is None or etf_df is None:
        return None
    
    # 获取最新数据
    latest_hv = hv_df.iloc[-1]
    latest_vix = vix_df.iloc[-1]['VIX'] if not vix_df.empty else None
    latest_price = etf_df.iloc[-1]['close']
    latest_date = etf_df.index[-1]
    
    stats = {
        '最新日期': latest_date.strftime('%Y-%m-%d'),
        '最新价格': f'{latest_price:.3f}',
        'VIX': f'{latest_vix:.2f}%' if latest_vix else 'N/A',
        'HV20': f'{latest_hv["HV20"]:.2f}%',
        'HV60': f'{latest_hv["HV60"]:.2f}%',
        'HV252': f'{latest_hv["HV252"]:.2f}%'
    }
    
    return stats
