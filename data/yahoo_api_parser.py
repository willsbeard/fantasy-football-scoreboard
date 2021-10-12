import requests
from datetime import datetime
from utils import convert_time
import os
import debug
import json
from yahoo_oauth import OAuth2

# https://fantasysports.yahooapis.com/fantasy/v2/games;game_codes=nfl I'm almost positive this is how to find the game id (406) but I totally forget now

class YahooFantasyInfo():
    def __init__(self, yahoo_consumer_key, yahoo_consumer_secret, game_id, league_id, team_id, week):
        self.team_id = team_id
        self.league_id = league_id
        self.game_id = game_id
        self.week = week
        self.auth_info = {"consumer_key": yahoo_consumer_key, "consumer_secret": yahoo_consumer_secret}

        authpath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'auth'))
        if not os.path.exists(authpath):
            os.makedirs(authpath, 0777)

        # load or create OAuth2 refresh token
        token_file_path = os.path.join(authpath, "token.json")
        if os.path.isfile(token_file_path):
            with open(token_file_path) as yahoo_oauth_token:
                self.auth_info = json.load(yahoo_oauth_token)
        else:
            with open(token_file_path, "w") as yahoo_oauth_token:
                json.dump(self.auth_info, yahoo_oauth_token)

        if "access_token" in self.auth_info.keys():
            self._yahoo_access_token = self.auth_info["access_token"]

        # complete OAuth2 3-legged handshake by either refreshing existing token or requesting account access
        # and returning a verification code to input to the command line prompt
        self.oauth = OAuth2(None, None, from_file=token_file_path)
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()

        self.matchup = self.get_matchup(self.game_id, self.league_id, self.team_id, week)
        self.all_matchups = self.get_all_matchups(self.game_id, self.league_id, week)
        self.league = self.get_league(self.game_id, self.league_id, self.team_id, week)
        self.get_avatars(self.matchup)

    # yeah these two are stupid and useless functions but right now I'm panicking trying to get this to work
    def refresh_matchup(self):
        return self.get_matchup(self.game_id, self.league_id, self.team_id, self.week)

    def refresh_scores(self):
        return self.get_matchup(self.game_id, self.league_id, self.team_id, self.week)
    
    def get_matchup(self, game_id, league_id, team_id, week):
        self.refresh_access_token()
        url = "https://fantasysports.yahooapis.com/fantasy/v2/team/{0}.l.{1}.t.{2}/matchups;weeks={3}".format(self.game_id, self.league_id, self.team_id, week)
        response = self.oauth.session.get(url, params={'format': 'json'})
        matchup = response.json()["fantasy_content"]["team"][1]["matchups"]
        #print("FULL MATCHUP")
        #print(matchup)
        matchup_info = {}
        for m in matchup:
            #print("M in MATCHUP: ")
            #print(m)
            if not isinstance(matchup[m], int): #WHEN INTEGER ENTER
                #print ("FALSE")
                team = matchup[m]['matchup']['0']['teams']
                #print("TEAM")
                #print(team)
                for t in team:
                    #print("T in TEAM: ")
                    #print(t)
                    if not isinstance(team[t], int):
                        #print("INSIDE")
                        if team[t]['team'][0][3]:
                            matchup_info['user_name'] = team[t]['team'][0][19]['managers'][0]['manager']['nickname']
                            matchup_info['user_av'] = team[t]['team'][0][19]['managers'][0]['manager']['nickname']
                            matchup_info['user_av_location'] = team[t]['team'][0][5]['team_logos'][0]['team_logo']['url']
                            matchup_info['user_team'] = team[t]['team'][0][2]['name']
                            matchup_info['user_proj'] = team[t]['team'][1]['team_projected_points']['total']
                            matchup_info['user_score'] = float(team[t]['team'][1]['team_points']['total'])
                        else:
                            matchup_info['opp_name'] = team[t]['team'][0][19]['managers'][0]['manager']['nickname']
                            matchup_info['opp_av'] = team[t]['team'][0][19]['managers'][0]['manager']['nickname']
                            matchup_info['opp_av_location'] = team[t]['team'][0][5]['team_logos'][0]['team_logo']['url']
                            matchup_info['opp_team'] = team[t]['team'][0][2]['name']
                            matchup_info['opp_proj'] = team[t]['team'][1]['team_projected_points']['total']
                            matchup_info['opp_score'] = float(team[t]['team'][1]['team_points']['total'])
        return matchup_info

    def get_all_matchups(self, game_id, league_id, week):
        self.refresh_access_token()
        #url = "https://fantasysports.yahooapis.com/fantasy/v2/team/{0}.l.{1}.t.{2}/matchups;weeks={3}".format(self.game_id, self.league_id, self.team_id, week)
        url = "https://fantasysports.yahooapis.com/fantasy/v2/league/{0}.l.{1}/scoreboard;week={2}".format(self.game_id, self.league_id, week)
        response = self.oauth.session.get(url, params={'format': 'json'})
        #print("URL")
        #print(url)
        #matchups = response.json()["fantasy_content"]["league"][1]["scoreboard"][0]["matchups"]
        matchups = response.json()["fantasy_content"]["league"][1]["scoreboard"]
        print("FULL MATCHUPS")
        print(matchups)
        matchups_info = {}
        for m in matchups:
            #print("M in MATCHUPS: ")
            #print(m)
            if not isinstance(matchups[m], int): #WHEN INTEGER ENTER
                #print ("FALSE")
                team = matchups[m]['matchup']['0']['teams']
                print("TEAM")
                print(team)
        #return matchups_info

    def get_league(self, game_id, league_id, team_id, week):
        self.refresh_access_token()
        url = "https://fantasysports.yahooapis.com/fantasy/v2/league/{0}.l.{1}/standings".format(self.game_id, self.league_id)
        response = self.oauth.session.get(url, params={'format': 'json'})
        #standings = response.json()["fantasy_content"]["league"][1]["standings"]
        standings = response.json()["fantasy_content"]["league"][1]["standings"][0]["teams"]
        standing_info = {}
        final_standings_info = {}
        for s in standings:
            if not isinstance(standings[s], int):
                team_name = standings[s]['team'][0][2]['name']
                team_rank = standings[s]['team'][2]['team_standings']['rank']
                team_wins = standings[s]['team'][2]['team_standings']['outcome_totals']['wins']
                team_losses = standings[s]['team'][2]['team_standings']['outcome_totals']['losses']
                team_ties = standings[s]['team'][2]['team_standings']['outcome_totals']['ties']
                team_pts_for = standings[s]['team'][2]['team_standings']['points_for']
                team_pts_agst = standings[s]['team'][2]['team_standings']['points_against']
                standing_info[s] = [team_rank,team_name,team_wins,team_losses,team_ties,team_pts_for,team_pts_agst]
        
        #SORT RANKINGS
        for t in standing_info:
            rank = int(standing_info[t][0])-1
            final_standings_info[rank]=standing_info[t]
            #print("PRE: ",standing_info[t]," ",rank)
        
        # TEST PRINT SORTED RANKING
        #for q in range(12):
        #    print(str(final_standings_info[q][0]) + " " + final_standings_info[q][1].encode('utf-8') + " " + str(final_standings_info[q][2]) + "-" + str(final_standings_info[q][3]) + "-" + str(final_standings_info[q][4]))
        
        return final_standings_info

    def get_avatars(self, teams):
        self.refresh_access_token()
        debug.info('getting avatars')
        logospath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'logos'))
        if not os.path.exists(logospath):
            os.makedirs(logospath, 0777)
        self.get_avatar(logospath, teams['user_name'], teams['user_av_location'])
        self.get_avatar(logospath, teams['opp_name'], teams['opp_av_location'])

    def get_avatar(self, logospath, name, url):
        filename = os.path.join(logospath, '{0}.jpg'.format(name))
        if not os.path.exists(filename):
            debug.info('downloading avatar for {0}'.format(name))
            r = requests.get(url, stream=True)
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)

    def refresh_access_token(self):
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()