import math
import matplotlib.pyplot as plt

def plot_images_grid(images, classes, dictionary):
    """
    Plots the dictionary of images as a grid.
    
    The dictionary's keys will be used as titles,
    while the values are expected to be images.
    
    :param images: dictionary of images
    """

    ncols = 2
    nrows = math.ceil(len(images) / ncols)

    plt.figure(figsize=[15, nrows * 6])
    
    for idx, (image, class_id) in enumerate(zip(images, classes)):
        class_label = dictionary.iloc[class_id]
        
        plt.subplot(nrows, ncols, idx + 1)
        plt.title(class_label)
        plot_image(image)
        
        
def plot_image(pixels):
    """
    Simply plots an image from its pixels.
    Pixel values must be either integers in [0, 255], or floats in [0, 1].
    """
    plt.imshow(pixels)
    plt.yticks([])
    plt.xticks([])