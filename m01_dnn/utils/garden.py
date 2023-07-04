import seaborn as sns
import matplotlib.pyplot as plt
from functools import lru_cache
import ipywidgets as pw
import os
from matplotlib import animation, rc
from IPython.display import HTML
import numpy as np
from typing import Callable, Sequence

rc('animation', html='jshtml')

def cross(aa: Sequence[int], bb: Sequence[int]):
    return np.array([[b, a] for a in aa for b in bb], dtype='float64')

@lru_cache(None)
def evaluate_on_square(f, location=(0, 0), side=200, n=100):
    xd = np.linspace(location[0]-side/2, location[1]+side/2, n)
    xx = cross(xd, xd)
    fs = np.array([f(x) for x in xx])

    return fs


def plot_field(fig: plt.Figure, field: np.array, location: tuple, side: int):
    n = np.sqrt(field.shape[0]).astype(int)
    min_x, max_x = location[0]-side/2, location[0]+side/2
    min_y, max_y = location[1]-side/2, location[1]+side/2
    

    fig.gca().imshow(
        field.reshape(n, n), 
        extent=[min_x, max_x, max_y, min_y],
        cmap=plt.get_cmap('Greens').reversed()
    )
    fig.gca().set_yticks([])
    fig.gca().set_xticks([])
    return fig

    
def plot_learning_path(fig: plt.Figure, paths):
    for history in paths:
        # First point will be blue
        sns.scatterplot({'x': history[0:1, 0], 'y': history[0:1, 1]}, x='x', y='y', color='blue', ax=fig.gca())
        # Intermediate steps are red
        sns.scatterplot({'x': history[1:, 0], 'y': history[1:, 1]}, x='x', y='y', color='red', ax=fig.gca())
        # Last point will be black
        sns.scatterplot({'x': history[-1:, 0], 'y': history[-1:, 1]}, x='x', y='y', color='black', ax=fig.gca())
        
    return fig


def animate_garden(loss_function: Callable, paths: np.array): 
    center = (0, 0)
    side = 30
    
    field = evaluate_on_square(
        loss_function, 
        location=center, 
        side=side
    )
    
    fig = plt.figure(figsize=[8, 8])
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    plot_field(fig=fig, field=field, location=center, side=side)
    
    def animate(i):
        if i == 0:
            color = 'red'
        else:
            color = 'blue'
            
        scatter = fig.gca().scatter(
            x=paths[:, i, 0], 
            y=paths[:, i, 1], 
            color=color,
            edgecolors='white'
        )
        
        return (scatter,)
    
    anim = animation.FuncAnimation(
        fig, 
        animate, 
        frames=paths.shape[1], 
        interval=100,
        blit=False,
    )
    
    plt.close()
    return anim