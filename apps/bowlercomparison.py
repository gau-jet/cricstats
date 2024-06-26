import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from apps import utils

def app():
    utils.header()
    series = utils.getSeries()
    table_header_str = f"""<h3 style='text-align: center; color: white;'>{series} - Bowler Comparison</h3>"""
    phase_list = ['ALL','Powerplay',
     'Middle',
     'Death'    
     ]
    
    del_df = utils.load_deliveries_data()
    match_df = utils.load_match_data()
    player_df = utils.return_df("data/Player Profile.csv")
    

    merged_df = utils.return_combined_matchdf(del_df,match_df)   
    batting_merged_df = pd.merge(merged_df, player_df[['Player_Name','batting_style']], left_on='batsman', right_on='Player_Name', how='left')
    batting_merged_df.drop(['Player_Name'], axis=1, inplace=True)       
    comb_df = pd.merge(batting_merged_df, player_df[['Player_Name','bowling_style']], left_on='bowler', right_on='Player_Name', how='left')
    comb_df.drop(['Player_Name'], axis=1, inplace=True)
    
    #comb_df = comb_df[['id' , 'inning' , 'batting_team' , 'bowling_team' , 'over' , 'ball' , 'total_runs' , 'is_wicket' , 'player_dismissed' , 'venue']]
    #comb_df = comb_df.replace(np.NaN, 0)
    #st.write(comb_df.head(10))
    
       
    bowling_type_list = comb_df['bowling_style'].dropna().unique()
    batting_style_list = comb_df['batting_style'].unique()
    season_list = utils.getSeasonList(comb_df)
    start_season = min(season_list)    
    end_season = max(season_list)
    venue_list = utils.getVenueList(comb_df)
    #st.write(comb_df['batting_style'].unique())
    #na_df = comb_df[comb_df['bowling_style'].isna()]
    #st.write(na_df)
    
    with st.form("my_form"):
        st.markdown(table_header_str, unsafe_allow_html=True)
        #DEFAULT_BATSMAN = 'Pick a style'
        DEFAULT = 'Pick a style'
        DEFAULT_STYLE = 'ALL'
        bowling_type = utils.selectbox_with_default(st,'Select bowler type *',sorted(bowling_type_list),DEFAULT)    
        col1, col2 = st.columns(2)
        with col1:
            phase = st.selectbox('Select phase',phase_list)
        with col2:    
            venue = utils.selectbox_with_default(st,'Select Venue',sorted(venue_list),DEFAULT_STYLE)
        batting_style = utils.selectbox_with_default(st,'Select batting hand',sorted(batting_style_list),DEFAULT_STYLE)    
        
        col1, col2 = st.columns(2)
        with col1:
            start_year, end_year = st.select_slider('Season',options=season_list, value=(start_season, end_season))
        with col2:    
            min_balls = st.number_input('Min. Balls',min_value=20,value=100,format='%d')
        submitted = st.form_submit_button("Show Stats")
        title_alignment= """   <style>  .css-1p05t8e {   border-width : 0    }    </style>   """
        st.markdown(title_alignment, unsafe_allow_html=True)        
    
    if submitted:       
        filtered_df = utils.getSeasonDataFrame(comb_df,start_year,end_year)
        if bowling_type != DEFAULT:
            filtered_df = utils.getSpecificDataFrame(filtered_df,'bowling_style',bowling_type) 
        else:
            st.error('Please select bowler type')
            return
        if venue != DEFAULT_STYLE:
            filtered_df = utils.getSpecificDataFrame(filtered_df,'venue',venue)
        if not filtered_df.empty: 
            if batting_style != DEFAULT_STYLE:
                #filtered_df = utils.getSeasonDataFrame(filtered_df,start_year,end_year)
                filtered_df = utils.getSpecificDataFrame(filtered_df,'batting_style',batting_style)             
           
            if not filtered_df.empty:  
                
               # st.write(filtered_df)
                #grpbyList = 'bowler'
                filtered_df['isBowlerWk'] = filtered_df.apply(lambda x: utils.is_wicket(x['player_dismissed'], x['dismissal_kind']), axis = 1)
                if not filtered_df.empty:
                    if phase != 'ALL':
                        grpbyList = ['bowler','phase']
                    else:
                         grpbyList = ['bowler']
                player_df = utils.getPlayerStatistics(filtered_df,grpbyList)
                #st.table(player_df);            
                player_df.reset_index(drop=True,inplace=True)
                
                if phase != 'ALL':
                    player_df = utils.getSpecificDataFrame(player_df,'phase',phase)
                if not player_df.empty:
                    player_df = utils.getMinBallsFilteredDF(player_df,min_balls)
                #st.write(player_df)
                #return
                if not player_df.empty:
                    sort_by_list = ['Dismissals']
                    sort_asc_order = [False]
                    topbowler_df = utils.getTopRecordsDF(player_df,sort_by_list,sort_asc_order,20)
                    #topSRbatsman_df = getTopRecordsDF(player_df,'Runs',10)
                    
                #st.table(topbowler_df)          
                #plotScatterGraph(topSRbowlers_df,'SR','Eco','StrikeRate','EconomyRate')
                #topbowlers_df = getTopRecordsDF(player_df,'dismissals',15)
                    utils.plotScatterGraph(topbowler_df,'Boundary%','Dot%','Boundary Ball %','Dot Ball %','bowler')            
                    utils.plotScatterGraph(topbowler_df,'Eco','SR','Economy','Wicket Rate','bowler')
                else:
                    st.subheader('No Data Found!')
            else:
                st.subheader('No Data Found!')    
        else:
            st.subheader('No Data Found!')    