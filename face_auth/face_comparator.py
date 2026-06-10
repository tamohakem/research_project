import logging

import cv2
import numpy as np

from .fasiva import (
    EDGE_SCORE_THRESHOLD,
    HISTOGRAM_SCORE_THRESHOLD,
    LBP_SCORE_THRESHOLD,
    MATCH_CONFIDENCE_THRESHOLD,
    MAX_FACE_BRIGHTNESS,
    MIN_FACE_BRIGHTNESS,
    MIN_FACE_SHARPNESS,
    SUPPORTING_SCORE_THRESHOLD,
    VECTOR_SCORE_THRESHOLD,
)

try:
    from mtcnn import MTCNN
except ModuleNotFoundError:
    MTCNN = None

logger = logging.getLogger(__name__)


class FaceComparator:
    """Face comparator with strict multi-feature matching."""

    def __init__(self):
        self.detector = MTCNN() if MTCNN is not None else None
        self.last_match_details = {}
        self.last_liveness_details = {}
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )

    def extract_face_encoding(self, image_input):
        """
        Extract face features from image.
        Returns: (features_dict, success, message)
        """
        try:
            img = self._load_image(image_input)
            if img is None:
                return None, False, "Could not load image"

            faces = self._detect_faces(img)
            if not faces:
                return None, False, "No face detected in the image"

            if len(faces) > 1:
                return None, False, f"Multiple faces ({len(faces)}) detected. Please use a single face image"

            x, y, w, h = faces[0]
            x, y = max(0, x), max(0, y)
            image_h, image_w = img.shape[:2]
            w = min(w, image_w - x)
            h = min(h, image_h - y)

            face_roi = img[y:y + h, x:x + w]
            if face_roi.size == 0:
                return None, False, "Invalid face region extracted"

            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray_face = cv2.resize(gray_face, (128, 128))
            gray_face = cv2.equalizeHist(gray_face)

            sobel_x = cv2.Sobel(gray_face, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray_face, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

            histogram = cv2.calcHist([gray_face], [0], None, [128], [0, 256])
            histogram = cv2.normalize(histogram, histogram).flatten()

            face_vector = gray_face.astype(np.float32).flatten() / 255.0
            face_vector = (face_vector - np.mean(face_vector)) / (np.std(face_vector) + 1e-6)

            encoding = {
                'version': 2,
                'histogram': histogram,
                'lbp': self._extract_lbp_features(gray_face),
                'face_vector': face_vector,
                'magnitude_mean': float(np.mean(magnitude)),
                'magnitude_std': float(np.std(magnitude)),
                'face_box': (int(x), int(y), int(w), int(h)),
            }

            return encoding, True, "Face detected successfully"

        except Exception as exc:
            logger.error("Face extraction error: %s", exc)
            return None, False, f"Error: {exc}"

    def _load_image(self, image_input):
        if isinstance(image_input, np.ndarray):
            return image_input

        if isinstance(image_input, str):
            return cv2.imread(image_input)

        img_bytes = image_input.read() if hasattr(image_input, 'read') else image_input
        nparr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _detect_faces(self, img):
        """Return face boxes as (x, y, w, h), using OpenCV if MTCNN is not installed."""
        if self.detector is not None:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.detector.detect_faces(rgb_img)
            return [tuple(face['box']) for face in faces]

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(80, 80),
        )
        return [tuple(face) for face in faces]

    def _extract_lbp_features(self, gray_image):
        rows, cols = gray_image.shape
        lbp = np.zeros((rows - 2, cols - 2), dtype=np.uint8)

        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = gray_image[i, j]
                code = 0
                code |= (gray_image[i - 1, j - 1] >= center) << 7
                code |= (gray_image[i - 1, j] >= center) << 6
                code |= (gray_image[i - 1, j + 1] >= center) << 5
                code |= (gray_image[i, j + 1] >= center) << 4
                code |= (gray_image[i + 1, j + 1] >= center) << 3
                code |= (gray_image[i + 1, j] >= center) << 2
                code |= (gray_image[i + 1, j - 1] >= center) << 1
                code |= (gray_image[i, j - 1] >= center) << 0
                lbp[i - 1, j - 1] = code

        hist = cv2.calcHist([lbp], [0], None, [256], [0, 256])
        return cv2.normalize(hist, hist).flatten()

    def compare_faces(self, known_encoding, unknown_encoding):
        """
        Compare two face encodings using multiple metrics.
        Returns: (match, distance, confidence_percentage)
        """
        if known_encoding is None or unknown_encoding is None:
            return False, 1.0, 0.0

        try:
            known_encoding = self._upgrade_legacy_encoding(known_encoding)
            unknown_encoding = self._upgrade_legacy_encoding(unknown_encoding)

            known_hist = known_encoding.get('histogram')
            unknown_hist = unknown_encoding.get('histogram')
            known_lbp = known_encoding.get('lbp')
            unknown_lbp = unknown_encoding.get('lbp')
            known_vector = known_encoding.get('face_vector')
            unknown_vector = unknown_encoding.get('face_vector')

            if any(value is None for value in (
                known_hist, unknown_hist, known_lbp, unknown_lbp, known_vector, unknown_vector
            )):
                return False, 1.0, 0.0

            hist_score = self._histogram_score(known_hist, unknown_hist)
            lbp_score = self._histogram_score(known_lbp, unknown_lbp)
            vector_score = self._correlation_score(known_vector, unknown_vector)
            edge_score = self._edge_score(known_encoding, unknown_encoding)

            confidence = (
                vector_score * 0.35
                + lbp_score * 0.50
                + hist_score * 0.05
                + edge_score * 0.10
            ) * 100

            supporting_score = max(hist_score, edge_score)
            distance = 1 - (confidence / 100)
            self.last_match_details = {
                'confidence': round(confidence, 2),
                'vector_score': round(vector_score, 4),
                'lbp_score': round(lbp_score, 4),
                'histogram_score': round(hist_score, 4),
                'edge_score': round(edge_score, 4),
                'supporting_score': round(supporting_score, 4),
                'thresholds': {
                    'confidence': MATCH_CONFIDENCE_THRESHOLD,
                    'vector_score': VECTOR_SCORE_THRESHOLD,
                    'lbp_score': LBP_SCORE_THRESHOLD,
                    'histogram_score': HISTOGRAM_SCORE_THRESHOLD,
                    'edge_score': EDGE_SCORE_THRESHOLD,
                    'supporting_score': SUPPORTING_SCORE_THRESHOLD,
                },
            }
            match = (
                confidence >= MATCH_CONFIDENCE_THRESHOLD
                and vector_score >= VECTOR_SCORE_THRESHOLD
                and lbp_score >= LBP_SCORE_THRESHOLD
                and supporting_score >= SUPPORTING_SCORE_THRESHOLD
            )

            return match, distance, confidence

        except Exception as exc:
            logger.error("Face comparison error: %s", exc)
            return False, 1.0, 0.0

    def _upgrade_legacy_encoding(self, encoding):
        if encoding.get('face_vector') is not None:
            return encoding

        face_roi = encoding.get('face_roi')
        if face_roi is None:
            return encoding

        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        gray_face = cv2.resize(gray_face, (128, 128))
        gray_face = cv2.equalizeHist(gray_face)
        face_vector = gray_face.astype(np.float32).flatten() / 255.0
        face_vector = (face_vector - np.mean(face_vector)) / (np.std(face_vector) + 1e-6)
        encoding['face_vector'] = face_vector
        if encoding.get('lbp') is None:
            encoding['lbp'] = self._extract_lbp_features(gray_face)
        return encoding

    def _histogram_score(self, known, unknown):
        score = cv2.compareHist(
            known.astype(np.float32),
            unknown.astype(np.float32),
            cv2.HISTCMP_CORREL,
        )
        return max(0.0, min(1.0, float(score)))

    def _correlation_score(self, known, unknown):
        score = float(np.corrcoef(known, unknown)[0, 1])
        if np.isnan(score):
            return 0.0
        return max(0.0, min(1.0, score))

    def _edge_score(self, known_encoding, unknown_encoding):
        known_mean = float(known_encoding.get('magnitude_mean', 0.0))
        unknown_mean = float(unknown_encoding.get('magnitude_mean', 0.0))
        known_std = float(known_encoding.get('magnitude_std', 0.0))
        unknown_std = float(unknown_encoding.get('magnitude_std', 0.0))

        mean_diff = abs(known_mean - unknown_mean) / max(known_mean, unknown_mean, 1.0)
        std_diff = abs(known_std - unknown_std) / max(known_std, unknown_std, 1.0)
        return max(0.0, 1.0 - ((mean_diff + std_diff) / 2.0))

    def detect_liveness(self, frame):
        try:
            faces = self._detect_faces(frame)
            if len(faces) != 1:
                self.last_liveness_details = {
                    'face_count': len(faces),
                    'brightness': None,
                    'sharpness': None,
                    'eye_count': 0,
                    'quality_passed': False,
                }
                return False, 0.2

            face_roi = self._crop_face(frame, faces[0])
            if face_roi.size == 0:
                return False, 0.2

            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            brightness = float(np.mean(gray_face))
            sharpness = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
            eye_count = self._eye_count(gray_face)

            brightness_ok = MIN_FACE_BRIGHTNESS <= brightness <= MAX_FACE_BRIGHTNESS
            sharpness_ok = sharpness >= MIN_FACE_SHARPNESS

            confidence = 0.35
            if brightness_ok:
                confidence += 0.30
            if sharpness_ok:
                confidence += 0.30
            if face_roi.shape[1] >= 80 and face_roi.shape[0] >= 80:
                confidence += 0.05

            self.last_liveness_details = {
                'face_count': len(faces),
                'brightness': round(brightness, 2),
                'sharpness': round(sharpness, 2),
                'eye_count': int(eye_count),
                'quality_passed': bool(brightness_ok and sharpness_ok),
                'brightness_range': [MIN_FACE_BRIGHTNESS, MAX_FACE_BRIGHTNESS],
                'minimum_sharpness': MIN_FACE_SHARPNESS,
            }
            return brightness_ok and sharpness_ok, min(confidence, 1.0)

        except Exception as exc:
            logger.error("Liveness detection error: %s", exc)
            self.last_liveness_details = {'error': str(exc), 'quality_passed': False}
            return False, 0.0

    def analyze_blink_evidence(self, open_frame, blink_frame):
        try:
            open_count = self._frame_eye_count(open_frame)
            blink_count = self._frame_eye_count(blink_frame)
            blink_detected = open_count > blink_count
            return {
                'open_frame_eye_count': int(open_count),
                'blink_frame_eye_count': int(blink_count),
                'blink_detected': bool(blink_detected),
                'available': True,
            }
        except Exception as exc:
            logger.error("Blink evidence error: %s", exc)
            return {
                'available': False,
                'blink_detected': False,
                'error': str(exc),
            }

    def _crop_face(self, frame, face_box):
        x, y, w, h = face_box
        x, y = max(0, x), max(0, y)
        image_h, image_w = frame.shape[:2]
        w = min(w, image_w - x)
        h = min(h, image_h - y)
        return frame[y:y + h, x:x + w]

    def _frame_eye_count(self, frame):
        faces = self._detect_faces(frame)
        if len(faces) != 1:
            return 0
        face_roi = self._crop_face(frame, faces[0])
        if face_roi.size == 0:
            return 0
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        return self._eye_count(gray_face)

    def _eye_count(self, gray_face):
        eyes = self.eye_cascade.detectMultiScale(gray_face, 1.1, 8)
        return len(eyes)


face_comparator = FaceComparator()
