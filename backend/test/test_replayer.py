from viasp.asp.replayer import apply_multiple


def test_run(clingo_call_run_sample, app_context):
    replayed = apply_multiple(clingo_call_run_sample)
    num_models = 0
    with replayed.solve(yield_=True) as handle:  # type: ignore
        for m in handle:
            _ = m.symbols(atoms=True)
            num_models += 1
    assert num_models == 2
