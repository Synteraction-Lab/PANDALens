from transitions import Machine

# Define the hierarchy menu states
states = ['init', 'full', 'voice', 'photo', 'photo_comments', 'voice_recording', 'init_with_response']

menu_icons = {
    'init': {'up': None, 'down': None, 'left': 'Show', 'right': None},
    'init_with_response': {'up': None, 'down': None, 'left': 'Hide', 'right': None},
    'full': {'up': 'Summary', 'down': 'Photo', 'left': 'Hide', 'right': 'Voice'},
    'voice': {'up': None, 'down': None, 'left': None, 'right': 'Voice'},
    'photo': {'up': None, 'down': 'Photo', 'left': None, 'right': None},
    'voice_recording': {'up': None, 'down': None, 'left': None, 'right': 'Stop'},
    'photo_comments': {'up': 'Discard', 'down': 'Retake', 'left': 'Hide', 'right': 'Voice'}
}

# Define the transitions
transitions = [
    {'trigger': 'up', 'source': 'init', 'dest': 'full'},
    {'trigger': 'down', 'source': 'init', 'dest': 'full'},
    {'trigger': 'left', 'source': 'init', 'dest': 'full'},
    {'trigger': 'right', 'source': 'init', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'init', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'full', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'voice', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'photo', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'photo_comments', 'dest': 'full'},
    {'trigger': 'get_response', 'source': 'voice_recording', 'dest': 'full'},
    # {'trigger': 'left', 'source': 'init_with_response', 'dest': 'init'},
    {'trigger': 'show_voice_icon', 'source': 'init', 'dest': 'voice'},
    {'trigger': 'show_photo_icon', 'source': 'init', 'dest': 'photo'},
    {'trigger': 'ignore_voice_icon', 'source': 'voice', 'dest': 'init'},
    {'trigger': 'ignore_photo_icon', 'source': 'photo', 'dest': 'init'},
    {'trigger': 'down', 'source': 'photo', 'dest': 'photo_comments'},
    {'trigger': 'right', 'source': 'voice', 'dest': 'voice_recording'},
    {'trigger': 'show_results', 'source': 'voice_recording', 'dest': 'full'},
    {'trigger': 'show_results', 'source': 'photo_comments', 'dest': 'full'},
    {'trigger': 'right', 'source': 'photo_comments', 'dest': 'voice_recording'},
    {'trigger': 'right', 'source': 'full', 'dest': 'voice_recording'},
    {'trigger': 'left', 'source': 'voice', 'dest': 'init'},
    {'trigger': 'left', 'source': 'photo_comments', 'dest': 'init'},
    {'trigger': 'up', 'source': 'photo_comments', 'dest': 'init'},
    {'trigger': 'left', 'source': 'full', 'dest': 'init'},
    {'trigger': 'down', 'source': 'full', 'dest': 'photo_comments'},
    {'trigger': 'left', 'source': 'photo', 'dest': 'init'},
    # {'trigger': 'left', 'source': 'voice_recording', 'dest': 'init'},
    {'trigger': 'right', 'source': 'voice_recording', 'dest': 'full'},
]


class Matter(object):
    pass


class HierarchyMenu:
    def __init__(self, root, buttons, buttons_places):
        self.menu_layer = Matter()
        self.machine = Machine(self.menu_layer, states=states, transitions=transitions, initial='init')
        self.buttons = buttons
        self.buttons_places = buttons_places
        self.root = root

    def on_enter_state(self):
        # Get the current menu icons based on the state
        menu_icons_state = menu_icons[self.menu_layer.state]

        # Update the button labels based on the menu icons
        for direction, button in self.buttons.items():
            if menu_icons_state[direction]:
                button.configure(text=menu_icons_state[direction])
                button.place_forget()
                button.place(**self.buttons_places[direction])  # Place the button
            else:
                button.place_forget()  # Hide the button

        self.root.update_idletasks()

    def trigger(self, trigger_name):
        current_state = self.menu_layer.state
        current_press_icon = None
        if trigger_name in menu_icons[self.menu_layer.state].keys():
            current_press_icon = menu_icons[self.menu_layer.state][trigger_name]

        if trigger_name in self.machine.get_triggers(self.menu_layer.state):
            self.menu_layer.trigger(trigger_name)  # Call the trigger method
            self.on_enter_state()  # Update the GUI whenever a trigger happens

        return current_press_icon


if __name__ == '__main__':
    from pynput import keyboard
    import tkinter as tk


    def on_press(key):
        # check if key is arrow key and trigger the appropriate transition
        try:
            if key == keyboard.Key.up:
                menu.trigger('up')
            elif key == keyboard.Key.down:
                menu.trigger('down')
            elif key == keyboard.Key.left:
                menu.trigger('left')
            elif key == keyboard.Key.right:
                menu.trigger('right')
            # elif key is 'v':
            elif key.char == 'v':
                menu.trigger('show_voice_icon')
            # elif key is 'p':
            elif key.char == 'p':
                menu.trigger('show_photo_icon')
        except:
            pass


    # # start the key listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    # Example usage
    root = tk.Tk()
    root.geometry('300x300')

    button_up = tk.Button(root, text='')
    button_down = tk.Button(root, text='')
    button_left = tk.Button(root, text='')
    button_right = tk.Button(root, text='')

    buttons = {'up': button_up, 'down': button_down, 'left': button_left, 'right': button_right}
    buttons_places = {'up': {'relx': 0.5, 'rely': 0.3, 'anchor': 'center'},
                      'down': {'relx': 0.5, 'rely': 0.7, 'anchor': 'center'},
                      'left': {'relx': 0.3, 'rely': 0.5, 'anchor': 'center'},
                      'right': {'relx': 0.7, 'rely': 0.5, 'anchor': 'center'}}

    menu = HierarchyMenu(root, buttons, buttons_places)
    menu.on_enter_state()

    root.mainloop()
