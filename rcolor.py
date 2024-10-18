class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    LIGHT_GRAY = '\033[37m'
    Dark_GRAY = '\033[90m'


def colortext(color, text, other_style = None):
        if other_style is not None:
            return other_style + color + text + Color.RESET
        else:
            return color + text + Color.RESET