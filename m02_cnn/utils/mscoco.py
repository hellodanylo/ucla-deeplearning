from pathlib import Path

import pandas as pd
from google.protobuf import text_format

try:
    from .string_int_label_map_pb2 import StringIntLabelMap
except ImportError:
    # Imported as a top-level module (`from mscoco import ...` from inside utils/)
    from string_int_label_map_pb2 import StringIntLabelMap

UTILS_DIR = Path(__file__).parent


def load_class_map():

    with open(UTILS_DIR / 'mscoco_label_map.pbtxt') as f:
        classes_map = text_format.Parse(f.read(), StringIntLabelMap())

    classes_map = pd.DataFrame(
        [(i.id, i.display_name) for i in classes_map.item], 
        columns=['id', 'label']
    )
    classes_map = classes_map.set_index('id')
    
    return classes_map
