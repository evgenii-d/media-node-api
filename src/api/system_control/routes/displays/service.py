def xrandr_to_dict(xrandr_args: list[str]) -> dict[str, str]:
    """
    Convert a list of xrandr command-line arguments into a dictionary.

    Args:
        xrandr_args (list[str]): List of xrandr command-line arguments.

    Returns:
        dict[str, str]: 
            Dictionary where keys are xrandr options or commands 
            and values are their corresponding arguments. 
            Options like "--primary" that don't have a value are 
            mapped to `None`.

    Example:
        Input: 
        [
            "xrandr", "--output", "HDMI-1",
            "--primary", "--mode", "1920x1080"
        ]

        Output: 
        {
            "xrandr": None,
            "--output": "HDMI-1",
            "--primary": None,
            "--mode": "1920x1080"
        }
    """
    result = {}
    for i, word in enumerate(xrandr_args):
        if word in ["xrandr", "--primary"]:
            result.update({word: None})
        elif "--" in word:
            result.update({word: xrandr_args[i+1]})
    return result
