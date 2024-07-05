from viasp.__main__ import ViaspArgumentParser

def parse(test_args):
    options, clingo_options, prologue, file_warnings = ViaspArgumentParser().run(test_args)
    return options, clingo_options, prologue, file_warnings

def test_argparse_file():
    test_args = [
        'test/resources/sample_encoding.lp',
    ]
    options = parse(test_args)[0]
    assert len(options['files'])  == 1
    assert len(options['files'][0]) == 3
    assert options['files'][0][0] == 'test/resources/sample_encoding.lp'

def test_argparse_n_models():
    test_args = [
        'test/resources/sample_encoding.lp',
        '0'
    ]
    options = parse(test_args)[0]
    assert options['max_models'] == 0

    test_args = [
        'test/resources/sample_encoding.lp',
        '--models', '10'
    ]
    options = parse(test_args)[0]
    assert options['max_models'] == 10

    test_args = [
        'test/resources/sample_encoding.lp',
        '-n5'
    ]
    options = parse(test_args)[0]
    assert options['max_models'] == 5

def test_clingo_args_passed_through():
    test_args = [
        '--warn=none',
        '--rewrite-minimize'
    ]
    clingo_options = parse(test_args)[1]
    assert len(clingo_options) == 2
    assert clingo_options == test_args

def test_constant():
    test_args = [
        '--const', 'a=1',
        '-c', 'b=2',
    ]
    options = parse(test_args)[0]
    assert len(options['constants']) == 2
    assert options['constants'] == {'a': '1', 'b':'2'}

def test_help():
    test_args = [
        '--help'
    ]
    try:
        parse(test_args)
    except SystemExit as e:
        assert e.code == 0

def test_clingo_help():
    test_args = [
        '--clingo-help=1'
    ]
    options = parse(test_args)[0]
    assert options['clingo_help'] == 1

def test_basic_argumens():
    test_args = [
        'test/resources/sample_encoding.lp', '--host','localhost',
        '--port','8050',
        '--frontend-port','3000',
    ]
    options = parse(test_args)[0]
    assert options['host'] == 'localhost'
    assert options['port'] == 8050
    assert options['frontend_port'] == 3000

def test_opt_mode():
    test_args = [
        'test/resources/sample_encoding.lp',
        '--opt-mode=optN',
    ]
    options = parse(test_args)[0]
    assert options['opt_mode_str'] == '--opt-mode=optN'

    test_args = [
        'test/resources/sample_encoding.lp',
        '--opt-mode=opt,1,2',
    ]
    options = parse(test_args)[0]
    assert options['opt_mode_str'] == '--opt-mode=opt,1,2'


def test_select_model():
    test_args = [
        'test/resources/sample_encoding.lp',
        '--select-model=1',
    ]
    options = parse(test_args)[0]
    assert options['select_model'] == [1]

def test_clingraph():
    test_args = [
        'test/resources/sample_encoding.lp', '--viz-encoding',
        'test/resources/sample_encoding.lp', '--engine','neato',
        '--graphviz-type','digraph',
    ]
    options = parse(test_args)[0]
    assert len(options[
        'clingraph_files']) == 1
    assert options['clingraph_files'][0][0] == 'test/resources/sample_encoding.lp'
    assert options['engine'] == 'neato'
    assert options['graphviz_type'] == 'digraph'

def test_relaxer():
    test_args = [
        'test/resources/sample_encoding.lp', '--relax',
        '--no-collect-variables',
        '--head-name', 'testhead'
    ]
    options = parse(test_args)[0]
    assert options['relax'] == True
    assert options['no_collect_variables'] == True
    assert options['head_name'] == 'testhead'

def test_version():
    test_args = [
        '--version'
    ]
    try:
        parse(test_args)
    except SystemExit as e:
        assert e.code == 0
