from transitions import Machine

# Define the system states
states = ['init', 'show_gpt_response', 'comments_on_gpt_response',
          'photo_pending', 'photo_comments_pending', 'comments_on_photo',
          'full_writing_pending']

actions = {'gaze', 'zoom_in', 'move_to_another_place',
           'speak', 'ignore',
           'gpt_generate_response',
           'full_writing_command'}

# Define the transitions
transitions = [
    {'trigger': 'gaze', 'source': 'init', 'dest': 'photo_pending'},
    {'trigger': 'zoom_in', 'source': 'init', 'dest': 'photo_pending'},
    {'trigger': 'move_to_another_place', 'source': 'photo_pending', 'dest': 'photo_comments_pending'},
    {'trigger': 'speak', 'source': 'photo_comments_pending', 'dest': 'comments_on_photo'},
    {'trigger': 'ignore', 'source': 'photo_comments_pending', 'dest': 'init'},
    {'trigger': 'gpt_generate_response', 'source': 'comments_on_photo', 'dest': 'show_gpt_response'},
    {'trigger': 'ignore', 'source': 'show_gpt_response', 'dest': 'init'},
    {'trigger': 'speak', 'source': 'show_gpt_response', 'dest': 'comments_on_gpt_response'},
    {'trigger': 'gpt_generate_response', 'source': 'comments_on_gpt_response', 'dest': 'show_gpt_response'},
    {'trigger': 'full_writing_command', 'source': 'init', 'dest': 'full_writing_pending'},
    {'trigger': 'gpt_generate_response', 'source': 'full_writing_pending', 'dest': 'show_gpt_response'},
]


class Matter(object):
    pass


class SystemStatus(object):
    def __init__(self):
        self.system_status = Matter()
        self.machine = Machine(self.system_status, states=states, transitions=transitions, initial='init')

    def trigger(self, action):
        self.system_status.trigger(action)

    def get_current_state(self):
        return self.system_status.state


if __name__ == '__main__':
    # Test the system status
    system_status = SystemStatus()

    # Perform transitions
    print("Current state:", system_status.get_current_state())

    # Perform some actions to trigger transitions
    system_status.trigger('gaze')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('move_to_another_place')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('speak')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('gpt_generate_response')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('ignore')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('full_writing_command')
    print("Current state:", system_status.get_current_state())

    system_status.trigger('gpt_generate_response')
    print("Current state:", system_status.get_current_state())
