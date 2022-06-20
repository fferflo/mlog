import dash_bootstrap_components as dbc
import dash_html_components as html
import inspect, traceback, urllib, os

import numpy as np
import skimage.measure, scipy.ndimage
def mean_pool(array, axis=0, sigma=0):
    if sigma > 0:
        array = array.astype("float32")
        array = scipy.ndimage.gaussian_filter1d(array, sigma=sigma, axis=axis)
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
