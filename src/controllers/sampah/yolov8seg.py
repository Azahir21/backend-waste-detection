import os
import cv2
import numpy as np
import onnxruntime as ort
from ultralytics.utils import ASSETS, yaml_load
from ultralytics.utils.checks import check_yaml
from ultralytics.utils.plotting import Colors


class YOLOv8Seg:
    """YOLOv8 segmentation model."""

    def __init__(self, onnx_model, yaml_path=None):
        self.session = ort.InferenceSession(
            onnx_model,
            providers=(
                ["CUDAExecutionProvider", "CPUExecutionProvider"]
                if ort.get_device() == "GPU"
                else ["CPUExecutionProvider"]
            ),
        )
        self.ndtype = (
            np.half
            if self.session.get_inputs()[0].type == "tensor(float16)"
            else np.single
        )
        self.model_height, self.model_width = [
            x.shape for x in self.session.get_inputs()
        ][0][-2:]
        self.classes = yaml_load(check_yaml(yaml_path or "data.yaml"))["names"]
        self.color_palette = Colors()

    def __call__(self, im0, conf_threshold=0.4, iou_threshold=0.45, nm=32):
        im, ratio, (pad_w, pad_h) = self.preprocess(im0)
        preds = self.session.run(None, {self.session.get_inputs()[0].name: im})
        boxes, segments, masks = self.postprocess(
            preds,
            im0=im0,
            ratio=ratio,
            pad_w=pad_w,
            pad_h=pad_h,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            nm=nm,
        )
        return boxes, segments, masks

    def preprocess(self, img):
        shape = img.shape[:2]
        new_shape = (self.model_height, self.model_width)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        ratio = r, r
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        pad_w, pad_h = (new_shape[1] - new_unpad[0]) / 2, (
            new_shape[0] - new_unpad[1]
        ) / 2
        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
        left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        img = (
            np.ascontiguousarray(np.einsum("HWC->CHW", img)[::-1], dtype=self.ndtype)
            / 255.0
        )
        img_process = img[None] if len(img.shape) == 3 else img
        return img_process, ratio, (pad_w, pad_h)

    def postprocess(
        self, preds, im0, ratio, pad_w, pad_h, conf_threshold, iou_threshold, nm=32
    ):
        x, protos = preds[0], preds[1]
        x = np.einsum("bcn->bnc", x)
        x = x[np.amax(x[..., 4:-nm], axis=-1) > conf_threshold]
        x = np.c_[
            x[..., :4],
            np.amax(x[..., 4:-nm], axis=-1),
            np.argmax(x[..., 4:-nm], axis=-1),
            x[..., -nm:],
        ]
        x = x[cv2.dnn.NMSBoxes(x[:, :4], x[:, 4], conf_threshold, iou_threshold)]
        if len(x) > 0:
            x[..., [0, 1]] -= x[..., [2, 3]] / 2
            x[..., [2, 3]] += x[..., [0, 1]]
            x[..., :4] -= [pad_w, pad_h, pad_w, pad_h]
            x[..., :4] /= min(ratio)
            x[..., [0, 2]] = x[:, [0, 2]].clip(0, im0.shape[1])
            x[..., [1, 3]] = x[:, [1, 3]].clip(0, im0.shape[0])
            masks = self.process_mask(protos[0], x[:, 6:], x[:, :4], im0.shape)
            segments = self.masks2segments(masks)
            return x[..., :6], segments, masks
        else:
            return [], [], []

    @staticmethod
    def masks2segments(masks):
        segments = []
        for x in masks.astype("uint8"):
            c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
            if c:
                c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
            else:
                c = np.zeros((0, 2))
            segments.append(c.astype("float32"))
        return segments

    @staticmethod
    def crop_mask(masks, boxes):
        n, h, w = masks.shape
        x1, y1, x2, y2 = np.split(boxes[:, :, None], 4, 1)
        r = np.arange(w, dtype=x1.dtype)[None, None, :]
        c = np.arange(h, dtype=x1.dtype)[None, :, None]
        return masks * ((r >= x1) * (r < x2) * (c >= y1) * (c < y2))

    def process_mask(self, protos, masks_in, bboxes, im0_shape):
        c, mh, mw = protos.shape
        masks = (
            np.matmul(masks_in, protos.reshape((c, -1)))
            .reshape((-1, mh, mw))
            .transpose(1, 2, 0)
        )
        masks = np.ascontiguousarray(masks)
        masks = self.scale_mask(masks, im0_shape)
        masks = np.einsum("HWN -> NHW", masks)
        masks = self.crop_mask(masks, bboxes)
        return np.greater(masks, 0.5)

    @staticmethod
    def scale_mask(masks, im0_shape, ratio_pad=None):
        im1_shape = masks.shape[:2]
        if ratio_pad is None:
            gain = min(im1_shape[0] / im0_shape[0], im1_shape[1] / im0_shape[1])
            pad = (im1_shape[1] - im0_shape[1] * gain) / 2, (
                im1_shape[0] - im0_shape[0] * gain
            ) / 2
        else:
            pad = ratio_pad[1]
        top, left = int(round(pad[1] - 0.1)), int(round(pad[0] - 0.1))
        bottom, right = int(round(im1_shape[0] - pad[1] + 0.1)), int(
            round(im1_shape[1] - pad[0] + 0.1)
        )
        if len(masks.shape) < 2:
            raise ValueError(
                f'"len of masks shape" should be 2 or 3, but got {len(masks.shape)}'
            )
        masks = masks[top:bottom, left:right]
        masks = cv2.resize(
            masks, (im0_shape[1], im0_shape[0]), interpolation=cv2.INTER_LINEAR
        )
        if len(masks.shape) == 2:
            masks = masks[:, :, None]
        return masks

    def draw_and_visualize(
        self,
        im,
        bboxes,
        segments,
        vis=False,
        save=True,
        output_folder="output",
        filename="demo.jpg",
    ):
        os.makedirs(output_folder, exist_ok=True)
        im_canvas = im.copy()

        for (*box, conf, cls_), segment in zip(bboxes, segments):
            cls_int = int(cls_)
            color = self.color_palette(cls_int, bgr=True)  # Warna solid untuk BBOX

            # Gambar contour segmentasi dengan garis putih sebagai border
            cv2.polylines(
                im_canvas, np.int32([segment]), True, (255, 255, 255), 3, cv2.LINE_AA
            )
            # Isi area segmentasi dengan warna dari palette
            overlay = im_canvas.copy()
            cv2.fillPoly(overlay, np.int32([segment]), color)
            alpha = 0.4  # Transparansi
            cv2.addWeighted(overlay, alpha, im_canvas, 1 - alpha, 0, im_canvas)

            # Gambar bounding box dengan warna solid dan garis tebal
            cv2.rectangle(
                im_canvas,
                (int(box[0]), int(box[1])),
                (int(box[2]), int(box[3])),
                color,
                thickness=10,  # Dibuat lebih tebal
                lineType=cv2.LINE_AA,
            )

            # Buat teks label dengan background solid
            label = f"{self.classes[cls_int]}: {conf:.3f}"
            font_scale = 2.0
            font_thickness = 3
            (w, h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
            )

            # Posisi label
            pt1 = (int(box[0]), int(box[1] - h - baseline - 6))
            pt2 = (int(box[0] + w + 6), int(box[1]))

            # Gambar background label dengan warna solid
            cv2.rectangle(im_canvas, pt1, pt2, color, thickness=-1)

            # Tulis teks label dengan warna putih agar lebih kontras
            cv2.putText(
                im_canvas,
                label,
                (int(box[0] + 3), int(box[1] - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),  # Warna teks putih
                font_thickness,
                cv2.LINE_AA,
            )

        # Tampilkan atau simpan gambar hasil anotasi
        if vis:
            cv2.imshow("Detection", im_canvas)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if save:
            cv2.imwrite(os.path.join(output_folder, filename), im_canvas)

    def get_names(self, idx):
        return self.classes[int(idx)]
