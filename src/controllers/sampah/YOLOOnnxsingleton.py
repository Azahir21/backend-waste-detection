import threading

from src.controllers.sampah.yolov8seg import YOLOv8Seg


class YOLOOnnxSingleton:
    _instances = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, model_path: str, yaml_path: str = None):
        with cls._lock:
            if model_path not in cls._instances:
                cls._instances[model_path] = YOLOv8Seg(model_path, yaml_path)
                print(f"Loaded ONNX model from {model_path}")
            return cls._instances[model_path]
