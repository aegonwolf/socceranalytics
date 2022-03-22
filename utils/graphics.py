#----------------------------------------------------------------------------
# Created By: Danny Camenisch (dcamenisch)
# Created Date: 22/03/2022
# version ='1.0'
# ---------------------------------------------------------------------------
""" 
Draws a soccer pitch and draw a given Frame.
"""
# ---------------------------------------------------------------------------
from matplotlib import pyplot as plt
from matplotlib.patches import Arc
from matplotlib.axes import Axes

from socceranalytics.utils.match import Frame

def drawFrame(ax: Axes, frame: Frame):
    """Draw a the positions from a frame on a given axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to draw on
    frame : Frame
        Frame to draw
    """
    drawPitch(ax)
    for obj in frame.trackingObjs:
        x = obj.x / 100.0
        y = obj.y / 100.0 + 34.0

        if obj.type == "0":
            ax.scatter(x, y, color="blue")
        elif obj.type == "1":
            ax.scatter(x, y, color="red")
        elif obj.type == "7":
            ax.scatter(x, y, color="green")

def drawPitch(
    ax: Axes,
    x_min: float = -52.5,
    x_max: float = 52.5,
    y_min: float = 0,
    y_max: float = 68,
    zorder: int = -10,
):
    """Draw a football pitch on a given axes.

    The pitch is fitted between the given minimum and maximum coordinates.
    Scale is not guaranteed.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to draw the pitch on
    x_min : float, optional
        Minimum x point of the pitch, by default -52.5
    x_max : float, optional
        Maximum x point of the pitch, by default 52.5
    y_min : float, optional
        Minimum y point of the pitch, by default 0
    y_max : float, optional
        Maximum y point of the pitch, by default 68
    zorder : int, optional
        Plotting order of the pitch on the axes, by default -10
    """
    x = lambda x: (x / 130) * (x_max - x_min) + x_min
    y = lambda y: (y / 90) * (y_max - y_min) + y_min

    rat_x = (x_max - x_min) / 130
    rat_y = (y_max - y_min) / 90

    # Pitch Outline & Centre Line
    ax.plot([x(0), x(0)], [y(0), y(90)], color="black", zorder=zorder)
    ax.plot([x(0), x(130)], [y(90), y(90)], color="black", zorder=zorder)
    ax.plot([x(130), x(130)], [y(90), y(0)], color="black", zorder=zorder)
    ax.plot([x(130), x(0)], [y(0), y(0)], color="black", zorder=zorder)
    ax.plot([x(65), x(65)], [y(0), y(90)], color="black", zorder=zorder)

    # Left Penalty Area
    ax.plot([x(16.5), x(16.5)], [y(65), y(25)], color="black", zorder=zorder)
    ax.plot([x(0), x(16.5)], [y(65), y(65)], color="black", zorder=zorder)
    ax.plot([x(16.5), x(0)], [y(25), y(25)], color="black", zorder=zorder)

    # Right Penalty Area
    ax.plot([x(130), x(113.5)], [y(65), y(65)], color="black", zorder=zorder)
    ax.plot([x(113.5), x(113.5)], [y(65), y(25)], color="black", zorder=zorder)
    ax.plot([x(113.5), x(130)], [y(25), y(25)], color="black", zorder=zorder)

    # Left 6-yard Box
    ax.plot([x(0), x(5.5)], [y(54), y(54)], color="black", zorder=zorder)
    ax.plot([x(5.5), x(5.5)], [y(54), y(36)], color="black", zorder=zorder)
    ax.plot([x(5.5), x(0.5)], [y(36), y(36)], color="black", zorder=zorder)

    # Right 6-yard Box
    ax.plot([x(130), x(124.5)], [y(54), y(54)], color="black", zorder=zorder)
    ax.plot([x(124.5), x(124.5)], [y(54), y(36)], color="black", zorder=zorder)
    ax.plot([x(124.5), x(130)], [y(36), y(36)], color="black", zorder=zorder)

    # Prepare circles
    centre_circle = plt.Circle((x(65), y(45)), 9.15, color="black", fill=False, zorder=zorder)
    centre_spot = plt.Circle((x(65), y(45)), 0.8, color="black", zorder=zorder)
    left_pen_spot = plt.Circle((x(11), y(45)), 0.8, color="black", zorder=zorder)
    right_pen_spot = plt.Circle((x(119), y(45)), 0.8, color="black", zorder=zorder)

    # Draw Circles
    ax.add_patch(centre_circle)
    ax.add_patch(centre_spot)
    ax.add_patch(left_pen_spot)
    ax.add_patch(right_pen_spot)

    # Prepare Arcs
    left_arc = Arc(
        (x(11), y(45)),
        height=18.3 * rat_y,
        width=18.3 * rat_x,
        angle=0,
        theta1=310,
        theta2=50,
        color="black",
        zorder=zorder,
    )
    right_arc = Arc(
        (x(119), y(45)),
        height=18.3 * rat_y,
        width=18.3 * rat_x,
        angle=0,
        theta1=130,
        theta2=230,
        color="black",
        zorder=zorder,
    )

    # Draw Arcs
    ax.add_patch(left_arc)
    ax.add_patch(right_arc)