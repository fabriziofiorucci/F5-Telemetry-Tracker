

agent_for_callers = None

def set_agent_for_notifiers(_agent):
    global agent_for_callers
    agent_for_callers = _agent

def get_agent_for_notifiers():
    global agent_for_callers
    return agent_for_callers
