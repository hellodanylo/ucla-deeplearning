from utils.string_int_label_map_pb2 import StringIntLabelMap
import google.protobuf
import pandas as pd

def load_class_map():
    
    with open('./utils/mscoco_label_map.pbtxt') as f:
        classes_map = google.protobuf.text_format.Parse(f.read(), StringIntLabelMap())

    classes_map = pd.DataFrame(
        [(i.id, i.display_name) for i in classes_map.item], 
        columns=['id', 'label']
    )
    classes_map = classes_map.set_index('id')
    
    return classes_map