"""PyTorch version of pnp_dataset.build_dataset (no TensorFlow dependency).

Reads the images directly from pnp_dataset.zip, so the archive does not need to be extracted.
"""
from typing import Optional
import os
import zipfile

import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision.io import ImageReadMode, decode_jpeg


class PnpDataset(Dataset):
    """Images of the pnp dataset (and optionally their labels) as a map-style PyTorch dataset.

    Each item is an image tensor of shape (3, 224, 224) with dtype uint8 (pixel values 0..255),
    or a pair (image, label) if include_labels is True, where label is a float32 scalar
    (1.0 = the image contains a person, 0.0 = it does not).
    Items are returned in the same order as pnp_dataset.build_dataset.
    """

    def __init__(self, segment: str, limit: Optional[int] = None, include_labels: bool = True, zip_path: str = 'pnp_dataset.zip'):
        self.zip_path = zip_path
        self.include_labels = include_labels
        # Opened lazily in each process (including DataLoader workers):
        # a ZipFile can't be shared between processes, because they would share its file position.
        self._zip: Optional[zipfile.ZipFile] = None
        self._zip_pid: Optional[int] = None

        with zipfile.ZipFile(zip_path) as z:
            self.targets = sorted(p for p in z.namelist() if p.startswith(f'pnp_dataset/{segment}') and p.endswith('.jpg'))
            if limit is not None:
                self.targets = self.targets[:limit]

            self.labels = None
            if include_labels:
                with z.open(f'pnp_dataset/{segment}_y.npy') as f:
                    self.labels = torch.tensor(np.load(f)[:len(self.targets)], dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, index: int):
        if self._zip is None or self._zip_pid != os.getpid():
            self._zip = zipfile.ZipFile(self.zip_path)
            self._zip_pid = os.getpid()
        data = torch.frombuffer(bytearray(self._zip.read(self.targets[index])), dtype=torch.uint8)
        image = decode_jpeg(data, mode=ImageReadMode.RGB)
        if self.labels is not None:
            return image, self.labels[index]
        return image

    def __getstate__(self):
        # Don't pickle the open ZipFile when the dataset is sent to DataLoader workers (spawn start method).
        state = self.__dict__.copy()
        state['_zip'] = None
        state['_zip_pid'] = None
        return state
