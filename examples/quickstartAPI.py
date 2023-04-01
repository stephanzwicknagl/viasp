import sys
import viasp
from viasp.server import startup
from clingo import Control


# def main():
#     options = ['0']

#     ctl = Control(options)
#     for path in sys.argv[1:]:
#         ctl.load(path)
#     ctl.ground([("base", [])])

#     with ctl.solve(yield_=True) as handle:
#         for m in handle:
#             print("Answer:\n{}".format(m))
#         print(handle.get())
#     viasp.show()

app = startup.run()

if __name__ == '__main__':

    # main()
    viasp.load_program_string('''
    {sprinkler;rain}=1.wet:-rain.wet:-sprinkler.
    ''')
    viasp.mark_from_string('wet.rain.')
    viasp.mark_from_string('wet.sprinkler.')
    viasp.show()
    app.run_server()
