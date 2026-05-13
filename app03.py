import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 页面基本设置 (设置为宽屏)
st.set_page_config(page_title="Power Bank Dashboard", layout="wide")
st.title("充电宝竞品分析面板 Power Bank Competitor Analysis Dashboard")

# 2. 数据读取与缓存配置
@st.cache_data(ttl=600)  # 缓存10分钟，避免频繁请求
def load_data():
    # ⚠️ 请在这里替换为你真实的 Google Sheets CSV 发布链接
    sheet_url = "https://docs.google.com/spreadsheets/d/1fkMRXkdKVdYFN3d_Y7bhFtA1BGIUlA3xAG86UvvhT1w/export?format=csv&gid=0"
    
    # 读取数据
    df = pd.read_csv(sheet_url)
    
    # 清洗价格列：去掉 $ 符号或逗号，转换为数字，遇到无法转换的转为 NaN
    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')
    
    # 清洗容量列：确保为字符串格式以便作为分类轴
    if 'Capacity/mAh' in df.columns:
        df['Capacity/mAh'] = df['Capacity/mAh'].astype(str)
        
    return df

# 加载数据
try:
    df = load_data()
except Exception as e:
    st.error(f"数据读取失败，请检查链接是否正确。错误信息: {e}")
    st.stop()

# 3. 侧边栏：刷新按钮与筛选器
st.sidebar.header("⚙️ 控制面板")

# 刷新数据按钮
if st.sidebar.button("🔄 刷新数据 (Refresh Data)"):
    st.cache_data.clear()
    st.rerun()

# 品牌筛选器
if 'Brand' in df.columns:
    brands = df['Brand'].dropna().unique().tolist()
    selected_brands = st.sidebar.multiselect("🏷️ 筛选品牌 (Filter Brands)", options=brands, default=brands)
    filtered_df = df[df['Brand'].isin(selected_brands)]
else:
    st.error("数据中未找到 'Brand' 列，请检查表头拼写。")
    st.stop()

# 4. 构建 Plotly 散点图
# 将所有需要悬停显示的列按顺序放进一个列表中 (注意 'Link' 在最后一个，即索引 20)
hover_cols = [
    'Brand', 'Model Number', 'URL of Image', 'Pickup or not', 'Sold by', 
    'Rating', 'Number of Reviews', 'Was Price', 'Price', 'Capacity/mAh', 
    'Pack', 'Size', 'Weight', 'Connect Type', 'Wireless', 'Fast charging', 
    'USB power', 'Battery Indicator', 'Warranty', 'Note', 'Link'
]

# 检查列是否存在，防止报错
missing_cols = [col for col in hover_cols if col not in filtered_df.columns]
if missing_cols:
    st.warning(f"数据表中缺失以下列，悬停框可能会显示不全: {', '.join(missing_cols)}")
    for col in missing_cols:
        filtered_df[col] = "N/A"

# 绘制散点图
fig = px.scatter(
    filtered_df,
    x='Capacity/mAh',
    y='Price',
    color='Brand',
    text='Brand',  # 在散点旁边显示品牌名
    custom_data=hover_cols, # 将所有数据打包进图表，供悬停框和点击事件调用
    height=650
)

# 5. 自定义图表样式与鼠标悬停弹窗
fig.update_traces(
    textposition='top center', 
    marker=dict(size=14, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')), 
    hovertemplate=(
        "<b>%{customdata[0]} - %{customdata[1]}</b><br><br>"
        "💰 <b>Price:</b> $%{customdata[8]}<br>"
        "🔋 <b>Capacity:</b> %{customdata[9]} mAh<br>"
        "🔌 <b>Ports:</b> %{customdata[13]}<br>"
        "⚡ <b>Fast Charge:</b> %{customdata[15]}<br>"
        "📶 <b>Wireless:</b> %{customdata[14]}<br>"
        "⭐ <b>Rating:</b> %{customdata[5]} (%{customdata[6]} reviews)<br>"
        "📦 <b>Size:</b> %{customdata[11]}<br>"
        "⚖️ <b>Weight:</b> %{customdata[12]}<br>"
        "🛒 <b>Sold by:</b> %{customdata[4]}<br>"
        "<extra></extra>"
    )
)

fig.update_layout(
    xaxis_title="电池容量 (Capacity / mAh)",
    yaxis_title="价格 (Price / USD)",
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial"),
    plot_bgcolor='#f9f9f9',
    clickmode='event+select' # 开启点击高亮反馈
)

# 6. 在 Streamlit 中渲染图表并【捕获点击事件】
st.markdown("### 👇 选中任意散点，即可获取跳转链接 Select any point to get the product link.")
event = st.plotly_chart(
    fig, 
    use_container_width=True, 
    on_select="rerun",       # 点击时触发页面重载
    selection_mode="points"  # 设置为点选模式
)

# 7. 点击反馈逻辑：根据点击的散点生成跳转按钮
if event and event.selection.points:
    # 获取被点击的点所携带的数据 (customdata)
    point_data = event.selection.points[0]
    
    if "customdata" in point_data:
        # hover_cols 列表中，索引 20 是 Link，索引 0 是 Brand，索引 1 是 Model
        link = point_data["customdata"][20]
        brand = point_data["customdata"][0]
        model = point_data["customdata"][1]
        
        # 检查链接是否为空且以 http 开头
        if pd.notna(link) and str(link).startswith("http"):
            st.success(f"✅ 您选中了: **{brand} - {model}**")
            # 显示一个显眼的跳转按钮
            st.link_button(f"🛒 点击这里前往产品链接", link, type="primary")
        else:
            st.warning(f"⚠️ 您选中了: **{brand} - {model}**，但数据表中暂无有效的跳转链接。")
else:
    st.info("🖱️ 提示：用鼠标在上方图表中点击任意一个散点。Tip: Click on any point in the chart above.")

# 底部数据预览表
with st.expander("📊 查看底层原始数据 View Original Data"):
    st.dataframe(filtered_df)
