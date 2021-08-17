import dash_bootstrap_components as dbc
import dash_html_components as html
import inspect, traceback, urllib, os

import numpy as np
import skimage.measure
def mean_pool(array, axis=0, kernel_size=None, output_num=None):
    if kernel_size is None:
        kernel_size = (array.shape[axis] + output_num - 1) // output_num
    elif output_num is None:
        output_num = (array.shape[axis] + kernel_size - 1) // kernel_size
    if kernel_size != 1:
        array = array.astype("float32")
        if array.shape[axis] <= kernel_size:
            array = np.mean(array, axis=axis, keepdims=True)
        else:
            indices = np.linspace(0.0, float(array.shape[axis] - 1), num=(array.shape[axis] + kernel_size - 1) // kernel_size * kernel_size).astype("int32")
            array = np.take(array, indices, axis=axis)

            block_size = [1] * len(array.shape)
            block_size[axis] = kernel_size
            array = skimage.measure.block_reduce(array, block_size=tuple(block_size), func=np.mean)
    return array

class GraphFactory:
    def __init__(self, func, name, file):
        self.name = name
        if isinstance(func, str):
            self.code = func
        else:
            self.code = inspect.getsource(func)
        self.file = file

    def execute(self, experiments):
        loc = {"mean_pool": mean_pool}
        try:
            exec(self.code, globals(), loc)
            fig = loc["graph"](experiments)
        except:
            return None, traceback.format_exc()
        return fig, None

    def commit(self):
        with open(self.file, "w") as f:
            f.write(self.code)

class Database:
    def __init__(self, path):
        self.path = path
        if not os.path.isdir(path):
            os.makedirs(path)

    def get_by_name(self, name):
        if name is None:
            names = self.get_all_names()
            if len(names) == 0:
                return None
            else:
                name = names[0]
        file = os.path.join(self.path, name + ".py")
        if not os.path.isfile(file):
            return None
        with open(file, "r") as f:
            code = f.read()
        return GraphFactory(code, name, file)

    def get_all_names(self):
        return [f[:-3] for f in os.listdir(self.path) if f.endswith(".py")]
