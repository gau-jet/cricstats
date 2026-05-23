import sys
import streamlit as st
import numpy as np 
import pandas as pd 
import math
import matplotlib.pyplot as plt
import requests, zipfile, io

def download_url(zip_file_url, save_path):
    req = requests.get(zip_file_url)
    z = zipfile.ZipFile(io.BytesIO(req.content))   
    file = z.extractall(save_path)
        

def header():
    snippet = """
    <div style="display: flex; justify-content: space-between">
        <div>🡠 Check the sidebar for more options</div>        
    </div>
    """
    st.markdown(snippet, unsafe_allow_html=True)

def getSeries():
    return st.query_params.get("series", "IPL")

def load_deliveries_data():
    
    series = getSeries()

    if series == 'T20I':
        del_df = return_df("data/T20Ideliveries.csv")
    elif series == 'WT20':
        del_df = return_df("data/WT20deliveries.csv")
    else:
        del_df = return_df("data/deliveries.csv")        
    return del_df


def load_match_data():
    series = getSeries()

    if series == 'T20I':        
        match_df = return_df("data/T20Imatches.csv")
    elif series == 'WT20':
        match_df = return_df("data/WT20matches.csv")
    else:        
        match_df = return_df("data/matches.csv")
    return match_df

def load_player_data():
    
    player_df = return_df("data/Player Profile.csv")
    return player_df

