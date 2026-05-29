import ctypes
from ctypes import c_double, c_size_t
from pathlib import Path
from typing import Optional


class HermesCppNativeBridge:
    def __init__(self, dll_path: Optional[str] = None) -> None:
        self.dll_path = dll_path or str(Path("core/native/hermes_learning_kernel.dll"))
        self._dll = None
        self._load()

    def _load(self) -> None:
        dll = Path(self.dll_path)
        if not dll.exists():
            return
        self._dll = ctypes.CDLL(str(dll))
        self._dll.hermes_reward_update.argtypes = [
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            ctypes.POINTER(c_double),
            c_size_t,
        ]
        self._dll.hermes_reward_update.restype = c_double
        self._dll.hermes_gaussian_3d_score.argtypes = [
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
        ]
        self._dll.hermes_gaussian_3d_score.restype = c_double

    @property
    def available(self) -> bool:
        return self._dll is not None

    def reward_update(
        self,
        quality: float,
        speed: float,
        cost_efficiency: float,
        truth_score: float,
        novelty: float,
        weights: list[float],
    ) -> float:
        if not self._dll:
            score = (
                quality * weights[0]
                + speed * weights[1]
                + cost_efficiency * weights[2]
                + truth_score * weights[3]
                + novelty * weights[4]
            )
            if truth_score < 0.68:
                score -= (0.68 - truth_score) * 1.5
            return score

        arr = (c_double * len(weights))(*weights)
        return float(
            self._dll.hermes_reward_update(
                c_double(quality),
                c_double(speed),
                c_double(cost_efficiency),
                c_double(truth_score),
                c_double(novelty),
                arr,
                c_size_t(len(weights)),
            )
        )

    def gaussian_3d_score(
        self,
        x: float,
        y: float,
        z: float,
        target_x: float,
        target_y: float,
        target_z: float,
        sigma: float = 0.2,
    ) -> float:
        if not self._dll:
            dx = x - target_x
            dy = y - target_y
            dz = z - target_z
            dist2 = dx * dx + dy * dy + dz * dz
            safe_sigma = max(0.000001, sigma)
            return pow(2.718281828, -(dist2 / (2 * safe_sigma * safe_sigma)))

        return float(
            self._dll.hermes_gaussian_3d_score(
                c_double(x),
                c_double(y),
                c_double(z),
                c_double(target_x),
                c_double(target_y),
                c_double(target_z),
                c_double(sigma),
            )
        )
