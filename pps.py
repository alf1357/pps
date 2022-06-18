#!/usr/bin/env python3

# 20211224, the program for calculate roles, license is GPLv3, by alf of stk


# the function for calculate

fps = 1
fps_pe = 120
activityKartRadius = 3 # **0.5

def main(data):

    def getTrend():
        return(('def','att')[(1-trendAttTeam,0,trendAttTeam)[zModifier[name]+1]])

    defScore, attScore, blockScore, pushScore, timeCountTrend, timeCount = {}, {}, {}, {}, {}, {}
    fieldGoalScore ={} # fielder-goalkeeper
    playerSleep = {} # was cake or afk

    for (dataType,e) in data:
        if dataType == 'player':
            (name,coordinates,team) = e
            if not name in playerPos:
                defScore[name], attScore[name], blockScore[name], pushScore[name], fieldGoalScore[name] = 0, 0, 0, 0, 0
                playerSleep[name] = 0
                timeCountTrend[name], timeCount[name] = {'def':1,'att':1}, 1
                playerPos[name] = {'z':0, 'x':0, 'y':0}
            if team not in zTeamModifier: zTeamModifier[team] = (1,-1)[coordinates['z']>0]
            zModifier[name] = zTeamModifier[team]
            if playerPos != coordinates:
                playerPos[name] = coordinates
                if playerSleep[name] < 10*fps: playerSleep[name] = 0
                else: playerSleep[name] -= 10
            else: playerSleep[name] += 1
            if trendAttTeam != -1 and playerSleep[name] < fps:
                trend = getTrend()
                puckz = puck['z']*zModifier[name]
                playerz = playerPos[name]['z']*zModifier[name]
                zDistance = puckz-playerz
                xDistance = puck['x']-playerPos[name]['x']
                if trend == 'def':
                    if puckz > -fieldLen*2/3: fieldGoalScore[name] += -fieldLen*2/3-playerz
                    optimalzPosition, optimalxPosition = (puckz-fieldLen*7/8)/2, puck['x']*2/3
                    defScoreDelta = (3-abs(max(-3,min(2,(optimalzPosition-playerz)*4/fieldLen))))/(1+max(0.1,abs(optimalxPosition-playerPos[name]['x'])/fieldLen))
                    if puckz < -fieldLen/2: defScoreDelta = defScoreDelta*(fieldLen*3/2+puckz)/fieldLen
                    defScore[name] += defScoreDelta #positional defense
                    blockScore[name] += activityKartRadius/max((zDistance+3)**2+xDistance**2,activityKartRadius)*(abs(puckzspeed)+1) #block defense
                if trend == 'att':
                    if puckz < fieldLen/2: fieldGoalScore[name] += -fieldLen*2/3-playerz
                    optimalzPosition = puckz-fieldLen/14
                    attScore[name] += (1-abs(max(-1,min(1,-(optimalzPosition-playerz)*4/fieldLen)))) # positional attack
                    pushScore[name] += activityKartRadius/max((zDistance+1)**2+xDistance**2,activityKartRadius)*(abs(puckzspeed)+1) # push attack
                timeCountTrend[name][trend] += 1
                timeCount[name] += 1
        elif dataType == 'p': # p is puck
            oldPuck = puck
            puck = e
            puckZMin, puckZMax = min(puckZMin,puck['z']), max(puckZMax,puck['z'])
            puckzspeed = oldPuck['z'] - puck['z']
            if abs(puck['z'])*3 > fieldLen*4: fieldLen = abs(puck['z'])*3/4
            if  trendAttTeam != 0 and puckzspeed < 0 and puck['z']<fieldLen/2 and (puckZMax-puck['z'])*30>fieldLen:
                trendAttTeam = 0
                puckZMax = -fieldLen
            if trendAttTeam != 1 and puckzspeed > 0 and puck['z']>-fieldLen/2 and (puck['z']-puckZMin)*30>fieldLen:
                trendAttTeam = 1
                puckZMin = fieldLen
        elif dataType in ('caked','bowled','swattered'):
            (name,name2) = e
            if name in playerPos and name2 in playerPos and trendAttTeam != -1:
                trend = getTrend()
                if trend == 'def':
                    blockScore[name]+=fps/fps_pe/3
                    pushScore[name2]+=fps/fps_pe/30
                if trend == 'att':
                    pushScore[name]+=fps/fps_pe/3
                    blockScore[name2]+=fps/fps_pe/30
        elif dataType == 'puck_hit_bowl':
            (speed,name) = e
            if name in playerPos and trendAttTeam != -1:
                trend = getTrend()
                zDistance = (puck['z']-playerPos[name]['z'])*zModifier[name]
                if zDistance > 0:
                    if trend == 'def':
                        blockScore[name] += speed**(1/3)*fps/fps_pe/3
                    if trend == 'att':
                        pushScore[name] += speed**(1/3)*fps/fps_pe/3*max(0,min(1,2-puckz*2/fieldLen)) # skip stupid push maybe
        elif dataType == 'GAME_START':
            fieldLen = 60 # 1/2 field length
            oldPuck, puck, playerPos = {'z':0, 'x':0}, {'z':0, 'x':0}, {} # position
            zModifier, zTeamModifier = {}, {} # friend team identificator
            puckzspeed = fieldLen # for game start
        if abs(puckzspeed) > fieldLen/2:
            trendAttTeam = -1 # global situation, blue or red
            puckZMin, puckZMax = 0, 0
    r = []
    for name in playerPos:
        if timeCount[name] > fps*10:
            bs = blockScore[name]*150/timeCountTrend[name]['def']
            ps = pushScore[name]*150/timeCountTrend[name]['att']
            r.append([name,
            defScore[name]*35/timeCountTrend[name]['def']+bs,
            attScore[name]*160/timeCountTrend[name]['att']+ps,
            bs+ps,
            fieldGoalScore[name]/timeCount[name]])

    return(r)


# the function for print to stdout

def print_(data):

    r = ''
    if len(data)>0:
        for e in data:
            r += e[0] + ' '
            if e[-1] > 0: r += 'goalkeeper'
            else:
               p = e[2]-e[1]
               r += str(int(p))+' '+('defender','middle-defender','middler','middle-attacker','attacker')[max(0,min(4,int(p/12+2.5)))]+ ' '+str(int(e[3]))
#            r += '\n'
            r += ';   '
    return(r)


# for run like execute program

import sys

a=[]
for st in sys.stdin.read()[:2**20].split('\n'):
    e = st.split(' ')
    if len(e) > 3 and e[2][0] in '0123456789-':
        coordinates = {'z':float(e[3]),'x':float(e[1]),'y':float(e[2])}
        if len(e) > 4: a.append(('player',(e[0],coordinates,e[4])))
        else: a.append((e[0],coordinates))
        continue
    elif e[0] == 'puck_hit_bowl': a.append((e[0],(float(e[1]),e[2])))
    elif len(e) == 3 and e[1] in ('caked','bowled','swattered'): a.append((e[1],(e[0],e[2])))
    elif e == ['GAME_START']: a.append((e[0],0))
print(print_(main([('GAME_START',0)]+a)))
