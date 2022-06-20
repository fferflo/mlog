import yaml, datetime, os, threading
import numpy as np

class Node:
    def __init__(self, session):
        self.dict = {}
        self.session = session
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        with self.lock:
            if key in self.dict:
                raise ValueError(f"Node already contains a child with key {key}")
            self.dict[key] = value
            self.session.changed()

    def __getitem__(self, key):
        with self.lock:
            if not key in self.dict:
                self.dict[key] = Node(self.session)
            return self.dict[key]

    def __contains__(self, key):
        with self.lock:
            return key in self.dict

    def overwrite(self, key, value):
        with self.lock:
            self.dict[key] = value

    def Mapping(self, key):
        with self.lock:
            if not key in self.dict:
                self.dict[key] = Mapping(self.session)
            return self.dict[key]

    def TimeSeries(self, key):
        with self.lock:
            if not key in self.dict:
                self.dict[key] = TimeSeries(self.session)
            return self.dict[key]

    def commit(self, path, root):
        keys = list(self.dict.keys())
        keys_values = [(k, self.dict[k]) for k in keys]
        return {k: (v.commit(os.path.join(path, k), root) if "commit" in dir(v) else v) for k, v in keys_values}

class Mapping(Node):
    def __init__(self, session):
        Node.__init__(self, session)
        self.xs = []
        self.ys = []
        self.changed = False

    def add(self, x, y):
        with self.lock:
            self.xs.append(x)
            self.ys.append(y)
            self.changed = True
            self.session.changed()

    def commit(self, path, root):
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        xs_path = f"{path}-x.npy"
        ys_path = f"{path}-y.npy"
        if self.changed:
            np.save(xs_path, np.asarray(self.xs))
            np.save(ys_path, np.asarray(self.ys))
            self.changed = False
        xs_path = os.path.relpath(xs_path, root)
        ys_path = os.path.relpath(ys_path, root)
        return {"xs": xs_path, "ys": ys_path, "mlog-type": "mapping", **Node.commit(self, path, root)}

class TimeSeries(Mapping):
    def __init__(self, session):
        Mapping.__init__(self, session)

    def add(self, y):
        Mapping.add(self, np.datetime64(datetime.datetime.now()), y)

class Session(Node):
    def __init__(self, path, autocommit=True):
        Node.__init__(self, self)

        self.commit_lock = threading.Lock()

        self.path = path
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

        self.autocommit = autocommit

        self["time"]["start"] = datetime.datetime.now().replace(microsecond=0).isoformat()

    def commit(self):
        self["time"].overwrite("last_commit", datetime.datetime.now().replace(microsecond=0).isoformat())
        with self.commit_lock:
            dict = Node.commit(self, self.path, self.path)
            with open(os.path.join(self.path, "config.yaml"), "w") as f:
                yaml.dump(dict, f, default_flow_style=False)

    def changed(self):
        if self.autocommit:
            self.commit()
