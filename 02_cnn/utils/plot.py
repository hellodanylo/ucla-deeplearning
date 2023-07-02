import math
from io import BytesIO
from typing import List, Text, Dict, Mapping, Tuple, Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import requests
import tensorflow as tf
from PIL import ImageDraw, ImageFont, Image
from PIL.ImageFont import FreeTypeFont
from cachetools import LRUCache, cached

try:
    get_ipython().run_line_magic('config', 'InlineBackend.figure_format = "retina"')
except:
    pass

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def plot_conv_kernel(w: np.ndarray, labels: List[Text] = None, side_inches: int = 2):
    """
    Plots the kernel weights as a grid of images.
    The input's shape must be (height, weight, input channels, output channels).
    If the input is 3-dimensional, it's assumed to have 1 output channel.
    
    Before plotting, this function rescales the kernel
    by making its std = 1, so that pixel values are significantly different.
    Finally, it applies sigmoid activation to fit the weights into (0, 1) range.
    
    :param side_inches:
    :param w: the kernel to plot
    :param labels: optional list of labels for each output channel
    """

    if len(w.shape) == 3:
        w = np.expand_dims(w, -1)
    elif len(w.shape) != 4:
        raise Exception("Kernel must be either 3- or 4-dimensional array")

    cols = math.ceil(math.sqrt(w.shape[3]))
    rows = math.ceil(w.shape[3] / cols)

    if labels is None:
        labels = range(w.shape[3])

    plt.figure(figsize=[side_inches * cols, side_inches * rows])
    for i in range(w.shape[3]):
        wt = w[:, :, :, i]

        # Rescaling so that sigmoid is saturated.
        wt = wt / tf.math.reduce_std(wt)
        wt = sigmoid(wt)

        plt.subplot(rows, cols, i + 1)
        plt.imshow(wt, vmin=0, vmax=1)
        plt.title(labels[i])
        plt.xticks([])
        plt.yticks([])

    plt.show()


def plot_activation_map(am: np.ndarray):
    """
    Plots the activation map as a color-coded image.
    
    Red colors correspond to negative activation, green colors - positive.
    To make pixel values different from each other, activation is rescaled to std = 1.
    
    :param am: the activation map of shape (height, width)
    """
    std = am.std()

    if std != 0:
        am /= std

    am = sigmoid(am)

    plt.imshow(am, vmin=0, vmax=1, cmap=plt.get_cmap("RdYlGn"))
    plt.xticks([])
    plt.yticks([])


def plot_activation_volume(av: np.ndarray, side=3):
    """
    Plots the activation volume as a grid of color-coded images.
    See plot_activation_map for details on color-coding.
    
    Note that the grid will consist of side*side cells.
    If the activation volume has more channels than that,
    they will be plotted with a stride that makes
    the count of channels match the count of grid cells.
    
    :param av: the activation map of shape (height, width, channels)
    :param side: size of a single row/column of the grid
    """
    activation_depth = av.shape[-1]
    nrows = side
    ncols = side

    # Applies a stride that makes the count of channels
    # match the count of cells in the gtid.
    channels = np.linspace(0, activation_depth - 1, nrows * ncols)
    channels = channels.round().astype(int)

    plt.figure(figsize=[4 * ncols, 4 * nrows])

    for idx, channel in enumerate(channels):
        current_av = av[:, :, channel]

        plt.subplot(nrows, ncols, idx + 1)
        plt.title(f"channel = {channel}")
        plot_activation_map(current_av)

    plt.show()


def plot_gradient(grad: np.ndarray) -> None:
    """
    Plots the gradient as an image.
    
    Gradient values will be rescaled to std = 1,
    and sigmoid will be appplied before plotting.
    
    :param grad: an array of shape (height, width)
    """
    grad /= grad.std()
    grad = sigmoid(grad)
    plt.imshow(grad)
    plt.xticks([])
    plt.yticks([])


def load_from_internet(url: Text) -> Image.Image:
    """
    Loads an image by URL.
    """
    raw_bytes = requests.get(url).content
    return Image.open(BytesIO(raw_bytes))


@cached(cache=LRUCache(maxsize=1))
def load_tiny_batch() -> Dict[Text, Image.Image]:
    """
    Loads a tiny batch of images.
    """
    image_urls = {
        "cat": "https://farm7.staticflickr.com/6152/6150418513_01f9c2927c_z.jpg",
        "dog": "https://farm1.staticflickr.com/52/139518224_136aa37a7d_z.jpg",
        "truck + dog": "https://farm1.staticflickr.com/36/121456748_96661cebb9_z.jpg",
        "rover": "https://github.com/hellodanylo/ucla-deeplearning/raw/master/02_cnn/utils/images/600px-NASA_Mars_Rover.jpg",
    }
    return {name: load_from_internet(url) for name, url in image_urls.items()}


