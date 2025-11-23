import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hotel Review Dashboard", layout="wide")
st.title("Hotel Reviews Dashboard")

df = pd.read_csv("hotel_reviews_edited.csv")

# ======================= SIDEBAR FILTERS =======================
st.sidebar.header("Filters")

years = st.sidebar.multiselect("Review Year", sorted(df['Review Year'].dropna().unique()))
if years: df = df[df['Review Year'].isin(years)]

cities = st.sidebar.multiselect("City", sorted(df['City'].dropna().unique()))
if cities: df = df[df['City'].isin(cities)]

sentiments = st.sidebar.multiselect("Sentiment Label", sorted(df['Sentiment Label'].dropna().unique()))
if sentiments: df = df[df['Sentiment Label'].isin(sentiments)]

rtc = st.sidebar.multiselect("Room Type Category", sorted(df['Room Type Category'].dropna().unique()))
if rtc: df = df[df['Room Type Category'].isin(rtc)]

min_s, max_s = float(df['Average Score'].min()), float(df['Average Score'].max())
score_range = st.sidebar.slider("Average Score Range", min_s, max_s, (min_s, max_s))
df = df[(df['Average Score'] >= score_range[0]) & (df['Average Score'] <= score_range[1])]

# ======================= HELPER FUNCTIONS =======================
def top20(df_, group_col, value_col, agg='mean'):
    if agg == 'sum':
        return df_.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(20).reset_index()
    return df_.groupby(group_col)[value_col].mean().sort_values(ascending=False).head(20).reset_index()

def fill_month_insights(figures, needed, month_insights):
    for f in month_insights:
        if len(figures) >= needed: break
        figures.append(f)
    return figures

# ======================= TABS =======================
tab1, tab2, tab3, tab4 = st.tabs([
    "⭐ Hotel Scores",
    "🎭 Sentiment Analysis",
    "🌆 City Analysis",
    "🏆 Hotel Popularity Score"
])

# ====================================== TAB 1: Hotel Scores
with tab1:
    st.header("Hotel Scores")
    figs = []

    figs.append(px.bar(top20(df, 'Hotel Name', 'Average Score'),
                       x='Hotel Name', y='Average Score', text_auto=True,
                       title="Top 20 Hotels by Avg Score").update_layout(xaxis_tickangle=-45))

    figs.append(px.treemap(top20(df, 'Hotel Name', 'Average Score', 'sum'),
                           path=['Hotel Name'], values='Average Score',
                           title="Treemap: Total Score Share (Top 20 Hotels)"))

    yearly_trend = px.line(df.groupby('Review Year')['Average Score'].mean().reset_index(),
                           x='Review Year', y='Average Score', markers=True,
                           title="Trend: Avg Score Over Years")
    yearly_trend.update_xaxes(type='category')
    figs.append(yearly_trend)

    figs.append(px.bar(df.groupby('Hotel Name')['Total Number of Reviews Reviewer Has Given']
                       .mean().reset_index().sort_values('Total Number of Reviews Reviewer Has Given', ascending=False).head(20),
                       x='Hotel Name', y='Total Number of Reviews Reviewer Has Given',
                       text_auto=True, title="Top 20 Hotels by Reviewer Activity").update_layout(xaxis_tickangle=-45))

    figs.append(px.bar(top20(df, 'Hotel Name', 'Average Score', 'sum'),
                       x='Hotel Name', y='Average Score',
                       text_auto=True, title="Total Score for Top 20 Hotels"))

    figs.append(px.bar(df.groupby('Room Type Category')['Average Score'].mean().reset_index(),
                       x='Room Type Category', y='Average Score', text_auto=True,
                       title="Average Score by Room Type Category"))

    figs.append(px.bar(df.groupby('City')['Average Score'].mean().reset_index()
                       .sort_values('Average Score', ascending=False).head(20),
                       x='City', y='Average Score', text_auto=True,
                       title="Top Cities by Average Score"))

    monthly_avg = df.groupby('Review Month')['Average Score'].mean().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_avg.columns = ['Review Month', 'Average Score']
    f_month1 = px.line(monthly_avg, x='Review Month', y='Average Score',
                       title="Monthly Avg Score Trend", markers=True)

    monthly_dist = df['Review Month'].value_counts().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_dist.columns = ['Review Month', 'Count']
    f_month2 = px.bar(monthly_dist, x='Review Month', y='Count', text_auto=True,
                      title="Review Count per Month")

    figs = fill_month_insights(figs, 9, [f_month2])

    total_charts = len(figs)
    charts_per_row = 3
    for start in range(0, total_charts, charts_per_row):
        row = st.columns(charts_per_row)
        for i in range(charts_per_row):
            if start + i < total_charts:
                row[i].plotly_chart(figs[start + i], use_container_width=True)

    st.plotly_chart(f_month1, use_container_width=True)

