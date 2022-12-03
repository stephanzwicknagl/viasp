from .wrapper import Control, Control2, ShowConnector

v = None
def load_program(path):
    global v
    v = ShowConnector()
    v.load_program(path)

def show():
    v.show()

def unmark(model):
    v.unmark(model)

def mark(model):
    v.mark(model)

def clear(model):
    v.clear(model)

def relax_constraints(*args, **kwargs):
    return v.relax_constraints(*args, **kwargs)

def clingraph(viz_encoding, engine):
    v.clingrpah(viz_encoding,engine)