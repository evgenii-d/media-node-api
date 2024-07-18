"""
This script detects connected displays using `xrandr`
and creates Tkinter windows on each display.

The main window is placed on the primary display,
and additional windows are created for each secondary display.
The windows are positioned near the center of their respective
displays and display the name of the display.
"""

import re
import sys
from subprocess import run
from dataclasses import dataclass
from tkinter import Tk, Toplevel, Label


@dataclass
class WindowGeometry:
    """The geometry of a window.

    Attributes:
        width: The width of the window in pixels.
        height: The height of the window in pixels.
        x: The x-coordinate of the top-left corner.
        y: The y-coordinate of the top-left corner.
    """
    width: int
    height: int
    x: int
    y: int

    def __str__(self) -> str:
        """
        Returns a string representation
        suitable for Tkinter's geometry method.
        """
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


@dataclass
class XrandrDisplay:
    """Represents a display detected by `xrandr`.

    Attributes:
        name (str): The name of the display.
        is_primary (bool): 
            True if the display is the primary display.
        resolution (str): 
            The resolution of the display in the format "widthxheight".
        position (str): 
            The position of the display in the format "x+y".
    """
    name: str
    is_primary: bool
    resolution: str
    position: str


def create_window(geometry: WindowGeometry,
                  title: str = "", message: str = "") -> None:
    """Creates a Toplevel window.

    Args:
        geometry (WindowGeometry):
            Defining the window's size and position.
        title (str, optional):
            The title of the window. Defaults to "".
        message (str, optional):
            The message to be displayed in the window. Defaults to "".
    """
    window = Toplevel()
    window.title(title)
    window.geometry(str(geometry))
    font = ("Arial", int(geometry.width/geometry.height * 20))
    label = Label(window, text=message, font=font)
    label.place(relx=0.5, rely=0.5, anchor="center")


def main():
    """
    Main function to get display information and create windows.
    """
    root = Tk()
    xrandr_cmd = run(["xrandr"], check=True, capture_output=True, text=True)
    regex = r"(.+)\s(?:connected)(.*)\s(\d+x\d+)\+(\d+\+\d+)\s"
    displays: list[XrandrDisplay] = [
        XrandrDisplay(match[0], bool(match[1]), match[2], match[3])
        for match in re.findall(regex, xrandr_cmd.stdout)
    ]

    if not displays:
        sys.exit("No connected displays found")

    for display in displays:
        w, h = map(int, display.resolution.split("x"))
        x, y = map(int, display.position.split("+"))
        geometry = WindowGeometry(w//2, h//2, x+w//4, y+h//4)
        info = f'{display.resolution}\n{display.position}'

        if display.is_primary:
            root.title(f"{display.name} [Main Window]")
            root.geometry(str(geometry))
            font = ("Arial", int(w/h * 20))
            label = Label(root, font=font, text=f'[{display.name}]\n{info}')
            label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            create_window(geometry, display.name, f'{display.name}\n{info}')
    root.mainloop()


if __name__ == "__main__":
    main()
