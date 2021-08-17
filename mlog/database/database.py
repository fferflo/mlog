import os
from . import graph_factory, experiment_selector, experiment

class Database:
    def __init__(self, path):
        self.path = path
        if not os.path.isdir(path):
            os.makedirs(path)

        self.graph_factories = graph_factory.Database(os.path.join(self.path, "mlog", "graph_factories"))
        self.experiment_selectors = experiment_selector.Database(os.path.join(self.path, "mlog", "experiment_selectors"))
        self.experiments = experiment.Database(self.path)