def crop_and_resize_for_imagenet(image: Image.Image) -> np.ndarray:
    """
    Crops and resizes the image into the shape
    expected by ImageNet models.
    
    Source: https://stackoverflow.com/a/4744625
    """
    width = image.size[0]
    height = image.size[1]
    aspect = width / float(height)

    ideal_width = 224
    ideal_height = 224
    ideal_aspect = ideal_width / float(ideal_height)

    if aspect > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * height)
        offset = (width - new_width) / 2
        resize = (offset, 0, width - offset, height)
    else:
        # ... crop the top and bottom:
        new_height = int(width / ideal_aspect)
        offset = (height - new_height) / 2
        resize = (0, offset, width, height - offset)

    # ImageNet images are 224x244x3 array of type uint8 [0, 255]
    image = image.crop(resize).resize((ideal_width, ideal_height), Image.Resampling.LANCZOS)
    return np.array(image, dtype="uint8")


def plot_image(pixels: np.ndarray, figsize: Sequence[int] = None) -> None:
    """
    Simply plots an image from its pixels.
    Pixel values must be either integers in [0, 255], or floats in [0, 1].
    """
    if figsize is not None:
        plt.figure(figsize=figsize)

    plt.imshow(pixels)
    plt.yticks([])
    plt.xticks([])


def plot_images_grid(images: Mapping[Text, np.ndarray]) -> None:
    """
    Plots the dictionary of images as a grid.
    
    The dictionary's keys will be used as titles,
    while the values are expected to be images.
    
    :param images: dictionary of images
    """

    ncols = 2
    nrows = math.ceil(len(images) / ncols)

    plt.figure(figsize=[15, nrows * 6], dpi=100)

    for idx, name in enumerate(images):
        plt.subplot(nrows, ncols, idx + 1)
        plt.title(name)
        plot_image(images[name])


def draw_bounding_box_on_image(
    image: Image.Image,
    ymin: int,
    xmin: int,
    ymax: int,
    xmax: int,
    color: Tuple[int],
    font: FreeTypeFont,
    thickness: int = 4,
    display_str_list: List[Text] = [],
):
    """
    Adds a bounding box to an image.
    
    Adapted from:
    https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
    """
    draw = ImageDraw.Draw(image)  # type: ImageDraw.ImageDraw
    im_width, im_height = image.size
    (left, right, top, bottom) = (
        xmin * im_width,
        xmax * im_width,
        ymin * im_height,
        ymax * im_height,
    )
    draw.line(
        [(left, top), (left, bottom), (right, bottom), (right, top), (left, top)],
        width=thickness,
        fill=color,
    )

    # If the total height of the display strings added to the top of the bounding
    # box exceeds the top of the image, stack the strings below the bounding box
    # instead of above.
    display_str_heights = [abs(font.getbbox(ds)[1] - font.getbbox(ds)[3]) for ds in display_str_list]
    # Each display_str has a top and bottom margin of 0.05x.
    total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

    if top > total_display_str_height:
        text_bottom = top
    else:
        text_bottom = bottom + total_display_str_height
    # Reverse list and print from bottom to top.
    for display_str in display_str_list[::-1]:
        _, _, text_width, text_height = font.getbbox(display_str)
        margin = np.ceil(0.05 * text_height)
        draw.rectangle(
            [
                (left, text_bottom - text_height - 2 * margin),
                (left + text_width, text_bottom),
            ],
            fill=color,
        )
        draw.text(
            (left + margin, text_bottom - text_height - margin),
            display_str,
            fill="black",
            font=font,
        )
        text_bottom -= text_height - 2 * margin


def draw_boxes(
    image: np.ndarray,  # = [image, height, width, [r, g, b]]
    boxes: np.ndarray,  # = [image, [ymin, xmin, ymax, xmax]]
    class_names: Sequence[Text],
    scores: Sequence[float],
    max_boxes: int = 10,
    min_score: float = 0.1,
    font_size: int = 20,
) -> np.ndarray:
    """
    Overlay labeled boxes on an image with formatted scores and label names.
    
    Adapted from:
    https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
    """
    cmap = mpl.cm.get_cmap("tab20")
    colors = [tuple((np.array(cmap(i))[:3] * 255).astype(int)) for i in range(20)]

    font = ImageFont.truetype("./utils/Roboto-Regular.ttf", size=font_size)
    image_pil = Image.fromarray(np.uint8(image)).convert("RGB")

    for i in range(min(boxes.shape[0], max_boxes)):
        if scores[i] < min_score:
            continue

        ymin, xmin, ymax, xmax = tuple(boxes[i])
        display_str = "{}: {}%".format(class_names[i], int(100 * scores[i]))

        color = colors[hash(class_names[i]) % len(colors)]

        draw_bounding_box_on_image(
            image_pil,
            ymin,
            xmin,
            ymax,
            xmax,
            color,
            font,
            display_str_list=[display_str],
        )

    return np.array(image_pil)
