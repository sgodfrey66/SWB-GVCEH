# run as streamlit run ./dashboard/mockup.py from the github repo parent dir
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, time
import plotly.express as px
import pydeck as pdk
import altair as alt
import numpy as np
import gvceh_functions as gvceh
from PIL import Image

# set page layout
st.set_page_config(layout="wide")

# initialize streamlit containers
header = st.container()
aggregations = st.container()
sidebar = st.container()

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            tbody th {display:none}
            .blank {display:none}
            </style>
            """

# inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

# import data (this is only twitter for now)
dsource_dict = gvceh.get_data()

# import the help dictionary
readme = gvceh.tooltips()


with sidebar:
	# data source - twitter or reddit
	# st.sidebar.header('1. Data')
	# option = st.sidebar.selectbox('Select a data source',
	# 	('Twitter', 'Reddit'),
	# 	key='saanich',
	# 	help=readme['data_source'])
	option = 'Twitter'
	use_df = dsource_dict[option]

	st.sidebar.header('1. Date Range')
	scol1, scol2 = st.sidebar.columns(2)

	start_date = scol1.date_input(
			"Start Date",
			value=use_df['created_at'].min().date(),
			max_value=datetime.now(),
		)

	end_date = scol2.date_input(
			"End Date",
			value=use_df['created_at'].max().date(),
			max_value=datetime.now(),
		)

	if start_date > end_date:
	    st.sidebar.error('Error: End date must be on or after the start date.')

	priorperiod_flag = st.sidebar.checkbox(
	        "Prior period comparison", value=False, help=readme['prior_period']
	    )

	if priorperiod_flag:
		prior_start_date, prior_end_date = gvceh.get_prior_period(start_date, end_date)
		st.sidebar.write('Prior period is from', prior_start_date, 'to', prior_end_date, '.')


	st.sidebar.header('2. Top Influencer Tweets')
	displaytweets_flag = st.sidebar.checkbox('Display tweets by top influencers', value=False, help=readme['top_influencers'])


	st.sidebar.header('3. User Search Options')
	flag1, flag2 = st.sidebar.columns(2)
	influencer_flag = flag1.checkbox('Influencers', value=False)
	organization_flag = flag2.checkbox('Organizations', value=False)
	options_selected = []

	if influencer_flag is False and organization_flag is False:
		options_selected = []
	elif influencer_flag and organization_flag:
		appendix_ab_persons = pd.read_csv('./appendices/abpersons.csv')
		appendix_ab_persons = appendix_ab_persons["Influencers"].str.strip().unique()
		appendix_ab_persons = appendix_ab_persons.tolist()
		appendix_ab_orgs = pd.read_csv('./appendices/aborganizations.csv')
		appendix_ab_orgs = appendix_ab_orgs["Organizations"].str.strip().unique()
		appendix_ab_orgs = appendix_ab_orgs.tolist()
		ab_options_cat = appendix_ab_persons + appendix_ab_orgs
		options_selected = st.sidebar.multiselect('Select specific influencers/organizations:', ab_options_cat)
	elif influencer_flag:
		appendix_ab_persons = pd.read_csv('./appendices/abpersons.csv')
		ab_options_cat = appendix_ab_persons["Influencers"].str.strip().unique()
		options_selected = st.sidebar.multiselect('Select specific influencers:', ab_options_cat)
	else:
		appendix_ab_orgs = pd.read_csv('./appendices/aborganizations.csv')
		ab_options_cat = appendix_ab_orgs["Organizations"].str.strip().unique()
		options_selected = st.sidebar.multiselect('Select specific organizations:', ab_options_cat)

	# filter dataframe based on user options
	current_df, prior_df = gvceh.get_frames(start_date, end_date, use_df)
	current_df, prior_df = gvceh.filter_by_search_options(current_df, prior_df, options_selected)
	sentiments_by_category = gvceh.agg_sentiments_by_category(current_df, prior_df)
	image = Image.open('./dashboard/branding.png')

	# additions to sidebar after user input
	st.sidebar.header('4. Download Data')
	st.sidebar.download_button(
		label="Download data as CSV",
		data=use_df.to_csv().encode('utf-8'),
		file_name='twitter.csv'
	)


with header:

	a1, a2 = st.columns([2, 1])
	a1.title('Homelessness in Greater Victoria')
	a1.markdown('''This dashboard gives a sense of the sentiment around homelessness in the Greater Victoria area. 
	Data is collected from Twitter daily and a relevancy model actively filters out irrelevant tweets. Further 
	documentation and source code can be found at: https://github.com/Statisticians-Without-Borders-GVCEH/SWB-GVCEH''')
	a2.image(image)

	st.subheader('Summary')
	kpi1, kpi2, kpi3 = st.columns(3)
	if priorperiod_flag:
		kpi1.metric(label = "Total Tweets", value= f"{current_df['tweet_id'].nunique():,}", delta = f"{current_df['tweet_id'].nunique() - prior_df['tweet_id'].nunique():,}")
		kpi2.metric(label="Unique Users", value= f"{current_df['username'].nunique():,}", delta = f"{current_df['username'].nunique() - prior_df['username'].nunique():,}")
		kpi3.metric(label="Unique Locations", value= f"{current_df['search_neighbourhood'].nunique():,}", delta = f"{current_df['search_neighbourhood'].nunique() - prior_df['search_neighbourhood'].nunique():,}")
	else:
		kpi1.metric(label = "Total Tweets", value= f"{current_df['tweet_id'].nunique():,}")
		kpi2.metric(label="Unique Users", value= f"{current_df['username'].nunique():,}")
		kpi3.metric(label="Unique Locations", value= f"{current_df['search_neighbourhood'].nunique():,}")

	if not current_df.empty:
		# 1. Graph of tweets per day historically
		st.subheader('Tweets Per Day')
		tweets_per_day = current_df.groupby([current_df['created_at'].dt.date]).tweet_id.nunique()

		st.download_button(
			label="Download results as CSV",
			data=tweets_per_day.to_csv().encode('utf-8'),
			file_name='tweets_per_day.csv')

		fig_0 = px.line(tweets_per_day, x=tweets_per_day.index, y="tweet_id",
			labels={"tweet_id":"Number of Tweets", "created_at":"Date"})
		fig_0.update_traces(line_color='#BF4C41')
		st.plotly_chart(fig_0, use_container_width=True)


		# whitespace
		n = 0
		while n < 4:
			a1.write('')
			n = n + 1

		a3, a4 = st.columns(2)


		# 2. Top Influencers
		a3.subheader('Top Influencers')
		current_influencers = gvceh.top_influencers(current_df)
		if displaytweets_flag:
			a3.table(current_df.loc[current_df['username'].isin(current_influencers.iloc[0:5]['username'])][
						 ['username', 'text']].sample(n=5))

		fig_3 = px.bar(current_influencers.iloc[0:5], x='username', y='score',
			labels={'username': 'Username', "score": 'Score'},
			color_discrete_sequence=['#000080'])
		a3.plotly_chart(fig_3)

		# 3. Sentiment Scores Aggregated by Category, with prior period comparison
		a4.subheader('Sentiment Scores')
		if priorperiod_flag:
			fig_1 = px.bar(sentiments_by_category, x='Sentiment', y=['Current', 'Prior'],
							   barmode='group', color_discrete_sequence=['#000080', '#8c9e5e'] * 3)
			a4.plotly_chart(fig_1)
		else:
			fig_2 = px.bar(sentiments_by_category, x='Sentiment', y='Current', color_discrete_sequence=['#000080'] * 3)
			a4.plotly_chart(fig_2)



		# 5. Viewing a random sample of tweets for sentiment categories
		st.subheader('Sample of Tweets' if option == 'Twitter' else 'Sample of Posts')
		choice = st.selectbox('Choose a sentiment', ['Negative', 'Neutral', 'Positive'])
		st.table((current_df.loc[current_df.sentiment == choice].sample(n=6))[['username', 'text', 'sentiment']])
	else:
		st.write('No tweets found for the selected categories.')


############################################################################################## EOF ##############################################################################################