# ====================================== TAB 2: Sentiment Analysis
with tab2:
    st.header("Sentiment Analysis")
    figs = []

    dist = df['Sentiment Label'].value_counts().reset_index()
    dist.columns = ['Sentiment', 'Count']
    figs.append(px.pie(dist, names='Sentiment', values='Count', title="Sentiment Distribution", hole=0.35))

    figs.append(px.bar(df.groupby('Sentiment Label')['Average Score'].mean().reset_index(),
                       x='Sentiment Label', y='Average Score', text_auto=True,
                       title="Average Score per Sentiment"))

    figs.append(px.bar(df.groupby(['City', 'Sentiment Label']).size().reset_index(name='Count')
                       .sort_values('Count', ascending=False).head(20),
                       x='City', y='Count', text_auto=True, color='Sentiment Label',
                       title="Top Cities by Sentiment Count"))

    figs.append(px.line(df.groupby(['Review Year', 'Sentiment Label']).size().reset_index(name='Count'),
                        x='Review Year', y='Count', color='Sentiment Label',
                        markers=True, title="Sentiment Trend Over Years").update_xaxes(type='category')
                        )
# ========
    top_hotels = df['Hotel Name'].value_counts().head(50).index.tolist() 
    figs.append(px.sunburst(df[df['Hotel Name'].isin(top_hotels)],
                            path=['Sentiment Label', 'City', 'Hotel Name'],
                            title="Sentiment > City > Hotel Breakdown"))

    sentiment_ratio = (df['Sentiment Label'].value_counts(normalize=True) * 100).reset_index()
    sentiment_ratio.columns = ['Sentiment', 'Percentage']
    figs.append(px.bar(sentiment_ratio, x='Sentiment', y='Percentage', text_auto=True,
                       title="Sentiment Percentage Ratio (%)"))

    monthly_sent_total = df['Review Month'].value_counts().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_sent_total.columns = ['Review Month', 'Count']
    f_month2 = px.bar(monthly_sent_total, x='Review Month', y='Count',
                      text_auto=True, title="Sentiment Count per Month")

    figs = fill_month_insights(figs, 9, [f_month2])

    total_charts = len(figs)
    charts_per_row = 3
    for start in range(0, total_charts, charts_per_row):
        row = st.columns(charts_per_row)
        for i in range(charts_per_row):
            if start + i < total_charts:
                row[i].plotly_chart(figs[start + i], use_container_width=True)

    avg_h_sent = df.groupby(['Hotel Name', 'Sentiment Label'])['Average Score'].mean().reset_index()
    top_h = avg_h_sent.groupby('Hotel Name')['Average Score'].mean().sort_values(ascending=False).head(40).index
    top_hotels_chart = px.bar(avg_h_sent[avg_h_sent['Hotel Name'].isin(top_h)],
                              x='Hotel Name', y='Average Score', color='Sentiment Label',
                              title="Avg Score per Sentiment for Top Hotels")
    top_hotels_chart.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(top_hotels_chart, use_container_width=True)

    monthly_sent = df.groupby(['Review Month', 'Sentiment Label']).size().reset_index(name='Count')
    monthly_sent_chart = px.line(monthly_sent, x='Review Month', y='Count', color='Sentiment Label',
                                 title="Monthly Sentiment Trend", markers=True)
    st.plotly_chart(monthly_sent_chart, use_container_width=True)

