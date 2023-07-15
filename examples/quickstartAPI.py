import viasp
from viasp.server import startup


def main():
  viasp.load_program_file('clingraph/example5_encoding.lp')
  viasp.mark_from_string('person(a).person(c).')
  viasp.mark_from_string('person(b).person(d).')

  viasp.show()
  viasp.clingraph(viz_encoding='clingraph/example5_viz.lp', engine='dot', graphviz_type='digraph')


app = startup.run()
if __name__ == '__main__':
    main()
    app.run()