#@st.cache(allow_output_mutation=True,suppress_st_warning=True,ttl=3600*24,show_spinner=True)    
@st.cache_data(ttl="1d")    
def return_df(f):        
    try:
        try:
            df = pd.read_csv(f, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(f, encoding="latin-1")
        return df.copy()
    except Exception:
        st.write("Could not read file " + f)
        st.error(sys.exc_info())
        return pd.DataFrame()

@st.cache_data(ttl="1d")    
def return_combined_matchdf(del_df,match_df):        
    try:
        comb_df = pd.merge(del_df, match_df, on = 'id', how='left')
        comb_df.rename(columns = {'id':'match_id'}, inplace = True)                  
        comb_df= replaceTeamNames(comb_df)
        return comb_df
    except Exception:
        st.write("Could not combine match and delivery dataframe")
        st.error(sys.exc_info())
        return pd.DataFrame()

#@st.cache_data(ttl=3600*24,show_spinner=True)
@st.cache_data(ttl="1d")
def getBatsmanList(df):    
    # Check if display_name exists, if not return batsman names
    if 'display_name' not in df.columns:
        return sorted(df['batsman'].unique())
        
    # Get all unique batsmen with their display names
    batsman_df = df[['batsman', 'display_name']].drop_duplicates()
    missing_names = batsman_df[batsman_df['display_name'].isna()]['batsman'].unique()
    
    if len(missing_names) > 0:
        st.warning("⚠️ Players missing display names in Player Profile:")
        st.table(pd.DataFrame({'Player Name': missing_names}))
    
    # Return either display_name if available, otherwise batsman name
    return sorted(df['display_name'].dropna().unique())

def getPlayerName(player,player_df):    
    df = player_df[(player_df.display_name == player)].reset_index()    
    return df['Player_Name'][0]
    
#@st.cache_data(ttl=3600*24,show_spinner=True)
@st.cache_data(ttl="1d")    
def getBowlerList(df):    
    # Check if display_name exists, if not return bowler names
    if 'display_name' not in df.columns:
        return sorted(df['bowler'].unique())
        
    # Get all unique bowlers with their display names
    bowler_df = df[['bowler', 'display_name']].drop_duplicates()
    missing_names = bowler_df[bowler_df['display_name'].isna()]['bowler'].unique()
    
    if len(missing_names) > 0:
        st.warning("⚠️ Players missing display names in Player Profile:")
        st.table(pd.DataFrame({'Player Name': missing_names}))
    
    # Return either display_name if available, otherwise bowler name
    return sorted(df['display_name'].dropna().unique())

#@st.cache_data(ttl=3600*24,show_spinner=True)
@st.cache_data(ttl="1d")    
def getSeasonList(df):
    #return pd.DataFrame(sorted({2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022}))
    return sorted(df['season'].unique())
        

@st.cache_data(ttl="1d")    
def getVenueList(df):
    return sorted(df['venue'].unique())
        
def getMatchList(df,year,venue):    
    df = df[(df.season == year)]
    if venue != 'ALL':
        df = df[(df.venue == venue)]    
    query_params = st.query_params
    series = query_params['series']
    
    if series == 'T20I':  
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        #df["date"] = df["date"].astype('datetime64[ns]')
        df = df.sort_values(by='date',ascending = False).reset_index()
    else:        
        df = df.sort_values(by='id',ascending = False).reset_index()
    
    
    df['match_string'] = df.id.astype(str)+"-"+df.team1.astype(str)+" Vs "+df.team2.astype(str)+" at "+df.venue
    #st.write(df['match_string'])
    return df['match_string']
    
def replaceTeamNames(df):

    team_name_mappings = {'Delhi Daredevils':'Delhi Capitals','Deccan Chargers':'Sunrisers Hyderabad','Gujarat Lions':'Gujarat Titans','Kings XI Punjab':'Punjab Kings','Rising Pune Supergiants':'Rising Pune Supergiant','Pune Warriors':'Rising Pune Supergiant'} 
    
    for key, value in team_name_mappings.items():
        df['batting_team'] = df['batting_team'].str.replace(key,value)
        df['bowling_team'] = df['bowling_team'].str.replace(key,value)
        df['team1'] = df['team1'].str.replace(key,value)
        df['team2'] = df['team2'].str.replace(key,value)
        df['toss_winner'] = df['toss_winner'].str.replace(key,value)
        df['winner'] = df['winner'].str.replace(key,value)
    return df

def selectbox_with_default(st,text, values, default, sidebar=False):
        func = st.sidebar.selectbox if sidebar else st.selectbox
        return func(text, np.insert(np.array(values, object), 0, default))
        
def getSpecificDataFrame(df,key,value):
        if key:
            df = df[df[key] == value]
        else:
            st.error('No Key Passed in getSpecificDataFrame method')
        return df 

def getSeasonDataFrame(df,start_year=None,end_year=None):
        if start_year:
            df = df[df['season'].between(start_year, end_year)]
        else:
            st.error('Incorrect Start Year')
        return df 

def getTopRecordsDF(df,key,order,maxrows):        
        df = df.sort_values(by=key,ascending = order).head(maxrows).reset_index()
        return df  
        
def phase(over):
    if over <= 6:
        return 'Powerplay'
    elif over <= 15:
        return 'Middle'
    else:
        return 'Death'    
        
def balls_per_dismissal(balls, dismissals):
    if dismissals > 0:
        return balls/dismissals
    else:
        return math.inf 
    
def balls_per_boundary(balls, boundaries):
	if boundaries > 0:
		return balls/boundaries
	else:
		return math.inf
        
def boundary_per_ball(balls, boundaries):
    if boundaries > 0:
        return boundaries/balls
    else:
        #return 1/balls 
        return 0
        
def get_dot_percentage(dots, balls):
    if balls > 0:
        return dots/balls
    else:
        return 0
    
def runs_per_ball(balls, runs_conceeded):
    if balls > 0:
        return runs_conceeded/balls
    else:
        return math.inf
    
def runs_per_dismissal(runs_conceeded, dismissals):
    if dismissals > 0:
        return runs_conceeded/dismissals
    else:
        return math.inf
        
def is_wicket(player_dismissed, dismissal_kind):
    if type(player_dismissed) != str:
        return 0
    elif ~(type(player_dismissed) != str) & (dismissal_kind not in ['run out', 'retired hurt', 'obstructing the field']):
        return 1
    else:
        return 0


def getTeamBattingFirst(t1, t2, toss_winner, toss_decision): 
    if (toss_decision == 'bat'): 
        return toss_winner
    else: 
        if (toss_winner == t1): 
            return t2
        else: 
            return t1

def getTeamBattingSecond(t1, t2, toss_winner, toss_decision): 
    if (toss_decision == 'field'): 
        return toss_winner
    else: 
        if (toss_winner == t1): 
            return t2
        else: 
            return t1

def getMinBallsFilteredDataFrame(df,min_balls):        
        if (df.shape[0] >= min_balls):
            return df
        else:    
            return pd.DataFrame()            
            
def getMinBallsFilteredDF(df,min_balls):        
        df = df[df.Balls >= min_balls]
        return df

def getPerInningsWinCount(df,venue):    
    if not df.empty:
        df['TossWinnerIsWinner'] = df.apply(lambda x: x['toss_winner'] == x['winner'], axis=1)    
        
        df['TeamBattingFirst'] = df.apply(lambda x: getTeamBattingFirst(x['team1'] , x['team2'] , x['toss_winner'] , x['toss_decision']) , axis=1)
        df['TeamBattingSecond'] = df.apply(lambda x: getTeamBattingSecond(x['team1'] , x['team2'] , x['toss_winner'] , x['toss_decision']) , axis=1)
        
        TeamBattingFirstCount = df.apply( lambda x : 1 if x['TeamBattingFirst'] == x['winner']  else 0 , axis=1).sum()  
        TeamBattingSecondCount = df.apply( lambda x : 1 if x['TeamBattingSecond'] == x['winner'] else 0 , axis=1).sum()   
    else:
        TeamBattingFirstCount = 0
        TeamBattingSecondCount = 0
    
    venue_stats_df = {
        'venue':[venue],        
        'Batting 1st-Wins': TeamBattingFirstCount,
        'Batting 2nd-Wins': TeamBattingSecondCount       
      }
    final_df = pd.DataFrame(data=venue_stats_df)  
    return final_df
    #st.write(df['TeamBattingFirstWins'])
            
def getVenueStats(df,venue):
    
    avg_run_per_match = pd.DataFrame(df.groupby(['venue','inning']).total_runs.sum() / df.groupby('venue').match_id.nunique()).reset_index()
    avg_run_per_match.columns = ['venue', 'Inning','AvgRuns']
    avg_wkt_per_match = pd.DataFrame(df.groupby(['venue','inning']).is_wicket.sum() / df.groupby('venue').match_id.nunique()).reset_index()
    avg_wkt_per_match.columns = ['venue','Inning', 'AvgWkts']
    
    avg_run_per_match.drop(['venue'], axis=1, inplace=True) 
    avg_run_per_match_transposed = avg_run_per_match.T
    avg_wk_per_match_transposed = avg_wkt_per_match.T
    
    
    avg_run_per_match_transposed[0]['AvgRuns'] = (round(avg_run_per_match_transposed[0]['AvgRuns'],2))
    avg_run_per_match_transposed[1]['AvgRuns'] = (round(avg_run_per_match_transposed[1]['AvgRuns'],2))
    avg_wk_per_match_transposed[0]['AvgWkts'] = (round(avg_wk_per_match_transposed[0]['AvgWkts'],2))
    avg_wk_per_match_transposed[1]['AvgWkts'] = (round(avg_wk_per_match_transposed[1]['AvgWkts'],2))
    
   
    matches = pd.DataFrame(df.groupby('venue')['match_id'].apply(lambda x: len(list(np.unique(x)))).reset_index()).rename(columns = {'match_id':'NoofMatches'})
    matches.drop(['venue'], axis=1, inplace=True) 
    
    innings_stats_df = {
        'venue':[venue],
        'Matches': matches['NoofMatches'][0],
        'Avg Runs - 1st Innings': [avg_run_per_match_transposed[0]['AvgRuns']],
        'Avg Runs - 2nd Innings': [avg_run_per_match_transposed[1]['AvgRuns']],
        'Avg Wickets - 1st Innings': [avg_wk_per_match_transposed[0]['AvgWkts']],
        'Avg Wickets - 2nd Innings': [avg_wk_per_match_transposed[1]['AvgWkts']]
      }
      
    final_df = pd.DataFrame(data=innings_stats_df)
    
    #final_df = pd.merge(avg_run_per_match , avg_wkt_per_match, on = 'venue')
    
    #final_df = pd.merge(final_df , WinPercentage, on = 'venue')
    #final_df.drop(['venue'], axis=1, inplace=True) 
    
    return final_df

def getTeamStats(df,team):
    df = df[((df.team1 == team) | (df.team2 == team))]
    
    no_of_matches_played = df.match_id.nunique()
    no_of_matches_won = df[(df.winner == team)].match_id.nunique()    
    no_of_matches_tied  = df[(df.result == 'tie')].match_id.nunique()    
    no_of_matches_noresult  = df[(df.result == 'no result')].match_id.nunique()
    no_of_matches_lost  = no_of_matches_played - ( no_of_matches_won + no_of_matches_tied + no_of_matches_noresult)
   
    team_stats_df = {
        'Played': no_of_matches_played,
        'Won': no_of_matches_won,
        'Lost': no_of_matches_lost,
        'Tied': no_of_matches_tied,
        'No Result': no_of_matches_noresult
      }
      
    final_df = pd.DataFrame(data=team_stats_df, index=[0])
   
    return final_df
    

def getBowlingStyleWiseStats(df):
    new_df  = pd.DataFrame(df.groupby(['venue','bowling_style']).ball.count()).rename(columns = {'ball' : 'Balls'}).reset_index()
    new_df  = new_df .merge(pd.DataFrame(df.groupby(['venue','bowling_style']).total_runs.sum()).rename(columns = {'total_runs' : 'Runs'}) , on = ['venue', 'bowling_style'])
    new_df  = new_df .merge(pd.DataFrame(df.groupby(['venue','bowling_style']).is_wicket.sum()).rename(columns = {'is_wicket' : 'Wickets'}), on = ['venue', 'bowling_style'])
    new_df ['BallsPerWicket'] = (round(new_df ['Balls'] / new_df ['Wickets'],2))
    new_df ['RunsPerOver'] = (round(6 * new_df ['Runs'] / new_df ['Balls'],2))
    new_df.drop(['venue'], axis=1, inplace=True)
    new_df.rename(columns = {'bowling_style':'Bowling Style'}, inplace = True)
    return new_df
    
    
def getBowlingStatsforaVenue(df,venue):
    df = df[df.venue == venue]
    new_df = getBowlingStyleWiseStats(df)    
    return new_df.sort_values(by = 'BallsPerWicket', ascending = True) 

def getHighestScore(df):
    runs = pd.DataFrame(df.groupby(['batsman','match_id'])['batsman_runs'].sum().reset_index()).groupby(['batsman','match_id'])['batsman_runs'].sum().reset_index().rename(columns={'batsman_runs':'Match_Runs'})
    return (runs.Match_Runs.max())
    
def getTeamHighestScore(df,team):
    
    df = df[df.batting_team == team]
    
    runs = pd.DataFrame(df.groupby(['batting_team','match_id'])['total_runs'].sum().reset_index()).groupby(['batting_team','match_id'])['total_runs'].sum().reset_index().rename(columns={'total_runs':'Match_Runs'})
    
    return (runs.Match_Runs.max())

def getTeamLowestScore(df,team):
    
    lowest_score =  'NA'
    final_df = pd.DataFrame()
    first_df = df[(df.batting_team == team) & (df.inning == 1)]
    
    second_df = df[(df.batting_team == team) & (df.inning == 2) & (df.win_by != 'wickets')]
    
    if not first_df.empty:
            if not second_df.empty:
                final_df = pd.concat([first_df, second_df], ignore_index=True, sort=False)
            else:
                final_df = first_df
    if not second_df.empty:
            if not first_df.empty:
                final_df = pd.concat([first_df, second_df], ignore_index=True, sort=False)
            else:
                final_df = second_df
    
    if not final_df.empty:
        runs = pd.DataFrame(final_df.groupby(['batting_team','match_id'])['total_runs'].sum().reset_index()).groupby(['batting_team','match_id'])['total_runs'].sum().reset_index().rename(columns={'total_runs':'Match_Runs'})
        #match_id = runs.Match_Runs.min().match_id
        st.write(runs.head(10))
        lowest_score = runs.Match_Runs.min()
    
    return (lowest_score)

def getNoofThirties(df):
    
    runs = pd.DataFrame(df.groupby(['match_id'])['batsman_runs'].sum().reset_index()).rename(columns={'batsman_runs':'Match_Runs'})
    noofthirties= runs['Match_Runs'].apply(lambda x: 1 if x >=30 else 0).sum()
    return (noofthirties)    
    
def getNoofFifties(df):
    
    runs = pd.DataFrame(df.groupby(['match_id'])['batsman_runs'].sum().reset_index()).rename(columns={'batsman_runs':'Match_Runs'})
    nooffifties = runs['Match_Runs'].apply(lambda x: 1 if x >=50 and x <100 else 0).sum()    
    return (nooffifties)
    
def getNoof4Wickets(df):
    
    df = df[~df.dismissal_kind.isin(['run out', 'retired hurt', 'obstructing the field','NA'])]
    #df = df[df.venue == venue]     
    dismissals = pd.DataFrame(df.groupby(['season','match_id'])['player_dismissed'].count()).reset_index().rename(columns = {'player_dismissed':'Dismissals'})
       
    noof4wks = dismissals['Dismissals'].apply(lambda x: 1 if x == 4 else 0).sum()
    return (noof4wks)
    
def getNoof5Wickets(df):
    df = df[~df.dismissal_kind.isin(['run out', 'retired hurt', 'obstructing the field','NA'])]
    dismissals = pd.DataFrame(df.groupby(['match_id'])['player_dismissed'].count()).reset_index().rename(columns = {'player_dismissed':'Dismissals'})
        
    noof5wks = dismissals['Dismissals'].apply(lambda x: 1 if x > 4 else 0).sum()
    return (noof5wks)    
    
def getNoofHundreds(df):
    
    runs = pd.DataFrame(df.groupby(['season','match_id'])['batsman_runs'].sum().reset_index()).rename(columns={'batsman_runs':'Match_Runs'})
    noofhundreds = runs['Match_Runs'].apply(lambda x: 1 if x >=100 else 0).sum()
    
    return (noofhundreds)

# first innings
def innings_1_runs(curr_overs, curr_score, curr_wickets,t1_cum_pb):
    i1p_0 = t1_cum_pb[0]
    i1p_1 = t1_cum_pb[1]
    i1p_2 = t1_cum_pb[2]
    i1p_3 = t1_cum_pb[3]
    i1p_4 = t1_cum_pb[4]
    i1p_6 = t1_cum_pb[5]
    i1p_w = 1

    # initialize runs, wickets
    pred_runs = curr_score
    pred_wks = curr_wickets
    
    # calculate leftover balls
    over_ball = curr_overs
    over_number = int(str(over_ball).split('.')[0])
    ball_number = int(str(over_ball).split('.')[1])
    
    if ball_number >= 6:
        ball_number = 6
    current_balls = over_number*6 + ball_number 
    leftover_balls = 120 - current_balls

    for i in range(leftover_balls):
    
        r_value = np.random.random()

        if r_value <= i1p_0:
            pred_runs += 0
        elif r_value <= i1p_1:
            pred_runs += 1
        elif r_value <= i1p_2:
            pred_runs += 2
        elif r_value <= i1p_3:
            pred_runs += 3
        elif r_value <= i1p_4:
            pred_runs += 4
        elif r_value <= i1p_6:
            pred_runs += 6
        else:
            pred_runs += 0
            pred_wks += 1
            if pred_wks == 10:
                break

    return pred_runs
    
def innings_2_runs(curr_overs, curr_score, curr_wickets, target,t2_cum_pb):
    i2p_0 = t2_cum_pb[0]
    i2p_1 = t2_cum_pb[1]
    i2p_2 = t2_cum_pb[2]
    i2p_3 = t2_cum_pb[3]
    i2p_4 = t2_cum_pb[4]
    i2p_6 = t2_cum_pb[5]
    i2p_w = 1

    # initialize runs, wickets
    pred_runs = curr_score
    pred_wks = curr_wickets
    
    # calculate leftover balls
    over_ball = curr_overs
    over_number = int(str(over_ball).split('.')[0])
    ball_number = int(str(over_ball).split('.')[1])
    
    if ball_number >= 6:
        ball_number = 6
    current_balls = over_number*6 + ball_number 
    leftover_balls = 120 - current_balls

    for i in range(leftover_balls):
    
        r_value = np.random.random()

        if r_value <= i2p_0:
            pred_runs += 0
        elif r_value <= i2p_1:
            pred_runs += 1
        elif r_value <= i2p_2:
            pred_runs += 2
        elif r_value <= i2p_3:
            pred_runs += 3
        elif r_value <= i2p_4:
            pred_runs += 4
        elif r_value <= i2p_6:
            pred_runs += 6
        else:
            pred_runs += 0
            pred_wks += 1
            if pred_wks == 10:
                break
        
        if pred_runs > target:
            break

    return pred_runs

def getMatchid(match_string):
    
    match_string_arr = (match_string.split('-'))
    
    return match_string_arr[0]
 
def getMatchSummaryChart(df,matches_df,matchID): 
    
    venue = matches_df[matches_df.id==int(matchID)].venue.to_string(index=False)
    season = matches_df[matches_df.id==int(matchID)].season.to_string(index=False)
    
    df = df[df.id==int(matchID)]
    
    firstinnings_df = df[df.inning==1]
    secondinnings_df = df[df.inning==2]
    
    firstinnings_df.reset_index(inplace = True, drop = True)
    secondinnings_df.reset_index(inplace = True, drop = True)

    firstinnings_df['cummulative_runs'] = 0
    secondinnings_df['cummulative_runs'] = 0
    #Populate runs for both innings
    total_runs=0
    for i in range( len(firstinnings_df)):
        total_runs += firstinnings_df['total_runs'][i]
        firstinnings_df['cummulative_runs'][i] = total_runs

    total_runs=0
    for i in range(len(secondinnings_df)):
        total_runs += secondinnings_df['total_runs'][i]
        secondinnings_df['cummulative_runs'][i] = total_runs


    #Populate wickets for both innings    
    ball_no_ings1 = [i for i in range(1,len(firstinnings_df)+1)]
    ball_no_ings2 = [i for i in range(1,len(secondinnings_df)+1)]

    wk_index1 = list(firstinnings_df[~firstinnings_df.player_dismissed.isna()].index)
    wk_index2 = list(secondinnings_df[~secondinnings_df.player_dismissed.isna()].index)
    wk_runs1 = list(firstinnings_df[firstinnings_df.index.isin(wk_index1)].cummulative_runs)
    wk_runs2 = list(secondinnings_df[secondinnings_df.index.isin(wk_index2)].cummulative_runs)
           
    plt.figure(figsize = (16, 6))
    plt.style.use('dark_background')
    plt.tight_layout()
    team1 = firstinnings_df.batting_team[0]
    team2 = secondinnings_df.batting_team[0]
    plt.plot(firstinnings_df.index,firstinnings_df.cummulative_runs, linewidth = 3, label = team1)
    plt.plot(secondinnings_df.index,secondinnings_df.cummulative_runs, linewidth = 3, label = team2)

    plt.scatter(wk_index1, wk_runs1, s = 150)
    plt.scatter(wk_index2, wk_runs2, s = 150)


    plt.axvline(x = 36, ls = '--', c = 'g'),
    plt.axvline(x = 90, ls = '--', c = 'g')
    plt.text(16, 1.01, "Powerplay"),
    plt.text(60, 1.01, "Middle Overs"),
    plt.text(105, 1.01, "Death Overs")

    plt.xlabel('Ball Number')
    plt.ylabel('Runs Scored')
    title = "IPL Season",season," Match Summary at ",venue," - Runs progression Chart"
    plt.title(title)
    plt.legend()
    st.pyplot(plt)
 
def getMatchAnanlysis(df,matchid):
    
    ipl_df = df[(df.match_id == int(matchid))]
    
    ipl_df.reset_index(inplace = True, drop = True)
    
    t1 = ipl_df.team1[0]
    t2 = ipl_df.team2[0]
    
    df_ing1 = ipl_df[ipl_df.inning == 1]
    df_ing2 = ipl_df[ipl_df.inning == 2]
    df_ing1.reset_index(inplace = True, drop = True)
    df_ing2.reset_index(inplace = True, drop = True)
    
    first_batting_teamname = df_ing1.batting_team[0]
    second_batting_teamname = df_ing2.batting_team[0]
    #st.write(df_ing1)
    
    df_ing1 = df_ing1.sort_values(by=['over','ball'], ascending = True)
    df_ing2 = df_ing2.sort_values(by=['over','ball'], ascending = True)
    df_ing1.reset_index(inplace = True, drop = True)
    df_ing2.reset_index(inplace = True, drop = True)
    
    
    #return
    t1_outs = df[df.batting_team == t1].is_wicket.sum()
    t2_outs = df[df.batting_team == t2].is_wicket.sum()
    t1_outcomes = df[df.batting_team == t1].total_runs.value_counts()
    t2_outcomes = df[df.batting_team == t2].total_runs.value_counts()
    
        
    outcomes = [0, 1, 2, 3, 4, 6, 'w']
    t1_outcomes_count = []
    for outcome in outcomes:
        try:
            if outcome != 'w':
                t1_outcomes_count.append(t1_outcomes[outcome])
            else:
                t1_outcomes_count.append(t1_outs)
        except:
            t1_outcomes_count.append(0)
            
    #st.write(t1_outcomes_count)
    
    t2_outcomes_count = []
    for outcome in outcomes:
        try:
            if outcome != 'w':
                t2_outcomes_count.append(t2_outcomes[outcome])
            else:
                t2_outcomes_count.append(t2_outs)
        except:
            t2_outcomes_count.append(0)
    #st.write(t2_outcomes_count)
    #return
    t1_pb = [i/sum(t1_outcomes_count) for i in t1_outcomes_count]
    t2_pb = [i/sum(t2_outcomes_count) for i in t2_outcomes_count]
    #st.write(t2_pb)
    #st.write(t2_outcomes_count)
    t1_cum_pb = list(np.cumsum(t1_pb))
    t2_cum_pb = list(np.cumsum(t2_pb))
    
    ## Runs prediction: 1st Innings
    curr_score = 0
    curr_wickets = 0
    curr_overs = 0.0

    ing1_runs_pred = []
    
    #st.write(df_ing1.head(10))
    for i in range(len(df_ing1)):
        curr_score += df_ing1.total_runs[i]
        curr_overs = ".".join([str(df_ing1.over[i]-1), str(df_ing1.ball[i])])
        curr_wickets += df_ing1.is_wicket[i]
        
        prediction = innings_1_runs(curr_overs, curr_score, curr_wickets,t1_cum_pb)
        #st.write('score: ', curr_score, ' overs: ', curr_overs, ' wickets: ', curr_wickets, ' prediction: ', prediction)
        ing1_runs_pred.append(prediction)
        #return
    ing1_actual_score = sum(df_ing1.total_runs)
    #st.write("First Innings Score"+str(ing1_actual_score)+"/"+str(curr_wickets)+" ("+str(curr_overs)+")")
    ## Runs prediction: 2nd Innings
    curr_score = 0
    curr_wickets = 0
    curr_overs = 0.0
    target = ing1_actual_score

    ing2_runs_pred = []

    for i in range(len(df_ing2)):
        curr_score += df_ing2.total_runs[i]
        curr_overs = ".".join([str(df_ing2.over[i]-1), str(df_ing2.ball[i])])
        curr_wickets += df_ing2.is_wicket[i]
        
        prediction = innings_2_runs(curr_overs, curr_score, curr_wickets, target,t2_cum_pb)
    #     print('target: ', target)
    #     print('score: ', curr_score, ' overs: ', curr_overs, ' wickets: ', curr_wickets, ' prediction: ', prediction)
        ing2_runs_pred.append(prediction)
    
    ing2_actual_score = sum(df_ing2.total_runs)
    #st.write("Second Innings Score"+str(ing2_actual_score)+"/"+str(curr_wickets)+" ("+str(curr_overs)+")")
    
    # for each ball make a prediction: 1st runs, 2nd runs, win/lose/tie
    #st.write(np.mean([abs(i - ing2_actual_score) for i in ing2_runs_pred]))
    # initialize win/tie/lose
    win_count = 0
    tie_count = 0
    lose_count = 0

    win_count_ls = []
    tie_count_ls = []
    lose_count_ls = []

    ing1_curr_score = 0
    ing1_curr_overs = 0
    ing1_curr_wickets = 0
    win_count_ls.append(50) 
    lose_count_ls.append(50) 
    
    # each ball
    for i in range(len(df_ing1)):
        
        # 1st innings values
        ing1_curr_score += df_ing1.total_runs[i]        
        ing1_curr_overs = ".".join([str(df_ing1.over[i]-1), str(df_ing1.ball[i])])
        ing1_curr_wickets += df_ing1.is_wicket[i]
        
        #2nd innings values
        ing2_curr_score = 0
        ing2_curr_wickets = 0
        ing2_curr_overs = 0.0
        
        #st.write('score: ', ing1_curr_score, ' overs: ', ing1_curr_overs, ' wickets: ', ing1_curr_wickets)
        # make a prediction for 100 times & get win/lose/tie count(ex: 28% win)
        for j in range(100):
            
            ing1_prediction = innings_1_runs(ing1_curr_overs, ing1_curr_score, ing1_curr_wickets,t1_cum_pb)
            target = ing1_prediction
            
            ing2_prediction = innings_2_runs(ing2_curr_overs, ing2_curr_score, ing2_curr_wickets, target,t2_cum_pb)
            
            #st.write(ing1_prediction, ing2_prediction)
            
            # prediction w.r.t 2nd team
            if ing2_prediction > target:
                win_count += 1
            elif ing2_prediction == target:
                tie_count += 1
            else:
                lose_count += 1
                
        win_count_ls.append(win_count)
        tie_count_ls.append(tie_count)
        lose_count_ls.append(lose_count)
        
        win_count = 0
        tie_count = 0
        lose_count = 0
        
    #2nd innings values
    ing2_curr_score = 0
    ing2_curr_wickets = 0
    ing2_curr_overs = 0.0
    
    for i in range(len(df_ing2)):
        
        # 1st innings values
        target = ing1_actual_score
        
        #2nd innings values
        ing2_curr_score += df_ing2.total_runs[i]
        ing2_curr_wickets += df_ing2.is_wicket[i]
        ing2_curr_overs = ".".join([str(df_ing2.over[i]-1), str(df_ing2.ball[i])])
        #st.write("Score:"+str(ing2_curr_score)+"Wickets:"+str(ing2_curr_wickets)+"Overs:"+str(ing2_curr_overs))
        # make a prediction for 100 times & get win/lose/tie count(ex: 28% win)
        for j in range(100):
            ing2_prediction = innings_2_runs(ing2_curr_overs, ing2_curr_score, ing2_curr_wickets, target,t2_cum_pb)
            
            #st.write(target, ing2_prediction)
            
            # prediction w.r.t 2nd team
            if ing2_prediction > target:
                win_count += 1
            elif ing2_prediction == target:
                tie_count += 1
            else:
                lose_count += 1
                
        win_count_ls.append(win_count)
        tie_count_ls.append(tie_count)
        lose_count_ls.append(lose_count)
        #st.write("Win: "+str(win_count)+" Tie: "+str(tie_count)+" lose: "+str(lose_count))
    
    
        win_count = 0
        tie_count = 0
        lose_count = 0
    #st.write(win_count_ls)
    #st.write(tie_count_ls)
    #st.write(lose_count_ls)
    st.write(first_batting_teamname+": "+str(ing1_curr_score)+"/"+str(ing1_curr_wickets)+" ("+str(getOverDetails(ing1_curr_overs))+")")   
    st.write(second_batting_teamname+": "+str(ing2_curr_score)+"/"+str(ing2_curr_wickets)+" ("+str(getOverDetails(ing2_curr_overs))+")")
    
    plt.figure(figsize = (16, 6))
    plt.style.use('dark_background')
    plt.tight_layout()
    x1_values = [i for i in range(len(win_count_ls))]
    y1_values = win_count_ls

    x2_values = [i for i in range(len(tie_count_ls))]
    y2_values = tie_count_ls

    x3_values = [i for i in range(len(lose_count_ls))]
    y3_values = lose_count_ls
 
    for i in range(10, len(ipl_df), 20):
        if i < len(ipl_df) - 10:
            plt.axvspan(i, i+10, ymin = 0, ymax = 100, alpha = 0.05, color='grey')
            
    plt.axhline(y = 75, ls = '--', alpha = 0.3, c = 'grey')
    plt.axhline(y = 50, ls = '--', alpha = 1, c = 'grey')
    plt.axhline(y = 25, ls = '--', alpha = 0.3, c = 'grey')

    plt.plot(x1_values, y1_values, color = 'orange', label = t2)
    plt.plot(x2_values, y2_values, color = 'grey', label = 'Tie Value')
    plt.plot(x3_values, y3_values, color = 'blue', label = t1)

    plt.ylim(0, 100)
    plt.yticks([0, 25, 50, 75, 100])


    # add confidence interval
    # ci = 3
    # plt.fill_between(x1_values, np.array(y1_values) - ci, np.array(y1_values) + ci, color = 'orange', alpha = 0.2 )
    # plt.fill_between(x2_values, np.array(y2_values) - ci, np.array(y2_values) + ci, color = 'grey', alpha = 0.2 )
    # plt.fill_between(x3_values, np.array(y3_values) - ci, np.array(y3_values) + ci, color = 'blue', alpha = 0.2 )

    plt.title('Win Percentage Chart: ' + t1 + ' vs ' + t2, fontsize = 16)
    plt.xlabel('Ball No')
    plt.ylabel('Win %')
    plt.legend()
    #plt.show()
    st.pyplot(plt)
    
        
    match_stats_df = {
        't1_score':str(ing1_curr_score)+"/"+str(ing1_curr_wickets)+" ("+str(getOverDetails(ing1_curr_overs))+")",
        't2_score':str(ing2_curr_score)+"/"+str(ing2_curr_wickets)+" ("+str(getOverDetails(ing2_curr_overs))+")"
        }
    return match_stats_df

def getOverDetails(curr_overs):
    over_ball = curr_overs
    over_number = int(str(over_ball).split('.')[0])
    ball_number = int(str(over_ball).split('.')[1])
    if ball_number >=6:
        over_no = over_number+1
    else:
        over_no = curr_overs
    return over_no
    
def getPlayerStatistics(df,grpbyList):    
        
        df['isDot'] = df['batsman_runs'].apply(lambda x: 1 if x == 0 else 0)
        df['isOne'] = df['batsman_runs'].apply(lambda x: 1 if x == 1 else 0)
        df['isTwo'] = df['batsman_runs'].apply(lambda x: 1 if x == 2 else 0)
        df['isThree'] = df['batsman_runs'].apply(lambda x: 1 if x == 3 else 0)
        df['isFour'] = df['batsman_runs'].apply(lambda x: 1 if x == 4 else 0)
        df['isSix'] = df['batsman_runs'].apply(lambda x: 1 if x == 6 else 0)
        
      
        if ('phase' in grpbyList):
            df['phase'] = df['over'].apply(lambda x: phase(x))
         
            
        runs = pd.DataFrame(df.groupby(grpbyList)['batsman_runs'].sum().reset_index()).groupby(grpbyList)['batsman_runs'].sum().reset_index().rename(columns={'batsman_runs':'Runs'})
        
        innings = pd.DataFrame(df.groupby(grpbyList)['match_id'].apply(lambda x: len(list(np.unique(x)))).reset_index()).rename(columns = {'match_id':'Innings'})
        balls = pd.DataFrame(df.groupby(grpbyList)['match_id'].count()).reset_index().rename(columns = {'match_id':'Balls'})
        
        bowler_dismissal_df = df[~df.dismissal_kind.isin(['run out', 'retired hurt', 'obstructing the field','NA'])]
        dismissals = pd.DataFrame(bowler_dismissal_df.groupby(grpbyList)['player_dismissed'].count()).reset_index().rename(columns = {'player_dismissed':'Dismissals'})
        
        dots = pd.DataFrame(df.groupby(grpbyList)['isDot'].sum()).reset_index().rename(columns = {'isDot':'dots'})
        ones = pd.DataFrame(df.groupby(grpbyList)['isOne'].sum()).reset_index().rename(columns = {'isOne':'ones'})
        twos = pd.DataFrame(df.groupby(grpbyList)['isTwo'].sum()).reset_index().rename(columns = {'isTwo':'twos'})
        threes = pd.DataFrame(df.groupby(grpbyList)['isThree'].sum()).reset_index().rename(columns = {'isThree':'threes'})
        fours = pd.DataFrame(df.groupby(grpbyList)['isFour'].sum()).reset_index().rename(columns = {'isFour':'Fours'})
        sixes = pd.DataFrame(df.groupby(grpbyList)['isSix'].sum()).reset_index().rename(columns = {'isSix':'Sixes'})
        
        df = pd.merge(innings, runs, on = grpbyList).merge(balls, on = grpbyList).merge(dismissals, on = grpbyList).merge(dots, on = grpbyList).merge(ones, on = grpbyList).merge(twos, on = grpbyList).merge(threes, on = grpbyList).merge(fours, on = grpbyList).merge(sixes, on = grpbyList)
        
        
        
        #st.table(df)
        if 'batsman' in df.columns:
            
            #StrikeRate
            df['SR'] = (round(df.apply(lambda x: 100*(x['Runs']/x['Balls']), axis = 1),2))

            #runs per innings
            df['RPI'] = (round(df.apply(lambda x: x['Runs']/x['Innings'], axis = 1),2))

            #balls per dismissals
            df['BPD'] = (round(df.apply(lambda x: balls_per_dismissal(x['Balls'], x['Dismissals']), axis = 1),2))

            #balls per boundary
            df['BPB'] = (round(df.apply(lambda x: balls_per_boundary(x['Balls'], (x['Fours'] + x['Sixes'])), axis = 1),2))

        if 'bowler' in df.columns:    
            
            
           
            # StrikeRate = Balls per wicket
            df['SR'] = (round(df.apply(lambda x: balls_per_dismissal(x['Balls'], x['Dismissals']), axis = 1),2))

            # Economy = runs per over
            df['Eco'] = (round(df.apply(lambda x: runs_per_ball(x['Balls'], x['Runs'])*6, axis = 1),2))
        
        # Average = Runs per wicket
        df['Avg'] = (round(df.apply(lambda x: runs_per_dismissal(x['Runs'], x['Dismissals']), axis = 1),2))
        #boundary%
        df['Boundary%'] = (round(df.apply(lambda x: boundary_per_ball(x['Balls'], (x['Fours'] + x['Sixes']))*100, axis = 1),2))
        df['Dot%'] = (round(df.apply(lambda x: get_dot_percentage(x['dots'], x['Balls'])*100, axis = 1),2))
        
        df.drop(['dots','ones','twos','threes','Fours','Sixes'], axis=1, inplace=True)
        #df.drop(['dots','fours','sixes'], axis=1, inplace=True)    
              
        
        return df
        
def getNoofTeamWins(df,team):
    
    df = df[df.winner == team]
    if not df.empty:
        return len(pd.unique(df['match_id']))
    else:
        return 0

def getNoofTeamLoss(df,team):
    
    df = df[(df.result == 'normal') & (df.winner != team)]
    if not df.empty:
        return len(pd.unique(df['match_id']))
    else:
        return 0
        
def getTeamMatchupRecords(df,team1,team2,venue=None):
    
    team_records_df = df[((df.team1 == team1)&
                               (df.team2 == team2)) |
                              ((df.team1 == team2)&
                              (df.team2 == team1))]
    
    if venue:
        team_records_df = team_records_df[(team_records_df.venue == venue)]
    
    if not team_records_df.empty:     
        
        team1_win_count = getNoofTeamWins(team_records_df,team1)
        team2_win_count = getNoofTeamWins(team_records_df,team2)
        team1_lost_count = getNoofTeamLoss(team_records_df,team1)
        team2_lost_count = getNoofTeamLoss(team_records_df,team2)
        team1_max_runs = getTeamHighestScore(team_records_df,team1)
        team2_max_runs = getTeamHighestScore(team_records_df,team2)
        #team1_min_runs = getTeamLowestScore(team_records_df,team1)
        #team2_min_runs = getTeamLowestScore(team_records_df,team2)
        #team1_min_runs = getTeamLowestScore(team_records_df,team1)
        
        data = [
            ['Matches won',team1_win_count,team2_win_count],
            ['Matches lost',team1_lost_count,team2_lost_count],
            ['Highest Score',team1_max_runs,team2_max_runs],
            #['Lowest Score',team1_min_runs,team2_min_runs]
        ]
        teamstats_df = pd.DataFrame(data, columns = ['Team Name', team1,team2])  
    else:
        teamstats_df =  pd.DataFrame()
        
    return teamstats_df
    
def getTeamDF(df,team,start_year,end_year,venue=None):
    df = df[df['season'].between(start_year, end_year)]
    team_records_df = df[((df.team1 == team) | (df.team2 == team))]
    if venue:
        team_records_df = team_records_df[(team_records_df.venue == venue)]
        
    if team_records_df.empty:         
        team_records_df =  pd.DataFrame()
    return team_records_df
    
def plotBarGraph(df,grpbyList,title,xKey,xlabel,ylabel):        
        
        plt.figure(figsize = (12, 4))    
        plt.style.use('dark_background')
        plt.tight_layout()
        if xKey == 'is_wicket':
            df = df[~df.dismissal_kind.isin(['run out', 'retired hurt', 'obstructing the field','<NA>'])]   
            df = df[(df.is_wicket==1)]
        
        if df.empty:
            return
        final_df = df.groupby(grpbyList)[xKey].sum().sort_values(ascending=False).head(15)
        
        final_df.plot(kind = 'barh')
              
        
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        
        for i, v in enumerate(final_df):
            
            #plt.text(v+1 , i-.15 , str(v),
             #       color = 'blue', fontweight = 'bold')
            plt.text(v+0.05 , i-.15 , str(v),
                    color = 'blue', fontweight = 'bold')
        st.pyplot(plt)

def plotScatterGraph(df,key1,key2,xlabel,ylabel,player_type='batsman'):        
        
        plt.figure(figsize = (16, 10))
        plt.style.use('dark_background')
        plt.scatter(df[key1], df[key2],s=45)
        title = ylabel+' vs '+xlabel
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)


        annotations=list(df[player_type])
        #selected_players = ['A Kumble', 'SL Malinga', 'A Mishra', 'Sohail Tanvir', 'DW Steyn']

        for i, label in enumerate(annotations):
            #if label in selected_players:
            plt.annotate(label, (df[key1][i], df[key2][i]),(df[key1][i]+.07, df[key2][i]), fontsize=12)
        
        st.pyplot(plt)

def plotStackBarGraph(df,grpbyList,title,xKey,x2Key,xlabel,ylabel):        
        
        
        plt.style.use('dark_background')
        plt.tight_layout()
        Runs = pd.DataFrame(df.groupby(grpbyList)[xKey].sum().reset_index()).rename(columns = {'batsman_runs':'Runs'})
        innings = pd.DataFrame(df.groupby(grpbyList)[x2Key].apply(lambda x: len(list(np.unique(x)))).reset_index()).rename(columns = {'match_id':'Innings'})
        final_df = pd.merge(innings,Runs,on = grpbyList)
        
        #st.write(Runs)
        #st.write(final_df.sort_values(by='Runs', ascending=True))
        fig, ax = plt.subplots(figsize=(12, 4))
        final_df.sort_values(by='Runs', ascending=True).plot(ax=ax,x='bowling_team', kind='barh', color='yg',stacked=True,title=title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        for c in ax.containers:
            ax.bar_label(c, label_type='edge')
            
        ax.legend(title='Legend', bbox_to_anchor=(1.05, 1), loc='upper left')

        st.pyplot(plt)
        