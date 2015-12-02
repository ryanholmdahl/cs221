import play_game,qlearn,policy,util

#Does some q learning on the hdmdp.
def qlsimulate(hsmdp, rl, numTrials=10, maxIterations=1000, verbose=False):
    totalRewards = []  # The rewards we get on each trial
    for trial in range(numTrials):
        hsmdp.restart()
        state = hsmdp.startState()
        if state == None:
            continue
        sequence = [state]
        totalDiscount = 1
        totalReward = 0
        for _ in range(maxIterations):
            action = rl.getAction(state)
            newState, reward = hsmdp.succAndReward(state, action)
            if newState == None:
                rl.incorporateFeedback(state, action, 0, None)
                break

            sequence.append(action)
            sequence.append(reward)
            sequence.append(newState)

            rl.incorporateFeedback(state, action, reward, newState)
            totalReward += totalDiscount * reward
            totalDiscount *= hsmdp.discount()
            state = newState
        if verbose:
            print "Trial %d (totalReward = %s): %s" % (trial, totalReward, sequence)
        totalRewards.append(totalReward)
    return totalRewards

#Tests an hdmdp with the agent following the agent_decision policy.
def allsetsimulate(hsmdp, agent_decision, numTrials=10, maxIterations=1000, oracle=False, verbose=False):
    totalRewards = []  # The rewards we get on each trial
    for trial in range(numTrials):
        hsmdp.restart()
        state = hsmdp.startState()
        sequence = [state]
        totalDiscount = 1
        totalReward = 0
        for _ in range(maxIterations):
            if state == None:
                break
            if state[0] == "someone_wins":
                action = "end_game"
            else:
                if not oracle or len(state) == 6:
                    action = agent_decision(state,hsmdp.agent_index)
                else:
                    action = "pass" if hsmdp.lastPlayIsHonest() else "bs"

            newState, reward = hsmdp.succAndReward(state, action)

            sequence.append(action)
            sequence.append(reward)
            sequence.append(newState)

            totalReward += totalDiscount * reward
            totalDiscount *= hsmdp.discount()
            state = newState
        if verbose:
            print "Trial %d (totalReward = %s): %s" % (trial, totalReward, sequence)
        totalRewards.append(totalReward)
    return totalRewards