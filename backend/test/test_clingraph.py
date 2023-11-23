from flask import current_app


def test_clingraph_delete(client_with_a_clingraph):
    client, _, _, _ = client_with_a_clingraph
    res = client.delete("/control/clingraph")
    assert res.status_code == 200
    res = client.get("/control/clingraph")
    assert res.status_code == 200
    assert res.data == b'{"using_clingraph": false}'


def test_using_clingraph(client_with_a_clingraph):
    prg = """
        node(X):-a(X).
        attr(node,a,color,blue) :- node(a), not b(a).
        attr(node,a,color,red)  :- node(a), b(a).
    """
    client, _, _, program = client_with_a_clingraph

    serialized = current_app.json.dumps({"viz-encoding":prg, "engine":"dot", "graphviz-type": "graph"})
    res = client.post("/control/clingraph", data=serialized, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    assert res.data == b'ok'
    
    res = client.get("/control/clingraph")
    assert res.status_code == 200
    if "{b(X)}" in program:
        assert res.data == b'{"using_clingraph": true}'
    else:
        assert res.data == b'{"using_clingraph": false}'


def test_clingraph_children(client_with_a_clingraph):
    prg = """
        node(X):-a(X).
        attr(node,a,color,blue) :- node(a), not b(a).
        attr(node,a,color,red)  :- node(a), b(a).
    """
    client, _, _, program = client_with_a_clingraph

    serialized = current_app.json.dumps({"viz-encoding":prg, "engine":"dot", "graphviz-type": "graph"})
    res = client.post("/control/clingraph", data=serialized, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    assert res.data == b'ok'
    res = client.get("/clingraph/children")
    assert res.status_code == 200
    clingraph_uuids = current_app.json.loads(res.data)
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert len(clingraph_uuids) == 4
        res = client.get(f"/graph/clingraph/{clingraph_uuids[0]}")
        assert res.status_code == 200
        assert res.content_type == 'image/png'
    else:
        # program_recursive
        assert len(clingraph_uuids) == 0


def test_clingraph_image(client_with_a_clingraph):
    prg = """
        node(X):-a(X).
        attr(node,a,color,blue) :- node(a), not b(a).
        attr(node,a,color,red)  :- node(a), b(a).
    """
    client, _, _, program = client_with_a_clingraph

    serialized = current_app.json.dumps({"viz-encoding":prg, "engine":"dot", "graphviz-type": "graph"})
    res = client.post("/control/clingraph", data=serialized, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    assert res.data == b'ok'
    res = client.get("/clingraph/children")
    assert res.status_code == 200
    clingraph_uuids = current_app.json.loads(res.data)

    if "{b(X)}" in program:
        res = client.get(f"/graph/clingraph/{clingraph_uuids[0]}")
        assert res.status_code == 200
        assert res.content_type == 'image/png'


def test_clingraph_edges(client_with_a_clingraph):
    prg = """
        node(X):-a(X).
        attr(node,a,color,blue) :- node(a), not b(a).
        attr(node,a,color,red)  :- node(a), b(a).
    """
    client, _, _, program = client_with_a_clingraph

    serialized = current_app.json.dumps({"viz-encoding":prg, "engine":"dot", "graphviz-type": "graph"})
    res = client.post("/control/clingraph", data=serialized, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    assert res.data == b'ok'
    res = client.get("/clingraph/edges")
    assert res.status_code == 200
    assert type(res.json) == list

    uuids = [node.uuid for node in client.get(f"/graph").json]
    res = client.post(f"/clingraph/edges", json={"shownNodes": uuids, "shownRecursion": []})
    assert res.status_code == 200
    assert type(res.json) == list
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert len(res.json) == 4
    else:
        # program_recursive
        assert len(res.json) == 0
        res = client.post(f"/clingraph/edges", json={"shownNodes": uuids, "shownRecursion": [uuids[-1]]})
        assert res.status_code == 200
        assert type(res.json) == list
        assert len(res.json) == 0
