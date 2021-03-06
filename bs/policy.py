import random, util, collections
from util import cmb

class SimplePolicy(util.PolicyGenerator):
    def __init__(self, hdmdp):
        self.hsmdp = hdmdp

    def decision(self, state, id=None):
        if state[0] == 'bs':
            return 'bs' if random.random() < (1 / self.hsmdp.nplayers) else 'pass' # calls bs with 1/nplayers probability
        else: # 'play' state
            truthful = [a for a in self.hsmdp.actions(state) if a[0] > 0 and sum(a) == a[0]]
            if truthful: #we have cards to play
                return max(truthful, key = sum)
            else:
                return random.choice(self.hsmdp.actions(state)) # plays random action if can't be truthful

# where dishonesty and confidence are on a scale from 0 to 1 inclusive
class DishonestPolicy(util.PolicyGenerator):
    def __init__(self, hdmdp, dishonesty, confidence=1, learn=False):
        self.hsmdp = hdmdp
        self.dishonesty = dishonesty
        self.confidence = confidence # this value is only used for adversary learning, which is inactive
        self.learn = learn

    def decision(self, state, id=None):
        if state[0] == 'play':
            state_status, hand, knowledge, pilesize, bust_know, handsizes = state
        else:
            state_status, hand, knowledge, pilesize, bust_know, handsizes, bs_play = state

        state_dict = util.todict(state)

        if state_status == 'bs':
            cardsRemoved = 0
            if bust_know and bs_play[0] != bust_know[0]:
                cardsRemoved += bust_know[1][0]
            cardsRemoved += hand[0] + knowledge[0]
            totalInCirculation = self.hsmdp.getMaxPlayable()
            if totalInCirculation < cardsRemoved + bs_play[1]:
                return 'bs'

            if bs_play[1] == totalInCirculation and hand[0] == 0:
                return 'pass'
            N = sum(handsizes)+pilesize-sum(hand) #total number of cards
            k = totalInCirculation - cardsRemoved #number of cards the player MIGHT have
            n = handsizes[bs_play[0]] + bs_play[1] #cards the player had in hand
            x = bs_play[1] #number of cards played
            if (N-k) - (n-x) < 0: #if this is true, then the player had to have had these cards
                return 'pass'

            #the relative change in hand size for the BS caller if he fails
            changeForPlayer = util.changeForPlayer(state_dict)
            #the relative change in hand size for the player if he is caught
            changeForCaller = util.changeForCaller(state_dict)
            #hypergeometric probability that the player had x of the card
            prob = float(cmb(k, x)) * cmb(N-k, n-x) / cmb(N, n)
            #the ai takes into account the likelihood that the opponent is lying based on previous, similar moves.
            #check advLearnCall in play_game.py for details on what exactly is stored
            learnMult = 1
            if self.learn: # this feature is inactive, but maintained for legacy
                #we check if this kind of play has happened before
                if ("honesty", changeForPlayer, bs_play[1]) in self.hsmdp.action_history[bs_play[0]]:
                    #count up all the actions
                    actionList = self.hsmdp.action_history[bs_play[0]][("honesty", changeForPlayer, bs_play[1])]
                    counter = collections.Counter(actionList)
                    nActions = counter["lie"] + counter["true"]
                    lieChance = counter["lie"] / nActions
                    #we modify the multiplier based on how likely they are to BS and our confidence score
                    learnMult = 1 + (lieChance-1) * min(1, (nActions) * self.confidence)
            #we decrease the likelihood of calling based on the number of players, as we can just let someone else do it
            #we increase the likelihood of calling based on how badly a loss hurts the player
            #we decrease the likelihood of calling based on how badly a loss hurts the caller
            call = random.random() < (1 - prob) / self.hsmdp.nplayers * changeForPlayer / changeForCaller
            return 'bs' if call else 'pass'
        else:
            truthful = [a for a in self.hsmdp.actions(state) if a[0] > 0 and sum(a) == a[0]] #entirely honest plays
            semitruthful = [a for a in self.hsmdp.actions(state) if a[0] == hand[0] and a[0] > 0 and sum(a) > a[0]] #play all of the required card and more
            full_lies = [a for a in self.hsmdp.actions(state) if a[0] == 0] #play none of the required card
            if not truthful and not semitruthful: #if we don't have the card, play a number of cards weighted against future plays
                weights = {}
                for action in full_lies:
                    weight = 1
                    for i in range(self.hsmdp.nplayers, len(action), self.hsmdp.nplayers):
                        weight *= 1/(1+action[i])
                    weights[action] = weight
                return util.weightedChoice(weights)

            #if we have a play, weight against lies that use future cards and weight the truth based on dishonestyiness
            weights = {}
            for action in semitruthful:
                weight = 1
                for i in range(len(action)/2):
                    cardOnTurnI = i * self.hsmdp.nplayers
                    if cardOnTurnI >= len(action):
                        cardOnTurnI -= len(action)
                    weight *= 1/(1+action[cardOnTurnI])
                weights[action] = weight
            if random.random()<(1-self.dishonesty) or not semitruthful:
                return max(truthful)
            else:
                return util.weightedChoice(weights) #exaggerate if we can and are feeling dishonestyy

            #note that we do not have an option to play only some of the required card, as I can't think of a situation where we'd want to


