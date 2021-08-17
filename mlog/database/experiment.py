import os, yaml
import numpy as np

class Database:
    def __init__(self, path):
        self.path = path
        if not os.path.isdir(path):
            os.makedirs(path)

    def get_all(self):
        return [Experiment(os.path.join(self.path, n, "mlog")) for n in os.listdir(self.path) if n != "mlog"]

class Experiment:
    def __init__(self, path):
        self.path = path
        try:
            with open(os.path.join(self.path, "config.yaml"), "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
        self.name = os.path.basename(os.path.dirname(self.path))

        def process(node):
            if isinstance(node, list):
                for n in node:
                    process(n)
            elif isinstance(node, dict):
                if "mlog-type" in node:
                    if node["mlog-type"] == "mapping":
                        node["xs"] = np.load(os.path.join(self.path, node["xs"]))
                        node["ys"] = np.load(os.path.join(self.path, node["ys"]))
                    else:
                        print("Invalid mlog-type")
                        sys.exit(-1) # TODO: handling
                else:
                    for n in node.values():
                        process(n)
        process(self.config)

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

# import numpy as np
# experiments = []
#
# xs = np.linspace(-30.0, 30.0, num=600)
# experiments.append({
#     "name": "experiment1",
#     "xs": xs,
#     "ys": np.sin(xs / 3),
# })
#
# xs = np.linspace(-30.0, 30.0, num=600)
# experiments.append({
#     "name": "experiment2",
#     "xs": xs,
#     "ys": np.sin(xs),
# })
#
# def get_all():
#     return experiments
