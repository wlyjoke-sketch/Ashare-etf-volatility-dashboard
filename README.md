# ETF波动率分析仪表板

一个基于Streamlit的交互式Web应用,用于展示和分析中国A股ETF期权的波动率数据。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 功能特性

- 📊 **三张交互式图表**:
  1. ETF价格走势(含百分位指标)
  2. 历史波动率HV20/60/252对比
  3. VIX隐含波动率 vs 历史波动率(2023至今)

- 🔄 **一键增量数据更新**: 自动检测最新数据,只更新缺失部分

- 📈 **支持5个主流ETF**:
  - 50ETF (510050.SH)
  - 300ETF华泰 (510300.SH)
  - 500ETF南方 (510500.SH)
  - 科创50 (588000.SH)
  - 创业板 (159915.SZ)

- 📉 **百分位指标**: 显示当前值在全历史和过去一年中的相对位置

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/etf-volatility-dashboard.git
cd etf-volatility-dashboard
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置Tushare Token

在项目**父目录**创建`ts_token.txt`文件,并填入您的Tushare API token:

```bash
# 在 etf_volatility_dashboard 的父目录创建
echo "YOUR_TUSHARE_TOKEN" > ../ts_token.txt
```

> 💡 如何获取Tushare Token: 访问 [Tushare官网](https://tushare.pro/) 注册并获取免费token

### 4. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开: `http://localhost:8501`

## 使用说明

### 选择ETF
在左侧边栏的下拉菜单中选择要查看的ETF

### 更新数据
点击左侧边栏的"🔄 更新所有数据"按钮,系统将:
- 增量更新ETF历史价格数据
- 重新计算历史波动率(HV20/60/252)
- 增量更新VIX指数(基于期权价格)

### 查看图表

**图表1 - 价格走势**:
- 显示ETF完整历史价格
- 红色虚线标注当前价格
- 标题显示当前价格的百分位(全历史/过去一年)

**图表2 - 历史波动率**:
- HV20: 20日历史波动率(月度)
- HV60: 60日历史波动率(季度)
- HV252: 252日历史波动率(年度)
- 蓝色虚线标注当前HV20
- 标题显示HV20的百分位

**图表3 - VIX vs HV**:
- VIX: 从期权价格反推的隐含波动率
- 对比HV20和HV252
- 红色虚线标注当前VIX
- 标题显示VIX的百分位

### 百分位解读

- **0-20%**: 极低水平,历史底部区域
- **20-40%**: 较低水平
- **40-60%**: 中等水平
- **60-80%**: 较高水平
- **80-100%**: 极高水平,历史顶部区域

## 数据说明

### 历史波动率(HV)
使用对数收益率的滚动标准差计算,并年化:
- **HV20**: 反映短期(约1个月)波动
- **HV60**: 反映中期(约3个月)波动
- **HV252**: 反映长期(约1年)波动

### VIX指数
- 从ATM期权价格反推隐含波动率
- 选择20-40天到期的Call期权
- 加权平均计算,权重与moneyness相关
- **VIX < HV**: 期权被低估,适合买入
- **VIX > HV**: 期权被高估,适合卖出

## 项目结构

```
etf_volatility_dashboard/
├── app.py                  # Streamlit主应用
├── data_updater.py        # 数据更新模块(增量更新)
├── chart_generator.py     # 图表生成模块(Plotly)
├── requirements.txt       # Python依赖包
├── README.md             # 项目说明
├── .gitignore            # Git忽略文件
└── (需要在父目录)
    └── ts_token.txt      # Tushare API token(不上传)
    └── config.py         # ETF配置文件(共享)
    └── data/             # 数据目录(不上传)
        ├── volatility/   # ETF历史数据和HV
        ├── vix/          # VIX数据
        └── multi_etf/    # 期权数据
```

## 技术栈

- **Streamlit**: Web应用框架
- **Plotly**: 交互式图表
- **Pandas**: 数据处理
- **NumPy**: 数值计算
- **Tushare**: 金融数据API
- **Scipy**: 期权定价(Black-Scholes)和隐含波动率计算

## 数据更新机制

### 增量更新
- 自动检测最后数据日期
- 只获取缺失日期的新数据
- 节省API调用次数和时间
- VIX只计算新日期,不重复计算

### 更新内容
1. ETF历史数据(价格、成交量等)
2. 历史波动率(HV20/60/252)
3. VIX指数(基于现有期权processed数据)

## 注意事项

⚠️ **首次使用**:
- 需要先运行父目录的数据获取脚本,生成基础数据
- 首次点击"更新数据"会从最后日期开始更新

⚠️ **API限制**:
- Tushare免费用户有调用频率限制
- 建议每天更新一次数据即可
- 数据更新可能需要1-2分钟

⚠️ **数据依赖**:
- VIX计算依赖`data/multi_etf/`中的processed期权数据
- 如果没有期权数据,VIX更新会跳过

## 贡献

欢迎提交Issue和Pull Request!

## 许可证

MIT License

## 致谢

- 数据来源: [Tushare](https://tushare.pro/)
- 图表库: [Plotly](https://plotly.com/)
- Web框架: [Streamlit](https://streamlit.io/)

## 联系方式

如有问题或建议,欢迎提Issue!
