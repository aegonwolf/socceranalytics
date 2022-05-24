import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Arc
from matplotlib.transforms import Affine2D
import matplotlib.transforms as transforms
from matplotlib.patches import Ellipse


def draw_pitch(
    ax: Axes,
    pitch_center: tuple = (0, 34),
    pitch_length: float = 105,
    pitch_width: float = 68,
    linewidth: float = 1.2,
    linecolor="black",
    background_color=None,
    zorder: int = -10,
    orient_vertical: bool = False,
):
    """Draw a football pitch on a given axes.
    The pitch is fitted according to the provided center and width/length arguments.
    Scale is not guaranteed.
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to draw the pitch on
    pitch_center : tuple
        Center of the pitch, by default (0, 34). The center is the point in the
        middle of the pitch, lengthwise and widthwise respectively. If orient_vertical
        is False (default), this translates to x and y axes.
    pitch_length : float
        Length of the pitch, by default 105
    pitch_width : float
        Width of the pitch, by default 68
    linewidth : float
        Width of the lines, passed to plot calls and patch initializations, by default 1.2
    linecolor : color
        Color of the lines, passed to plot calls and patch initializations, by default "black"
    background_color : color
        Color of the plot background as a matplotlib color, by default None
    zorder : int, optional
        Plotting order of the pitch on the axes, by default -10
    orient_vertical : bool, optional
        Change the pitch orientation to vertical, by default False
    """
    if orient_vertical:
        transform = Affine2D().rotate_deg(90).scale(-1, 1) + ax.transData
    else:
        transform = ax.transData
    x = lambda x: (x / 130) * pitch_length + pitch_center[0] - pitch_length / 2
    y = lambda y: (y / 90) * pitch_width + pitch_center[1] - pitch_width / 2
    rat_x = pitch_length / 130
    rat_y = pitch_width / 90
    plot_arguments = dict(
        color=linecolor, zorder=zorder, transform=transform, linewidth=linewidth
    )
    # Pitch Outline & Centre Line
    ax.plot([x(0), x(0)], [y(0), y(90)], **plot_arguments)
    ax.plot([x(0), x(130)], [y(90), y(90)], **plot_arguments)
    ax.plot([x(130), x(130)], [y(90), y(0)], **plot_arguments)
    ax.plot([x(130), x(0)], [y(0), y(0)], **plot_arguments)
    ax.plot([x(65), x(65)], [y(0), y(90)], **plot_arguments)
    # Left Penalty Area
    ax.plot([x(16.5), x(16.5)], [y(65), y(25)], **plot_arguments)
    ax.plot([x(0), x(16.5)], [y(65), y(65)], **plot_arguments)
    ax.plot([x(16.5), x(0)], [y(25), y(25)], **plot_arguments)
    # Right Penalty Area
    ax.plot([x(130), x(113.5)], [y(65), y(65)], **plot_arguments)
    ax.plot([x(113.5), x(113.5)], [y(65), y(25)], **plot_arguments)
    ax.plot([x(113.5), x(130)], [y(25), y(25)], **plot_arguments)
    # Left 6-yard Box
    ax.plot([x(0), x(5.5)], [y(54), y(54)], **plot_arguments)
    ax.plot([x(5.5), x(5.5)], [y(54), y(36)], **plot_arguments)
    ax.plot([x(5.5), x(0.5)], [y(36), y(36)], **plot_arguments)
    # Right 6-yard Box
    ax.plot([x(130), x(124.5)], [y(54), y(54)], **plot_arguments)
    ax.plot([x(124.5), x(124.5)], [y(54), y(36)], **plot_arguments)
    ax.plot([x(124.5), x(130)], [y(36), y(36)], **plot_arguments)
    # Prepare circles
    centre_circle = plt.Circle((x(65), y(45)), 9.15, fill=False, **plot_arguments)
    centre_spot = plt.Circle((x(65), y(45)), linewidth / 2, **plot_arguments)
    left_pen_spot = plt.Circle((x(11), y(45)), linewidth / 4, **plot_arguments)
    right_pen_spot = plt.Circle((x(119), y(45)), linewidth / 4, **plot_arguments)
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
        theta1=312,
        theta2=48,
        **plot_arguments,
    )
    right_arc = Arc(
        (x(119), y(45)),
        height=18.3 * rat_y,
        width=18.3 * rat_x,
        angle=0,
        theta1=128,
        theta2=232,
        **plot_arguments,
    )
    # Draw Arcs
    ax.add_patch(left_arc)
    ax.add_patch(right_arc)
    if background_color is not None:
       ax.set_facecolor(background_color)


