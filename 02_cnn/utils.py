import math
from collections import OrderedDict
from io import BytesIO

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import ImageDraw, ImageColor, ImageFont, Image


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def plot_conv_kernel(w, labels=None):
    cols = math.ceil(math.sqrt(w.shape[3]))
    rows = math.ceil(w.shape[3] / cols)

    if labels is None:
        labels = range(w.shape[3])

    plt.figure(figsize=[2 * cols, 2 * rows])
    for i in range(w.shape[3]):
        wt = w[:, :, :, i]

        # Rescaling so that sigmoid is saturated.
        wt = wt / wt.std()
        wt = sigmoid(wt)

        plt.subplot(rows, cols, i + 1)
        plt.imshow(wt, vmin=0, vmax=1)
        plt.title(labels[i])
        plt.xticks([])
        plt.yticks([])

    plt.show()


def load_from_internet(url):
    # Loading the image from the Internet
    raw_bytes = requests.get(url).content
    return Image.open(BytesIO(raw_bytes))


def load_tiny_batch():
    image_urls = {
        'cat'        : 'https://farm7.staticflickr.com/6152/6150418513_01f9c2927c_z.jpg',
        'dog'        : 'https://farm1.staticflickr.com/52/139518224_136aa37a7d_z.jpg',
        'truck + dog': 'https://farm1.staticflickr.com/36/121456748_96661cebb9_z.jpg',
        'rover'      : 'https://upload.wikimedia.org/wikipedia/commons/d/d8/NASA_Mars_Rover.jpg',
    }
    return OrderedDict({name: load_from_internet(url) for name, url in image_urls.items()})


def crop_and_resize_for_imagenet(image):
    width = image.size[0]
    height = image.size[1]
    aspect = width / float(height)

    ideal_width = 224
    ideal_height = 224
    ideal_aspect = ideal_width / float(ideal_height)

    # https://stackoverflow.com/a/4744625
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
    image = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
    return np.array(image, dtype='uint8')


def plot_image(pixels):
    plt.imshow(pixels)
    plt.yticks([])
    plt.xticks([])


def plot_images_grid(images_raw):
    mpl.rcParams.update({'figure.dpi': 100})

    ncols = 2
    nrows = math.ceil(len(images_raw) / ncols)

    plt.figure(figsize=[15, nrows * 6], dpi=100)
    for idx, name in enumerate(images_raw):
        plt.subplot(nrows, ncols, idx + 1)
        plt.title(name)
        plot_image(images_raw[name])


def display_image(image):
    fig = plt.figure(figsize=[10, 10], dpi=100)
    plt.grid(False)
    plt.yticks([])
    plt.xticks([])
    plt.imshow(image)


# https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
def draw_bounding_box_on_image(image,
                               ymin,
                               xmin,
                               ymax,
                               xmax,
                               color,
                               font,
                               thickness=4,
                               display_str_list=()):
    """Adds a bounding box to an image."""
    draw = ImageDraw.Draw(image)
    im_width, im_height = image.size
    (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                  ymin * im_height, ymax * im_height)
    draw.line([(left, top), (left, bottom), (right, bottom), (right, top),
               (left, top)],
              width=thickness,
              fill=color)

    # If the total height of the display strings added to the top of the bounding
    # box exceeds the top of the image, stack the strings below the bounding box
    # instead of above.
    display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
    # Each display_str has a top and bottom margin of 0.05x.
    total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

    if top > total_display_str_height:
        text_bottom = top
    else:
        text_bottom = bottom + total_display_str_height
    # Reverse list and print from bottom to top.
    for display_str in display_str_list[::-1]:
        text_width, text_height = font.getsize(display_str)
        margin = np.ceil(0.05 * text_height)
        draw.rectangle([(left, text_bottom - text_height - 2 * margin),
                        (left + text_width, text_bottom)],
                       fill=color)
        draw.text((left + margin, text_bottom - text_height - margin),
                  display_str,
                  fill="black",
                  font=font)
        text_bottom -= text_height - 2 * margin


# https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
def draw_boxes(image, boxes, class_names, scores, max_boxes=10, min_score=0.1):
    """Overlay labeled boxes on an image with formatted scores and label names."""
    colors = list(ImageColor.colormap.values())
    font = ImageFont.load_default()

    for i in range(min(boxes.shape[0], max_boxes)):
        if scores[i] < min_score:
            continue

        ymin, xmin, ymax, xmax = tuple(boxes[i].tolist())
        display_str = "{}: {}%".format(
            class_names[i].decode("ascii"),
            int(100 * scores[i])
        )

        color = colors[hash(class_names[i]) % len(colors)]

        image_pil = Image.fromarray(np.uint8(image)).convert("RGB")
        draw_bounding_box_on_image(
            image_pil,
            ymin,
            xmin,
            ymax,
            xmax,
            color,
            font,
            display_str_list=[display_str]
        )

        np.copyto(image, np.array(image_pil))

    return image

def sigmoid(x):
    return np.exp(x) / (1 + np.exp(x))


def plot_activation_map(am):
    std = am.std()
    
    if std != 0:
        am /= std
        
    am = sigmoid(am)
    plt.imshow(
        am, 
        vmin=0, 
        vmax=1, 
        cmap=plt.get_cmap('RdYlGn')
    )
    plt.xticks([])
    plt.yticks([])

def plot_activation_volume(av, side=3):
    activation_depth = av.shape[-1]
    nrows = side
    ncols = side
    idxs = np.linspace(0, activation_depth-1, nrows*ncols).round().astype(int)

    plt.figure(figsize=[4 * ncols, 4 * nrows])
    for i, idx in enumerate(idxs):
        current_av = av[:, :, idx]
        plt.subplot(nrows, ncols, i+1)
        plt.title(f'channel = {idx}')
        plot_activation_map(current_av)
        
    plt.show()
    
def plot_gradient(grad):
    grad /= grad.std()
    grad = sigmoid(grad)
    plt.imshow(grad)
    plt.xticks([])
    plt.yticks([])