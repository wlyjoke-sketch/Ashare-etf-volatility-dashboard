"""
ETF波动率分析仪表板 - Streamlit主应用
"""
import streamlit as st
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

from data_updater import update_all_data, TARGET_ETFS
from chart_generator import (
    generate_price_chart,
    generate_hv_chart,
    generate_vix_chart,
    get_latest_stats
)

# 页面配置
st.set_page_config(
    page_title="ETF波动率分析仪表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📈 ETF波动率分析仪表板")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("控制面板")
    
    # ETF选择
    etf_names = [etf['name'] for etf in TARGET_ETFS]
    etf_display_names = {
        '50ETF': '50ETF',
        '300ETF_Huatai': '300ETF(华泰)',
        '500ETF_Southern': '500ETF(南方)',
        'STAR50_ChinaAMC': '科创50',
        'ChiNext_EFund': '创业板'
    }
    
    selected_display = st.selectbox(
        "选择ETF",
        [etf_display_names[name] for name in etf_names],
        index=0
    )
    
    # 反向查找code
    name_to_code = {etf['name']: etf['code'] for etf in TARGET_ETFS}
    display_to_name = {v: k for k, v in etf_display_names.items()}
    selected_name = display_to_name[selected_display]
    selected_code = name_to_code[selected_name]
    
    st.markdown("---")
    
    # 更新按钮
    st.subheader("数据更新")
    if st.button("🔄 更新所有数据", type="primary", use_container_width=True):
        with st.spinner("正在更新数据,请稍候..."):
            try:
                results = update_all_data()
                st.success("✅ 数据更新完成!")
                st.dataframe(results, use_container_width=True)
            except Exception as e:
                st.error(f"❌ 更新失败: {e}")
    
    st.markdown("---")
    
    # 显示最新统计
    st.subheader("最新数据")
    stats = get_latest_stats(selected_code)
    
    if stats:
        for key, value in stats.items():
            st.metric(key, value)
    else:
        st.warning("暂无数据")

# 主区域
st.header(f"{selected_display} 波动率分析")

# 创建三个图表
try:
    # 图表1: 价格走势
    with st.container():
        st.subheader("1️⃣ 价格走势")
        price_chart = generate_price_chart(selected_code, selected_display)
        
        if price_chart:
            st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.warning("⚠️ 价格数据不可用,请点击更新按钮")
    
    st.markdown("---")
    
    # 图表2: 历史波动率
    with st.container():
        st.subheader("2️⃣ 历史波动率 (HV20/60/252)")
        hv_chart = generate_hv_chart(selected_code, selected_display)
        
        if hv_chart:
            st.plotly_chart(hv_chart, use_container_width=True)
            
            # 添加说明
            with st.expander("📖 波动率说明"):
                st.markdown("""
                - **HV20**: 20日历史波动率(约1个月),反映短期波动
                - **HV60**: 60日历史波动率(约3个月),反映中期波动
                - **HV252**: 252日历史波动率(约1年),反映长期波动
                
                波动率越高,市场波动越剧烈;波动率越低,市场越平稳。
                """)
        else:
            st.warning("⚠️ 历史波动率数据不可用,请点击更新按钮")
    
    st.markdown("---")
    
    # 图表3: VIX vs HV
    with st.container():
        st.subheader("3️⃣ VIX vs 历史波动率 (2023至今)")
        vix_chart = generate_vix_chart(selected_code, selected_display)
        
        if vix_chart:
            st.plotly_chart(vix_chart, use_container_width=True)
            
            # 添加说明
            with st.expander("📖 VIX vs HV说明"):
                st.markdown("""
                - **VIX**: 隐含波动率指数,从期权价格反推,反映市场对未来波动的预期
                - **HV20**: 历史波动率(短期),反映过去实际波动
                - **HV252**: 历史波动率(长期),反映长期平均波动
                
                **关键信号**:
                - VIX < HV: 期权被低估,适合买入期权(做多波动率)
                - VIX > HV: 期权被高估,适合卖出期权(做空波动率)
                """)
        else:
            st.warning("⚠️ VIX数据不可用,请点击更新按钮")

except Exception as e:
    st.error(f"❌ 加载图表时出错: {e}")
    import traceback
    st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    <p>ETF波动率分析仪表板 | 数据来源: Tushare</p>
    </div>
    """,
    unsafe_allow_html=True
)
