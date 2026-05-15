# hermes_csharp_learning.py
# Python bindings for Hermes C# learning module
import ctypes
import numpy as np
import os

DLL_PATH = os.path.join(os.path.dirname(__file__), 'HermesCSharpLearning.dll')

class HermesCSharpLearning:
    def __init__(self):
        self.lib = ctypes.CDLL(DLL_PATH)
        self.lib.TrainSkill.restype = ctypes.c_double
        self.lib.TrainSkill.argtypes = [np.ctypeslib.ndpointer(dtype=np.float64), ctypes.c_int]

    def train_skill(self, data):
        arr = np.ascontiguousarray(data, dtype=np.float64)
        return self.lib.TrainSkill(arr, len(arr))

# Example usage:
# csharp = HermesCSharpLearning()
# result = csharp.train_skill([1.0, 2.0, 3.0])
# print(result)