## if you want to plot multiple scatters in one figure (for the clusters)
def plot_cluster(formation, fig, ax, coords_transformation = True):
    mus = formation
    colors = plt.cm.rainbow(np.linspace(0, 1, 11))
    shift = np.array([0, 0])

    if coords_transformation:
        draw_pitch(ax, pitch_center=(0, 0), orient_vertical=True)
        ax.set_xlim(-40, 40)
        ax.set_ylim(-50, 50)

        mus = [[-pair[1], -pair[0]] for pair in mus]

    for p in range(len(mus)):
        ax.scatter([mus[p][0]+shift[0]], [mus[p][1]+shift[1]], s=100, color=colors[p], edgecolors='k')
        # confidence_ellipse(mus[p]+shift, covs[p], ax, n_std=1, facecolor=(0,0,0,0.2))


# Modified from: https://matplotlib.org/3.1.1/gallery/statistics/confidence_ellipse.html#sphx-glr-gallery-statistics-confidence-ellipse-py
def confidence_ellipse(mu, cov, ax, n_std=1.0, facecolor='none', **kwargs):
    if np.sum(cov**2) < 1e-6:
        return
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0),
        width=ell_radius_x * 2,
        height=ell_radius_y * 2,
        facecolor=facecolor,
        zorder= 100,
        **kwargs)

    # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std

    # calculating the stdandard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mu[0], mu[1])

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def plot_formation_cluster_compact(formation, coords_transformation = True):
    mus  = formation[0].copy()
    covs = np.stack(formation[1], axis=0).copy()
    fig = plt.figure(figsize=(8, 8))
    ax = plt.gca()
    ax.set_facecolor('white')
    ax.set_xlim(-30, 50)
    ax.set_ylim(-30, 30)
    
    # note: coordinate transformation assumes a ltr formation, as it is implemented here.
    if coords_transformation:

        ax.set_xlim(-40, 40)
        ax.set_ylim(-50, 50)
        # fig, ax = plt.subplots(figsize=(6.8, 10.5))
        draw_pitch(ax, orient_vertical=True, pitch_center=(0, 0))
        mus = [[-pair[1], -pair[0]] for pair in mus]

        colors = plt.cm.rainbow(np.linspace(0, 1, 11), alpha = 0.3)

        covs_flipped = []
        for cov in covs:
            cov = np.flip(cov)
            covs_flipped.append(cov)

    # shift = np.array([-106/2, -68/2])
    for p in range(len(mus)):
        confidence_ellipse(mus[p], covs_flipped[p], ax, n_std=1, facecolor=colors[p])
        ax.scatter([mus[p][0]], [mus[p][1]], s=100, color=colors[p], edgecolors='k')
    plt.axis('off')

# very specific to our match, change if necessary
def get_fig_title(key: str, clusters_idx: int):
    if '_1_' in key and 'defensive' in key: 
        return f'Italy Defensive Formation Cluster Number {clusters_idx}.'
    elif '_1_' in key and 'offensive' in key:
        return f'Italy Attacking Formation Cluster Number {clusters_idx}.'
    elif '_2_' in key and 'defensive' in key:
        return f'Spain Defensive Formation Cluster Number {clusters_idx}.'
    elif '_2_' in key and 'offensive' in key:
        return f'Spain Attacking Formation Cluster Number {clusters_idx}.'
    else: ValueError('Invalid Key or Index')