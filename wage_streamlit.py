import pandas as pd
import streamlit as st  
import pydeck as pdk
import plotly.express as px


st.title('日本の賃金データダッシュボード')

#賃金データの読み込み
df_jp_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv', encoding='shift-jis')
df_jp_category = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv', encoding='shift-jis')
df_pref_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv', encoding='shift-jis')


st.header('■2019年：一人当たり平均賃金のヒートマップ')

#全国の県庁所在地の緯度/経度情報読込
jp_lat_lon = pd.read_csv('./pref_lat_lon.csv')

#2種のデータで列名が異なるので、賃金データの列名を変更
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name':'都道府県名'})

#賃金データから、列[年齢]の値='年齢計' / 列[集計年] = 2019 の値抽出
df_pref_map = df_pref_ind[(df_pref_ind['年齢'] == '年齢計') & (df_pref_ind['集計年'] == 2019)]

#賃金データと緯度経度情報を、列[都道府県名]をキーとして結合
df_pref_map = pd.merge(df_pref_map, jp_lat_lon, on='都道府県名')

df_pref_map['一人当たり賃金（相対値）'] = ((df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())
                                        /(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min()))

#ヒートマップの表示
view = pdk.ViewState(
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,
    pitch=40.5,
)
layer = pdk.Layer(
    "HeatmapLayer",
    data=df_pref_map,
    opacity=0.4, #ヒートマップの透明度
    get_position=["lon", "lat"],
    threshold=0.3,
    get_weight = '一人当たり賃金（相対値）'
    )
layer_map = pdk.Deck(
    layers=layer,
    initial_view_state=view,
)
st.pydeck_chart(layer_map)

#ヒートマップの元となるデータの表示/非表示(チェックボックス)
show_df = st.checkbox('Show DataFrame')
if show_df == True:
    st.write(df_pref_map)

#集計年別の平均賃金推移をグラフ表示
st.header('■集計年別の一人当たり賃金（万円）の推移')

#賃金データから、列[年齢]の値='年齢計'の値抽出
df_ts_mean = df_jp_ind[(df_jp_ind['年齢'] == '年齢計')]
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）':'全国_一人当たり賃金（万円）'})

#賃金データから、列[年齢]の値='年齢計'の値抽出し、セレクトボックスで選択した都道府県のみグラフ表示
df_pref_mean = df_pref_ind[(df_pref_ind['年齢'] == '年齢計')]
pref_list = df_pref_mean['都道府県名'].unique()
option_pref = st.selectbox(
    '都道府県',
    (pref_list)) #都道府県の選択肢
df_pref_mean = df_pref_mean[df_pref_mean['都道府県名'] == option_pref]

#上記賃金データ2種を、集計年をキーとして結合
df_mean_line = pd.merge(df_ts_mean, df_pref_mean, on='集計年')

#表示するデータを、列[集計年][全国_一人当たり賃金（万円）][一人当たり賃金（万円）]に絞り込み
df_mean_line = df_mean_line[['集計年', '全国_一人当たり賃金（万円）', '一人当たり賃金（万円）']]
#df_mean_line = df_mean_line.astype({'集計年': 'int'})

#列[集計年]をインデックス(行名)に変更し、折れ線グラフとして表示
df_mean_line = df_mean_line.set_index('集計年')
st.line_chart(df_mean_line)


#年齢階級別のグラフ
st.header('■年齢階級別の全国一人当たり平均賃金（万円）')

#年齢階級別の賃金データ
df_mean_bubble = df_jp_ind[df_jp_ind['年齢'] != '年齢計']

#バブルチャートで4次元表示
##一人当たり賃金/年間賞与その他特別給与額を年齢別でまとめたバブルが時系列でどう変化するかアニメーション
fig = px.scatter(df_mean_bubble,
                x='一人当たり賃金（万円）',
                y='年間賞与その他特別給与額（万円）',
                range_x=[150,700],
                range_y=[0,150],
                size='所定内給与額（万円）',
                size_max=38,
                color='年齢',
                animation_frame='集計年',
                animation_group='年齢')
st.plotly_chart(fig)



#産業別の平均賃金を横棒グラフ表示
st.header('■産業別の賃金推移')

year_list = df_jp_category["集計年"].unique()
option_year = st.selectbox(
    '集計年',
    (year_list))

wage_list = ['一人当たり賃金（万円）', '所定内給与額（万円）', '年間賞与その他特別給与額（万円）'] 
option_wage = st.selectbox(
    '賃金の種類',
    (wage_list))

df_mean_categ = df_jp_category[(df_jp_category['集計年'] == option_year)]

#選択した賃金の種類の最大値+50 の値を、グラフの最大値に設定
max_x = df_mean_categ[option_wage].max() + 50

#横棒グラフ設定
fig = px.bar(df_mean_categ,
            x=option_wage, #横軸:セレクトボックスで選択した賃金の種類
            y='産業大分類名',#縦軸
            color='産業大分類名',
            animation_frame='年齢',
            range_x=[0, max_x],#横軸の上限
            orientation='h',   #横棒グラフに指定
            width=800,
            height=500)
st.plotly_chart(fig)

#オープンデータを使用する際は<記載必須>
st.text('出展:RESAS(地域経済分析システム)')
st.text('本結果はRESAS(地域経済分析システム)を加工して作成')
