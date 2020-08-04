#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
import pandas as pd
import numpy as np
import requests
import datetime
import math
from flask import *
app = Flask(__name__)

api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJkYmZkNzQyMC04Yjc1LTAxMzgtMmZjYy00ZDk1MjEyYTg1YmEiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNTkxNTkzNzAxLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6ImE1NzIxNTg5OC1nbWFpIn0.Dy-voJzorhh1_ACqCOhBz8efyZNL2OwJu3LMuog7MsM'
userId = 'aaaa'
headers = {'Authorization': f'Bearer {api_key}',
            'Accept': 'application/vnd.api+json'}


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/boubtIdSearch', methods=['POST'])
def BS(boubtId = None):
    page = 1
    if request.method == 'POST':
        boubtId = request.form['boubtId']

    params = (('filter[playerNames]', boubtId),)
    boubt_player_re = requests.get('https://api.pubg.com/shards/steam/players', headers=headers, params=params)
    match_data = boubt_player_re.json()['data'][0]['relationships']['matches']['data']
    platform = boubt_player_re.json()['data'][0]['attributes']['shardId']
    mapList = {'Desert_Main':'미라마','DihorOtok_Main':'비켄디','Erangel_Main':'에란겔','Baltic_Main':'에란겔'
                  ,'Range_Main':'훈련장','Savage_Main':'사녹','Summerland_Main':'카라킨'}
    
    attributes,gameModeData,mapNameData,createdAtData,groupNumData,killsData,rankData,matchIdData = [],[],[],[],[],[],[],[]
    length = len(match_data)//20+2
    if len(match_data)%20 == 0:
        length -= 1
    attributes = []
    for match_id in match_data:
        m_id = match_id['id']
        response = requests.get(f'https://api.pubg.com/shards/{platform}/matches/{m_id}', headers=headers)
        gameMode = response.json()['data']['attributes']['gameMode']
        mapName = response.json()['data']['attributes']['mapName']
        createdAt = response.json()['data']['attributes']['createdAt']
        groupNum = 0
        for i in range(len(response.json()['included'])):
            typ = response.json()['included'][i]['type']
            if typ == 'participant':
                win = response.json()['included'][i]['attributes']['stats']['winPlace']
                if groupNum <= win:
                    groupNum = win
                participant = response.json()['included'][i]['attributes']['stats']['name']
                if participant == boubtId:
                    kills = response.json()['included'][i]['attributes']['stats']['kills']
                    rank = response.json()['included'][i]['attributes']['stats']['winPlace']
                    
        mapName = mapList[mapName]
        attributes.append(gameMode)
        attributes.append(mapName)
        attributes.append(createdAt)
        attributes.append(rank)
        attributes.append(groupNum)
        attributes.append(kills)
        attributes.append(m_id)
        
    attributesLen = len(attributes)
    return render_template('boubtIdSearch.html',boubtId = boubtId, attributes = attributes, length = length,
                           page = page, attributesLen = attributesLen)

@app.route('/page', methods=['POST'])
def page():
    if request.method == 'POST':
        attributes,page, length, boubtId, attributesLen = request.form['movePage'].split('//')
    attributes = attributes.replace("[","")
    attributes = attributes.replace(']','')
    attributes = attributes.replace('\'','')
    attributes = attributes.split(',')
    return render_template('boubtIdSearch.html',page = int(page), attributes = attributes, length = int(length),
                           boubtId = boubtId, attributesLen = int(attributesLen))

