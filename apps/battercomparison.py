import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from apps import utils

def app():
    utils.header(st)
    st.title('Batsman Comparison')    
    
    phase_list = ['Powerplay',
     'Middle',
     'Death'    
     ]
    
    del_df = utils.return_df("data/IPL Ball-by-Ball 2008-2022.csv")
    match_df = utils.return_df("data/IPL Matches 2008-2022.csv")
    player_df = utils.return_df("data/Player Profile.csv")
    

    merged_df = pd.merge(del_df, match_df, on = 'id', how='left')
    merged_df.rename(columns = {'id':'match_id'}, inplace = True)    
    batting_merged_df = pd.merge(merged_df, player_df[['Player_Name','batting_style']], left_on='batsman', right_on='Player_Name', how='left')
    batting_merged_df.drop(['Player_Name'], axis=1, inplace=True)       
    comb_df = pd.merge(batting_merged_df, player_df[['Player_Name','bowling_style']], left_on='bowler', right_on='Player_Name', how='left')
    comb_df.drop(['Player_Name'], axis=1, inplace=True)
    
    comb_df=utils.replaceTeamNames (comb_df)

    #comb_df = comb_df[['id' , 'inning' , 'batting_team' , 'bowling_team' , 'over' , 'ball' , 'total_runs' , 'is_wicket' , 'player_dismissed' , 'venue']]
    #comb_df = comb_df.replace(np.NaN, 0)
    #st.write(comb_df.head(10))
    
       
    bowling_type_list = comb_df['bowling_style'].dropna().unique()
    batting_style_list = comb_df['batting_style'].unique()
    season_list = comb_df['Season'].unique()
    #st.write(comb_df)
    
    #DEFAULT_BATSMAN = 'Pick a style'
    DEFAULT = 'Pick a style'
    batting_style = utils.selectbox_with_default(st,'Select batting hand',sorted(batting_style_list),DEFAULT)    
    phase = st.selectbox('Select phase',phase_list)
    bowling_type = utils.selectbox_with_default(st,'Select bowler type',sorted(bowling_type_list),DEFAULT)
    
    col1, col2 = st.columns(2)
    with col1:
        start_year, end_year = st.select_slider('Season',options=season_list, value=(2008, 2022))
    with col2:    
        min_balls = st.number_input('Min. Balls',min_value=20,value=40,format='%d')
        
    if batting_style != DEFAULT:       
        filtered_df = utils.getSpecificDataFrame(comb_df,'batting_style',batting_style,start_year,end_year)
        
        if bowling_type != DEFAULT:
            filtered_df = utils.getSpecificDataFrame(filtered_df,'bowling_style',bowling_type,start_year,end_year)             
       
        if filtered_df.empty:
            st.subheader('No Data Found!')
        if not filtered_df.empty:  
            
           # st.write(filtered_df)
            #grpbyList = 'bowler'
            filtered_df['isBowlerWk'] = filtered_df.apply(lambda x: utils.is_wicket(x['player_dismissed'], x['dismissal_kind']), axis = 1)
            player_df = utils.getPlayerStatistics(filtered_df,['batsman','phase'])
            #st.table(player_df);            
            player_df.reset_index(drop=True,inplace=True)
            player_df = utils.getSpecificDataFrame(player_df,'phase',phase)
            if not player_df.empty:
                player_df = utils.getMinBallsFilteredDF(player_df,min_balls)
            #st.write(player_df)
            #return
            if not player_df.empty:
                sort_by_list = ['Runs']
                sort_asc_order = [False]
                topSRbatsman_df = utils.getTopRecordsDF(player_df,sort_by_list,sort_asc_order,15)
                #topSRbatsman_df = getTopRecordsDF(player_df,'Runs',10)
                
                      
            #plotScatterGraph(topSRbowlers_df,'SR','Eco','StrikeRate','EconomyRate')
            #topbowlers_df = getTopRecordsDF(player_df,'dismissals',15)
            utils.plotScatterGraph(topSRbatsman_df,'Boundary%','Dot%','Boundary Ball %','Dot Ball %')            
            utils.plotScatterGraph(topSRbatsman_df,'SR','BPD','Strike Rate','Balls Per Dismissal')
           