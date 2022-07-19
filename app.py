from flask import Flask, render_template, request
import json
import gzip, pickle
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import datetime
import itertools
from flask import Response


players_all_records = pd.read_csv(r'combined_data_copy.csv',index_col=False)

with open('players.json', 'r') as f:
    unique_players = json.loads(f.read())

with open('grounds.json', 'r') as f:
    unique_grounds = json.loads(f.read())

with open('ground_countries.json', 'r') as f:
    unique_ground_countries = json.loads(f.read())
# Load the pickle model
model = pickle.load(open("final_model.pkl", "rb"))

app = Flask(__name__)

def createPlayerDict (pak_players, opp_players, match_date, opp_team):
    pakplayerdict = {}
    oppplayerdict = {}

    match_date_input = datetime.datetime.strptime(match_date, '%Y-%m-%d')

    players_all_records["date"] = pd.to_datetime(players_all_records["date"], format='%d %b %Y')
    players_all_records['player_name'] = players_all_records['player_name'].str.strip()

    for player in pak_players:
        if (player.split()[:2] == "New Player"):
            this_player_batting_average = 0
            this_player_batting_4s6sRate = 0

        else:
            mask = (players_all_records['date'] < match_date_input) & (players_all_records['date'] > match_date_input - relativedelta(years=3)) & (players_all_records['player_name'] == player) & (players_all_records['player_country'] == "Pakistan") & (players_all_records['opposition'] == opp_team)
            players_old_matches = players_all_records.loc[mask]
            total_Runs = 0
            Num_of_outs = 0
            total_4s_6s = 0
            innings = 0
            for index, row in players_old_matches.iterrows():
                if ((row['runs_made'] != '-')):
                    total_Runs = total_Runs + int(row['runs_made'])
                    if (row['is_out'] == 1):
                        Num_of_outs =  Num_of_outs + 1
                    total_4s_6s = total_4s_6s + int(row['fours']) + int(row['sixes'])
                    innings = innings + 1

            if (Num_of_outs == 0):
                this_player_batting_average = 0
            else:
                this_player_batting_average = total_Runs/Num_of_outs

            if (innings == 0):
                this_player_batting_4s6sRate = 0
            else:
                this_player_batting_4s6sRate = (total_4s_6s)/innings


        pakplayerdict[player] = [this_player_batting_average, this_player_batting_4s6sRate ]


    for player in opp_players:

        if (player.split()[:2] == "New Player"):
            this_player_batting_average = 0
            this_player_batting_4s6sRate = 0

        else:
            mask = (players_all_records['date'] < match_date_input) & (players_all_records['date'] > match_date_input - relativedelta(years=3)) & (players_all_records['player_name'] == player) & (players_all_records['player_country'] == opp_team) & (players_all_records['opposition'] == "Pakistan")
            players_old_matches = players_all_records.loc[mask]

            total_Runs = 0
            Num_of_outs = 0
            total_4s_6s = 0
            innings = 0

            for index, row in players_old_matches.iterrows():
                if ((row['runs_made'] != '-')):
                    total_Runs = total_Runs + int(row['runs_made'])
                    if (row['is_out'] == 1):
                        Num_of_outs =  Num_of_outs + 1
                    total_4s_6s = total_4s_6s + int(row['fours']) + int(row['sixes'])
                    innings = innings + 1

            if (Num_of_outs == 0):
                this_player_batting_average = 0
            else:
                this_player_batting_average = total_Runs/Num_of_outs

            if (innings == 0):
                this_player_batting_4s6sRate = 0
            else:
               this_player_batting_4s6sRate = (total_4s_6s)/innings


        oppplayerdict[player] = [this_player_batting_average, this_player_batting_4s6sRate ]


    return [pakplayerdict, oppplayerdict]

