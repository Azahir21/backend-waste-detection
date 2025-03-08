import cv2
from fastapi import HTTPException

from assets.models.label_mapping_points import LABEL_MAPPING_POINTS
from config.schemas.sampah_schema import CountObject, InputSampahItem
from src.controllers.sampah.YOLOOnnxsingleton import YOLOOnnxSingleton

# Configuration Constants
INPUT_DIR = "assets/original_image"
OUTPUT_DIR = "assets/detected_image"
MODEL_PATH_GARBAGE_PCS = "assets/models/garbage-pcs-yolov8.onnx"
MODEL_PATH_GARBAGE_PILE = "assets/models/garbage-pile-yolov8.onnx"
GARBAGE_PCS_YAML = "assets/models/garbage_pcs_data.yaml"
GARBAGE_PILE_YAML = "assets/models/garbage_pile_data.yaml"

GARBAGE_PCS_MODEL = YOLOOnnxSingleton.get_instance(
    MODEL_PATH_GARBAGE_PCS, GARBAGE_PCS_YAML
)
GARBAGE_PILE_MODEL = YOLOOnnxSingleton.get_instance(
    MODEL_PATH_GARBAGE_PILE, GARBAGE_PILE_YAML
)


def calculate_objects(detected_objects):
    object_summary = {}
    for obj in detected_objects:
        name = obj["name"]
        points = obj["point"]
        if name in object_summary:
            object_summary[name].count += 1
            object_summary[name].point += points
        else:
            object_summary[name] = CountObject(name=name, count=1, point=points)
    return list(object_summary.values())


def process_image(filename: str, use_garbage_pile_model: bool) -> tuple:
    if use_garbage_pile_model:
        model_label = "garbage_pile"
        model = GARBAGE_PILE_MODEL
    else:
        model_label = "garbage_pcs"
        model = GARBAGE_PCS_MODEL
    file_path = f"{INPUT_DIR}/{filename}"
    im = cv2.imread(file_path)
    boxes, segments, masks = model(im)
    detected_objects = []
    filename = f"{model_label}_{filename}"
    if len(boxes) > 0:
        model.draw_and_visualize(
            im,
            boxes,
            segments,
            vis=False,
            save=True,
            output_folder="assets/detected_image",
            filename=filename,
        )
        for i, box in enumerate(boxes):
            class_id = box[5]
            class_name = model.get_names(class_id)
            if use_garbage_pile_model:
                class_name = "Garbage"
                class_id = 60
            detected_objects.append(
                {
                    "name": class_name,
                    "class": class_id,
                    "point": LABEL_MAPPING_POINTS.get(class_name, 0),
                }
            )
        total_point = sum(obj["point"] for obj in detected_objects)
        list_sampah_item = [
            InputSampahItem(jenisSampahId=obj["class"]) for obj in detected_objects
        ]
        return filename, total_point, list_sampah_item
    else:
        raise HTTPException(status_code=400, detail="No object detected")
