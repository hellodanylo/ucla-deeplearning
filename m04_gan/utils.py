import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

try:
    get_ipython().run_line_magic('config', 'InlineBackend.figure_format = "retina"')
except:
    pass

def plot_strided_grid(images, ncols=5, nrows=5):
    """
    Plots some of the images in a grid of given size.
    
    Applies a stride that makes the count of images
    match the count of cells in the grid.
    """
    n_images = images.shape[0]
    n_cells = ncols * nrows
    
    idxs = np.linspace(0, n_images-1, n_cells)
    idxs = idxs.round().astype(int)

    fig = plt.figure(figsize=[2*ncols, 2*nrows])
    fig.subplots_adjust(hspace=0, wspace=0)

    for cell_id, image_id in enumerate(idxs):
        plt.subplot(nrows, ncols, cell_id+1)
        plt.title(image_id)
        plt.imshow(images[image_id])
        plt.xticks([])
        plt.yticks([])

    plt.tight_layout()
    

def save_images(images, prefix):
    """
    Saves the images to a local folder.
    Use gif.sh script to animate the images.
    """
    
    previous_folders = [
        int(n.split(prefix)[1]) for n in os.listdir('.') 
        if n.startswith(prefix)
    ]

    if len(previous_folders) > 0:
        next_id = max(previous_folders) + 1
    else:
        next_id = 0

    folder = f'{prefix}{next_id}'
    os.system(f'mkdir -p {folder}')
    
    for idx, image in enumerate(images):
        Image.fromarray(image.astype('uint8')).save(f'{folder}/{idx}.png')

    print(f'Images are saved to {folder}')
    return folder