def getBattingAverageAnd4s6sRateCategory(pak_players, opp_players,pakplayerdict, oppplayerdict):

    raw_batting_average_A_B = 0
    pakistan_team_batting_average = 0
    pakistan_team_batting_4sand6sRate = 0
    for player in pak_players:

        this_player_batting_average = pakplayerdict.get(player)[0];
        this_player_batting_4s6sRate = pakplayerdict.get(player)[1];

        pakistan_team_batting_average = pakistan_team_batting_average + this_player_batting_average
        pakistan_team_batting_4sand6sRate = pakistan_team_batting_4sand6sRate +this_player_batting_4s6sRate

    opposite_team_batting_average = 0
    opposite_team_batting_4sand6sRate = 0

    for player in opp_players:

        this_player_batting_average = oppplayerdict.get(player)[0];
        this_player_batting_4s6sRate = oppplayerdict.get(player)[1];

        opposite_team_batting_average = opposite_team_batting_average + this_player_batting_average
        opposite_team_batting_4sand6sRate = opposite_team_batting_4sand6sRate + this_player_batting_4s6sRate

    raw_batting_average_A_B = pakistan_team_batting_average - opposite_team_batting_average
    min_batting_average_A_B = -125.24999999999996
    max_batting_average_A_B = 163.0

    if (raw_batting_average_A_B < min_batting_average_A_B):
        min_batting_average_A_B = raw_batting_average_A_B
    if (raw_batting_average_A_B > max_batting_average_A_B):
        max_batting_average_A_B = raw_batting_average_A_B

    raw_batting_4sand6sRate_A_B = pakistan_team_batting_4sand6sRate - opposite_team_batting_4sand6sRate
    min_batting_4sand6sRate_A_B = -18.000000
    max_batting_4sand6sRate_A_B = 17.000000

    if (raw_batting_4sand6sRate_A_B < min_batting_4sand6sRate_A_B):
        min_batting_4sand6sRate_A_B = raw_batting_4sand6sRate_A_B
    if (raw_batting_4sand6sRate_A_B > max_batting_4sand6sRate_A_B):
        max_batting_4sand6sRate_A_B = raw_batting_4sand6sRate_A_B

    batting_average_A_B = int(round((raw_batting_average_A_B - min_batting_average_A_B) / (max_batting_average_A_B - min_batting_average_A_B),1)*10)
    batting_4sand6sRate_A_B = int(round((raw_batting_4sand6sRate_A_B - min_batting_4sand6sRate_A_B) / (max_batting_4sand6sRate_A_B - min_batting_4sand6sRate_A_B),1)*10)

    return [batting_average_A_B, batting_4sand6sRate_A_B]

def preprocessData(ground, ground_country, opp_team, pak_players, opp_players, match_date, pakplayerdict, oppplayerdict):
    Ground_Karachi = 0
    Ground_Hamilton = 0
    Ground_Mohali = 0
    Ground_Cardiff = 0
    Ground_Country_India = 0
    Opposite_Team_England = 0
    Opposite_Team_Zimbabwe = 0
    Opposite_Team_India = 0


    if ground == "Karachi":
        Ground_Karachi = 1
    elif ground == "Hamilton":
        Ground_Hamilton = 1
    elif ground == "Mohali":
        Ground_Mohali = 1
    elif ground == "Cardiff":
        Ground_Cardiff = 1

    if ground_country=="India":
        Ground_Country_India = 1


    if opp_team == "England":
        Opposite_Team_England = 1
    elif opp_team == "Zimbabwe":
        Opposite_Team_Zimbabwe = 1
    elif opp_team == "India":
        Opposite_Team_India = 1

    batting_average_A_B, batting_4sand6sRate_A_B = getBattingAverageAnd4s6sRateCategory(pak_players, opp_players, pakplayerdict, oppplayerdict)

    return [batting_average_A_B, batting_4sand6sRate_A_B, Ground_Country_India, Ground_Karachi, Ground_Cardiff, Ground_Hamilton, Ground_Mohali, Opposite_Team_England, Opposite_Team_India, Opposite_Team_Zimbabwe]

@app.route('/prediction', methods = ["GET", "POST"])
def prediction():
    if request.method == "POST":

        matchDetails = request.form
        opp_team = matchDetails["opposite_team"]
        toss = matchDetails["toss"]
        bat_first = matchDetails["bat_first"]
        match_date = matchDetails["date"]
        match_timing = matchDetails["match_timing"]
        ground = matchDetails["ground"]
        all_pak_players = matchDetails.getlist("pak_players")
        new_pak_players = int(matchDetails["new_pak_players"])
        all_opp_players = matchDetails.getlist("opp_players")
        new_opp_players = int(matchDetails["new_opp_players"])

        if ground == "other":
            ground_country = matchDetails["Ground-Country"]
        else:
            for i in unique_grounds:
                if (i['Ground'] == ground):
                    ground_country = i['Ground_Country']
                    break

        for i in range(new_pak_players):
            all_pak_players.append("New Player " + str(i))

        for j in range(new_opp_players):
            all_opp_players.append("New Player " + str(j))

        pakplayerdict, oppplayerdict = createPlayerDict(all_pak_players, all_opp_players, match_date, opp_team)

        # Net Batting Average, Net 4s_6s_rate, Ground_Country_India, Ground_Karachi, Ground_Cardiff, Ground_Hamilton, Ground_Mohali,Opposite_Team_England, Opposite_Team_India, Opposite_Team_Zimbabwe

        features = preprocessData(ground, ground_country, opp_team, all_pak_players, all_opp_players, match_date, pakplayerdict, oppplayerdict )
        prediction_percentage = model.predict_proba((np.array(features)).reshape(1, -1))
        losing_percentage = round(prediction_percentage[0][0]*100,2)
        winning_percentage = round(prediction_percentage[0][1]*100,2)

        return render_template('predict_result.html', losing_percentage=losing_percentage, winning_percentage= winning_percentage )

    else:

        return render_template('prediction_form.html', unique_grounds = unique_grounds, unique_players=unique_players, unique_ground_countries=unique_ground_countries )