# ====================================== TAB 3: City Analysis
with tab3:
    st.header("City Analysis")
    figs = []

    figs.append(px.bar(top20(df, 'City', 'Review Total Positive Word Counts', 'sum'),
                       x='City', y='Review Total Positive Word Counts', text_auto=True,
                       title="Top 20 Cities by Total Positive Words").update_layout(xaxis_tickangle=-45))

    city_counts = df['City'].value_counts().reset_index()
    city_counts.columns = ['City', 'Count']
    figs.append(px.histogram(city_counts, x='City', y='Count',
                             title="Histogram of City Review Counts"))

    city_stats = df.groupby('City')['Average Score'].agg(['mean', 'std']).reset_index()
    city_stats = city_stats.sort_values('mean', ascending=False).head(20)
    figs.append(px.bar(city_stats, x='City', y='mean', error_y='std', text_auto=True,
                       title="City Avg Score").update_layout(xaxis_tickangle=-45))

    ct = df.groupby(['City', 'Room Type Category'])['Average Score'].mean().reset_index()
    top_city_list = df['City'].value_counts().head(8).index.tolist()
    figs.append(px.sunburst(ct[ct['City'].isin(top_city_list)],
                            path=['City', 'Room Type Category'],
                            values='Average Score',
                            title="City > Room Type > Avg Score"))

    city_rev_act = df.groupby('City')['Total Number of Reviews Reviewer Has Given'].mean().reset_index()
    figs.append(px.bar(city_rev_act.sort_values('Total Number of Reviews Reviewer Has Given',
                                                ascending=False).head(20),
                       x='City', y='Total Number of Reviews Reviewer Has Given',
                       text_auto=True, title="Avg Reviewer Activity per City").update_layout(xaxis_tickangle=-45))

    figs.append(px.pie(city_counts.head(10), names='City', values='Count',
                       hole=0.3, title="Top 10 Cities by Review Share"))

    monthly_city_cnt = df['Review Month'].value_counts().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_city_cnt.columns = ['Review Month', 'Count']
    f_month2 = px.bar(monthly_city_cnt, x='Review Month', y='Count', text_auto=True,
                      title="Monthly City Review Count")

    figs = fill_month_insights(figs, 9, [f_month2])

    total_charts = len(figs)
    charts_per_row = 3
    for start in range(0, total_charts, charts_per_row):
        row = st.columns(charts_per_row)
        for i in range(charts_per_row):
            if start + i < total_charts:
                row[i].plotly_chart(figs[start + i], use_container_width=True)

    monthly_city = df.groupby('Review Month')['Average Score'].mean().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_city.columns = ['Review Month', 'Average Score']
    f_month1 = px.line(monthly_city, x='Review Month', y='Average Score',
                       title="Monthly City Avg Score Trend", markers=True)
    st.plotly_chart(f_month1, use_container_width=True)

# ====================================== TAB 4: Hotel Popularity Score
with tab4:
    st.header("🏆 Hotel Popularity Score")
    figs = []

    figs.append(px.bar(top20(df, 'Hotel Name', 'Hotel Popularity Score'),
                       x='Hotel Name', y='Hotel Popularity Score', text_auto=True,
                       title="Top 20 Hotels by Popularity Score").update_layout(xaxis_tickangle=-45))

    figs.append(px.treemap(top20(df, 'Country', 'Hotel Popularity Score', 'mean'),
                           path=['Country'], values='Hotel Popularity Score',
                           title="Top Countries by Hotel Popularity Score"))

    figs.append(px.bar(df.groupby('Room Type Category')['Hotel Popularity Score'].mean().reset_index(),
                       x='Room Type Category', y='Hotel Popularity Score', text_auto=True,
                       title="Popularity Score by Room Type Category"))

    figs.append(px.bar(top20(df, 'Hotel Name', 'Hotel Popularity Score', 'sum'),
                       x='Hotel Name', y='Hotel Popularity Score', text_auto=True,
                       title="Top 20 Hotels by Total Popularity Score (SUM)").update_layout(xaxis_tickangle=-45))

    monthly_pop_cnt = df['Review Month'].value_counts().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_pop_cnt.columns = ['Review Month', 'Count']
    f_month2 = px.bar(monthly_pop_cnt, x='Review Month', y='Count', text_auto=True,
                      title="Monthly Popularity Count")
    figs = fill_month_insights(figs, 9, [f_month2])

    total_charts = len(figs)
    charts_per_row = 3
    for start in range(0, total_charts, charts_per_row):
        row = st.columns(charts_per_row)
        for i in range(charts_per_row):
            if start + i < total_charts:
                row[i].plotly_chart(figs[start + i], use_container_width=True)

    popularity_bar = px.bar(top20(df, 'Hotel Name', 'Hotel Popularity Score'),
                             x='Hotel Name', y='Hotel Popularity Score',
                             text_auto=True,
                             title="Popularity Score by Hotel")
    st.plotly_chart(popularity_bar, use_container_width=True)

    monthly_pop = df.groupby('Review Month')['Hotel Popularity Score'].mean().reindex(range(1, 13), fill_value=0).reset_index()
    monthly_pop.columns = ['Review Month', 'Hotel Popularity Score']
    f_month1 = px.line(monthly_pop, x='Review Month', y='Hotel Popularity Score',
                       title="Monthly Popularity Trend", markers=True)
    st.plotly_chart(f_month1, use_container_width=True)
