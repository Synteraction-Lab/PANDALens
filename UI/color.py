from UI.UI_config import COLOR_THEME
# translate color to the theme (ttkbootstrap)'s color name

# color_theme = {'blue': 'primary',
#                'red': 'danger',
#                'yellow': 'warning',
#                'black': 'dark',
#                'green': 'success',
#                'aquamarine': 'info',
#                'lightgrey': 'light'}


# def color_translation(color):
#     if color in color_theme.keys():
#         return color_theme[color]
#     return 'default'

def color_translation(color):
    if color in COLOR_THEME.keys():
        return COLOR_THEME[color]
    return 'white'