@app.route('/recommendation', methods = ["GET", "POST"])
def recommendation():

    if request.method == "POST":

        e = datetime.datetime.now()
        print("start")
        print("%s %s:%s:%s", e.hour, e.minute, e.second, e.microsecond)
        matchDetails = request.form
        opp_team = matchDetails["opposite_team"]
        toss = matchDetails["toss"]
        bat_first = matchDetails["bat_first"]
        match_date = matchDetails["date"]
        match_timing = matchDetails["match_timing"]
        ground = matchDetails["ground"]
        all_pak_players = matchDetails.getlist("pak_players")
        new_pak_players = int(matchDetails["new_pak_players"])
        all_opp_players = matchDetails.getlist("opp_players")
        new_opp_players = int(matchDetails["new_opp_players"])

        if ground == "other":
            ground_country = matchDetails["Ground-Country"]
        else:
            for i in unique_grounds:
                if (i['Ground'] == ground):
                    ground_country = i['Ground_Country']
                    break

        compulsory_pak_players = request.form.getlist('comp-pak-players')
        compulsory_opp_players = request.form.getlist('comp-opp-players')

        nc_pak_players = list(set(all_pak_players).difference(set(compulsory_pak_players)))
        nc_opp_players = list(set(all_opp_players).difference(set(compulsory_opp_players)))

        pak_combinations = list(itertools.combinations(nc_pak_players, 11-len(compulsory_pak_players)))

        opp_combinations = list(itertools.combinations(nc_opp_players, 11-len(compulsory_opp_players)))

        pakplayerdict, oppplayerdict = createPlayerDict(all_pak_players, all_opp_players, match_date, opp_team)

        min_win_perc_pak = 101
        strongest_opp_team = []

        count1=0

        for pak_comb in pak_combinations:
            for opp_comb in opp_combinations:

                count1= count1+1
                pak_team_comb = list(set(pak_comb).union(set(compulsory_pak_players)))
                opp_team_comb = list(set(opp_comb).union(set(compulsory_opp_players)))
                features = preprocessData(ground, ground_country, opp_team, pak_comb, opp_comb, match_date, pakplayerdict, oppplayerdict)
                prediction_percentage = model.predict_proba((np.array(features)).reshape(1, -1))
                # losing_percentage = round(prediction_percentage[0][0]*100,2)
                winning_percentage = round(prediction_percentage[0][1]*100,2)

                if (winning_percentage < min_win_perc_pak):
                    min_win_perc_pak = winning_percentage
                    strongest_opp_team=opp_team_comb



        max_win_perc_pak = 0
        strongest_pak_team = []
        count2 = 0
        for pak_comb in pak_combinations:

            count2 = count2+1
            pak_team_comb = list(set(pak_comb).union(set(compulsory_pak_players)))
            features = preprocessData(ground, ground_country, opp_team, pak_comb, opp_comb, match_date,pakplayerdict, oppplayerdict)
            prediction_percentage = model.predict_proba((np.array(features)).reshape(1, -1))
            # losing_percentage = round(prediction_percentage[0][0]*100,2)
            winning_percentage = round(prediction_percentage[0][1]*100,2)
            if (winning_percentage > max_win_perc_pak):
                max_win_perc_pak = winning_percentage
                strongest_pak_team=pak_team_comb

        final_winning_percentage = max_win_perc_pak
        final_losing_percentage = 100 - max_win_perc_pak

        print("finish")
        e = datetime.datetime.now()
        print ("%s %s:%s:%s", e.hour, e.minute, e.second, e.microsecond)

        return render_template('recommendation_result.html', losing_percentage=final_losing_percentage, winning_percentage=final_winning_percentage, pak_team=strongest_pak_team, opp_team=strongest_opp_team)
    else:
        return render_template('recommendation_form.html', unique_grounds = unique_grounds, unique_players=unique_players, unique_ground_countries=unique_ground_countries )

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
