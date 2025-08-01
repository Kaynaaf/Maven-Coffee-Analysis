import pandas as pd
import streamlit as st
import plotly.express as px


#---------STREAMLIT PAGE CONFIG---------
st.set_page_config(layout="wide")
st.sidebar.title(":material/space_dashboard: Dashboard Filters")





#------LOAD REVENUE DATA---------------
# Load Data
@st.cache_data
def load_data():
    return pd.read_csv('data/coffee_revenue_monthly.csv')
df = load_data()
df['month']=df['month'].astype('int64') #set month as type int
pivot_df = df.pivot_table(index=["product_category","month"],values="revenue",aggfunc="sum")
pivot_df = pivot_df.reset_index()




col1, col2, col3 = st.columns([1,2 , 1],vertical_alignment='center')
with col2:
    st.title(' :material/local_cafe: Coffee Sales Dashboard')

    st.header(" :material/monitoring: *KPIs at a glance*")





#-------------KPI Columns------------------- 

met1,met2,met3 = st.columns(3)

kpi_data = pd.read_csv("data/kpi_data.csv")
kpi_data['date'] = pd.to_datetime(kpi_data['date'])
kpi_data['month'] = kpi_data['date'].dt.to_period("M")

# Group by month and aggregate columns
monthly_df = kpi_data.groupby('month').agg({
    'revenue': 'sum',
    'aov': 'mean',
    'orders': 'sum'
}).reset_index()



# Compare current month's metrics with the previous one.
# Only compute KPIs if at least two months of data is available for comparison
if len(monthly_df) >= 2:
    current = monthly_df.iloc[-1]
    previous = monthly_df.iloc[-2]


    with met1:
        st.metric(
            label="Revenue MoM",
            value= f"${current['revenue']:.2f}",
            delta= round(current['revenue'] - previous['revenue'],2),
            border=True
        )

    with met2:
        st.metric(
            label="Avg Order Value MoM",
            value=f"${current['aov']:.2f}",
            delta= round(current['aov'] - previous['aov'],2),
            border= True
        )

    with met3:
        st.metric(
            label="Order Volume MoM",
            value=int(current['orders']),
            delta=int(current['orders'] - previous['orders']),
            border=True
        )
else:
    st.warning("Need at least two months of data to compare KPIs.")





#-----------OVERALL TRENDS-------------
col1,col2,col3 = st.columns([1,2,1],vertical_alignment='center')
with col2:
    st.header(' :material/line_axis: Overall Trends')
col1,col2 = st.columns(2)

tab1,tab2 = st.tabs(["Monthly Revenue","Share of Revenue"])
with tab1:
    st.subheader(":material/bar_chart_4_bars: *Revenue by product category*")
    all_prods = pivot_df['product_category'].unique()
    product_filter = st.multiselect("Filter by Product Type:",all_prods,default=all_prods[0])
    pivot_df_filter = pivot_df.copy()
    if product_filter:
        pivot_df_filter = pivot_df_filter[pivot_df_filter['product_category'].isin(product_filter)]

    pivot_df_agg = pivot_df_filter.groupby(['month','product_category'],as_index=False).agg({'revenue':'sum'})
    
   
    rev_bar = px.bar(pivot_df_agg,x='month',y='revenue',color='product_category',hover_data={'revenue': ":.2f"},height=700,width=950)
    st.plotly_chart(rev_bar)
    rev_bar.update_layout(xaxis_title_font=dict(size=18),yaxis_title_font=dict(size=18),legend=dict(font=dict(size=16)),font=dict(size=16),xaxis=dict(tickfont=dict(size=18)),yaxis=dict(tickfont=dict(size=18)))

with tab2:
    rev_df = pd.read_csv('data/revenue_by_cat.csv')
    st.subheader(':material/donut_large: *Share of total revenue by category*')
    pie = px.pie(rev_df,values="revenue",names="product_category",height=600,width=600)
    pie.update_traces(textfont_size=16)
    pie.update_layout(legend=dict(font=dict(size=16)))
    st.plotly_chart(pie)

#------------AOV OVER TIME-------------------------


aov_df = pd.read_csv('data/daily_aov.csv')

aov_df['order_date'] = pd.to_datetime(aov_df['order_date'])

col1,col2,col3 = st.columns([1,2,1],vertical_alignment='center')
with col2:
    st.header(":material/paid: **AOV over Time** ")
min_date = aov_df['order_date'].min().date()
max_date = aov_df['order_date'].max().date()
#--------SIDEBAR TABS---------------------------


tab1,tab2 = st.sidebar.tabs(['AOV','Revenue Comparison'])

with tab1:

    start_date = st.date_input("Select Start date:",value=min_date,min_value=min_date,max_value=None)
    end_date = st.date_input("Select End date:",value=max_date,min_value=None,max_value=max_date)
aov_df_fl = aov_df[
    (aov_df['order_date'].dt.date >= start_date) &
    (aov_df['order_date'].dt.date <= end_date)]

#aov chart
aov_chart = px.line(aov_df_fl,x='order_date',y='avg_order_value',labels={'order_date':'Date','avg_order_value':'AOV/$'})
st.plotly_chart(aov_chart)



all_df = pd.read_csv('data/revenue_breakdown.csv')

all_df['date'] = pd.to_datetime(all_df['date'])



with tab2:
    time_intervals = {
        "Daily" : lambda x:x.dt.date,
        "Weekly" : lambda x:x.dt.to_period("W").apply(lambda y:y.start_time.date()),
        "Monthly" : lambda x:x.dt.to_period("M").apply(lambda y:y.start_time.date())}

    filter_options = ['Product Category','Product Type']
    filter1 = st.segmented_control("Filter By:",options=filter_options,selection_mode='single',default=filter_options[0])
    get_col = filter1.lower().replace(" ","_")             
    val_select = st.multiselect(f"Choose an Option:", all_df[get_col].unique())
    time_select = st.selectbox("Select Time View:",list(time_intervals.keys()))
    all_df['time_interval'] = time_intervals[time_select](all_df['date'])

    df_filter = all_df.copy()

    if val_select:
        df_filter = df_filter[df_filter[get_col].isin(val_select)]

    
    df_filter_agg = df_filter.groupby(['time_interval',get_col],as_index=False).agg({'revenue':'sum'},color=get_col)



col1,col2,col3 = st.columns([1,2,1],vertical_alignment='center')
with col2:
    st.header(" :material/stacked_line_chart: Revenue comparison")

plot_line = px.line(df_filter_agg,x='time_interval',y='revenue',labels={'time_interval': 'Time','revenue':'Revenue/$'},color=get_col)
plot_line.update_layout(xaxis_title_font=dict(size=16),yaxis_title_font=dict(size=16),legend=dict(font=dict(size=12)),font=dict(size=14))

plot_line.update_traces(line=dict(width=2),connectgaps=True)

plot_line.update_layout(xaxis_title="Time Period",yaxis_title="Revenue ($)",font=dict(family="Arial", size=12),
plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))


st.plotly_chart(plot_line)