@app.route('/teaming', methods=['POST'])
def teaming():
    if request.method == 'POST':
        aaa = request.form['matchId'].split(',')
        m_id, boubtId = request.form['matchId'].split(',')
        m_id = m_id.strip()
    mod = sys.modules[__name__]
    platform = 'steam'
    response = requests.get(f'https://api.pubg.com/shards/{platform}/matches/{m_id}', headers=headers)
    for i in range(len(response.json()['included'])):
        if 'URL' in response.json()['included'][i]['attributes']:
            url = response.json()['included'][i]['attributes']['URL']

    createdAt = response.json()['data']['attributes']['createdAt']
    telemetry = requests.get(url, headers=headers)
    
    columns = ['match_date', 'match_id', '_D', '_T', 'isGame', 'teamId', 'c_name','c_accountId', 'c_health'
               , 'pk_killer', 'pk_victim', 'pk_victim_accountId', 'td_attacker', 'td_victim'
               , 'td_victim_acouuntId', 'c_loc_x', 'c_loc_y', 'c_loc_z']

    for col in columns:
        setattr(mod,col,[])
    
    global teamId,isGame,match_date,match_id,_D,_T,c_name,c_accountId,c_health,pk_killer,pk_victim,    pk_victim_accountId,td_attacker,td_victim,td_victim_acouuntId,c_loc_x,c_loc_y,c_loc_z

    for log,i in zip(telemetry.json(),range(len(telemetry.json()))):
        if 'common' in log:
            if log['common']['isGame'] >= 1 and log['common']['isGame'] != None:
                if log['_T'] == 'LogPlayerTakeDamage':
                    if (log['victim']['isInBlueZone'] or log['victim']['isInRedZone'] 
                        or log['damageTypeCategory']=='Damage_BlueZone'
                        or log['damageTypeCategory'] == 'Damage_VehicleHit'
                        or log['damageTypeCategory'] == 'Damage_Drown'
                        or log['damageTypeCategory'] == 'Damage_Explosion_BlackZone'
                        or log['attackId'] == -1):
                        pass
                    else:
                        teamId.append(log['attacker']['teamId'])
                        td_attacker.append(log['attacker']['name'])
                        td_victim.append(log['victim']['name'])
                        td_victim_acouuntId.append(log['victim']['accountId'])
                        c_name.append(log['attacker']['name'])
                        c_accountId.append(log['attacker']['accountId'])
                        c_health.append(log['attacker']['health'])
                        c_loc_x.append(log['attacker']['location']['x'])
                        c_loc_y.append(log['attacker']['location']['y'])
                        c_loc_z.append(log['attacker']['location']['z'])
                        match_date.append(createdAt)
                        match_id.append(m_id)
                        isGame.append(log['common']['isGame'])
                        _D.append(log['_D'])
                        _T.append(log['_T'])
                        pk_killer.append(None)
                        pk_victim.append(None)
                        pk_victim_accountId.append(None)

                elif log['_T'] == 'LogPlayerKill':
                    if (log['victim']['isInBlueZone'] or log['victim']['isInRedZone'] or log['attackId'] == -1
                        or log['damageTypeCategory'] == 'Damage_Drown'
                        or log['damageTypeCategory'] == 'Damage_Explosion_BlackZone'):
                        pass
                    else:
                        teamId.append(log['killer']['teamId'])
                        pk_killer.append(log['killer']['name'])
                        pk_victim.append(log['victim']['name'])
                        pk_victim_accountId.append(log['victim']['accountId'])
                        c_name.append(log['killer']['name'])
                        c_accountId.append(log['killer']['accountId'])
                        c_health.append(log['killer']['health'])
                        c_loc_x.append(log['killer']['location']['x'])
                        c_loc_y.append(log['killer']['location']['y'])
                        c_loc_z.append(log['killer']['location']['z'])
                        match_date.append(createdAt)
                        match_id.append(m_id)
                        isGame.append(log['common']['isGame'])
                        _D.append(log['_D'])
                        _T.append(log['_T'])
                        td_attacker.append(None)
                        td_victim.append(None)
                        td_victim_acouuntId.append(None)

                elif 'character' in log:
                        teamId.append(log['character']['teamId'])
                        c_name.append(log['character']['name'])
                        c_accountId.append(log['character']['accountId'])
                        c_health.append(log['character']['health'])
                        c_loc_x.append(log['character']['location']['x'])
                        c_loc_y.append(log['character']['location']['y'])
                        c_loc_z.append(log['character']['location']['z'])
                        match_date.append(createdAt)
                        match_id.append(m_id)
                        isGame.append(log['common']['isGame'])
                        _D.append(log['_D'])
                        _T.append(log['_T'])
                        td_attacker.append(None)
                        td_victim.append(None)
                        td_victim_acouuntId.append(None)
                        pk_killer.append(None)
                        pk_victim.append(None)
                        pk_victim_accountId.append(None)
                        
    df = pd.DataFrame(data=[match_date,match_id, _D, _T, isGame, teamId, c_name,c_accountId, c_health
                  ,pk_killer, pk_victim, pk_victim_accountId, td_attacker,td_victim, td_victim_acouuntId
                  ,c_loc_x, c_loc_y, c_loc_z],index = columns).T
    df['_D'] = pd.to_datetime(df['_D'])
        
    s_time = df['_D'].min()
    e_time = df['_D'].max()
    one_s = datetime.timedelta(seconds=1)
    log_df = pd.DataFrame()
    count = 0
    tdCount = 0
    while s_time < e_time:
        time_df = df.loc[(df['_D']>=s_time)&(df['_D']<s_time+one_s)]
        c_names = time_df['c_name'].unique()
        columns = ['time','c_name','teamId','isGame','pk_killer','pk_victim','td_attacker','td_victim']
        for n in c_names:
            columns.append(n) 
        try:
            data = []
            x1, y1, z1, teamId1, isGame,pk_killer,pk_victim,td_attacker,td_victim= time_df.loc[time_df['c_name']==boubtId]                [['c_loc_x','c_loc_y','c_loc_z','teamId', 'isGame','pk_killer','pk_victim','td_attacker','td_victim']].iloc[0]
            for name in c_names:
                if boubtId != name:
                    x2, y2, z2 , teamId2 = time_df.loc[time_df['c_name']==name][['c_loc_x','c_loc_y','c_loc_z','teamId']].iloc[0]
                    distance_m = math.sqrt((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)/100
                else: 
                    distance_m = 0.0
            if (distance_m > 0 and distance_m <= 20 and teamId1 != teamId2):
                count += 1
                if (pk_killer or pk_victim or td_attacker or td_victim):
                    tdCount += 1
            totalCount = count * tdCount
            s_time = s_time + one_s
        except:
            s_time = s_time + one_s
    if count <= 5:
        isTeaming = '티밍일 확률이 매우 적습니다'
    elif count <= 10:
        isTeaming = '티밍일 확률이 적습니다'
    elif count <= 15:
        isTeaming = '티밍이 약간 의심 됩니다'
    elif count <= 20:
        isTeaming = '티밍이 의심 됩니다'
    else:
        isTeaming = '티밍이 매우 의심 됩니다'
    return render_template('teaming.html',isTeaming=isTeaming,count=count, tdCount = tdCount, totalCount = totalCount)

if __name__ == '__main__':
    app.run(host = '0.0.0.0')


# In[ ]:




