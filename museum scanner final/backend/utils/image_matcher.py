import os
import cv2
import numpy as np
from typing import Dict, Tuple, List

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

class ORBMatcher:
    def __init__(self, reference_dir: str, n_features: int = 2000):
        self.reference_dir = reference_dir
        self.orb = cv2.ORB_create(nfeatures=n_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.index = self._build_index()

    def _load_image(self, path: str):
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        # Fallback if Windows unicode path fails imdecode
        if img is None:
            img = cv2.imread(path)
        return img

    def _build_index(self) -> Dict[str, Dict]:
        idx = {}
        for name in os.listdir(self.reference_dir):
            base, ext = os.path.splitext(name)
            if ext.lower() not in ALLOWED_EXTS:
                continue
            label = base.lower()  # use filename as label
            full = os.path.join(self.reference_dir, name)
            img = self._load_image(full)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kps, des = self.orb.detectAndCompute(gray, None)
            if des is None or len(kps) == 0:
                continue
            idx[label] = {
                "path": full,
                "kps": kps,
                "des": des,
                "kp_count": len(kps)
            }
        if not idx:
            raise RuntimeError("No valid reference images found in " + self.reference_dir)
        return idx

    def _good_match_count(self, des_query, des_ref, ratio=0.75) -> int:
        # Lowe's ratio test
        matches = self.bf.knnMatch(des_query, des_ref, k=2)
        good = 0
        for m, n in matches:
            if m.distance < ratio * n.distance:
                good += 1
        return good

    def match(self, img_bgr) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Returns best_label, score, top list of (label, score)."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        kps_q, des_q = self.orb.detectAndCompute(gray, None)
        if des_q is None or len(kps_q) == 0:
            return "", 0.0, []

        results = []
        qcount = len(kps_q)
        for label, ref in self.index.items():
            good = self._good_match_count(des_q, ref["des"])
            # Simple normalized score based on keypoint counts
            denom = max(ref["kp_count"], qcount, 1)
            score = good / denom
            results.append((label, score))

        results.sort(key=lambda x: x[1], reverse=True)
        best_label, best_score = results[0]
        return best_label, float(best_score), results[:4]
