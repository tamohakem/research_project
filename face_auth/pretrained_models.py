import logging

import cv2
import numpy as np

from .fasiva import (
    ANTI_SPOOFING_THRESHOLD,
    PRETRAINED_FACE_MODEL_NAME,
    USE_PRETRAINED_FACE_MODEL,
)

logger = logging.getLogger(__name__)


class PretrainedBiometricModels:
    """Optional pretrained ArcFace and anti-spoofing adapters."""

    def __init__(self):
        self.face_app = None
        self.face_error = None
        self.anti_spoof_error = None

    def arcface_embedding(self, image_bgr):
        if not USE_PRETRAINED_FACE_MODEL:
            return None, 'disabled'

        app, error = self._get_face_app()
        if error:
            return None, error

        try:
            faces = app.get(image_bgr)
        except Exception as exc:
            logger.warning("ArcFace embedding failed: %s", exc)
            return None, str(exc)

        if len(faces) != 1:
            return None, f'Expected one face for ArcFace, found {len(faces)}'

        embedding = np.asarray(faces[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return None, 'ArcFace produced an empty embedding'

        return embedding / norm, None

    def anti_spoof(self, image_bgr):
        try:
            from deepface import DeepFace
        except ModuleNotFoundError as exc:
            self.anti_spoof_error = f'Missing optional anti-spoofing dependency: {exc.name}'
            return {
                'available': False,
                'is_real': None,
                'score': None,
                'error': self.anti_spoof_error,
            }

        try:
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            faces = DeepFace.extract_faces(
                img_path=image_rgb,
                detector_backend='opencv',
                enforce_detection=False,
                anti_spoofing=True,
            )
        except Exception as exc:
            self.anti_spoof_error = str(exc)
            logger.warning("Anti-spoofing failed: %s", exc)
            return {
                'available': False,
                'is_real': None,
                'score': None,
                'error': str(exc),
            }

        if not faces:
            return {
                'available': True,
                'is_real': False,
                'score': 0.0,
                'error': 'No face found by anti-spoofing model',
            }

        result = faces[0]
        is_real = result.get('is_real')
        score = result.get('antispoof_score')

        if is_real is None and score is not None:
            is_real = float(score) >= ANTI_SPOOFING_THRESHOLD

        return {
            'available': True,
            'is_real': bool(is_real) if is_real is not None else None,
            'score': round(float(score), 4) if score is not None else None,
            'error': None,
        }

    def _get_face_app(self):
        if self.face_error:
            return None, self.face_error

        if self.face_app is not None:
            return self.face_app, None

        try:
            from insightface.app import FaceAnalysis
        except ModuleNotFoundError as exc:
            self.face_error = f'Missing optional ArcFace dependency: {exc.name}'
            return None, self.face_error

        try:
            app = FaceAnalysis(name=PRETRAINED_FACE_MODEL_NAME)
            app.prepare(ctx_id=-1, det_size=(640, 640))
            self.face_app = app
            return self.face_app, None
        except Exception as exc:
            self.face_error = str(exc)
            logger.warning("ArcFace model initialization failed: %s", exc)
            return None, self.face_error


pretrained_models = PretrainedBiometricModels()
