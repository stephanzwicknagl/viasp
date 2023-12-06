
node(1..4). start(1).
edge(1,2). edge(2,3). edge(2,4). edge(3,1).
edge(3,4). edge(4,1). edge(4,3).

{ hc(V,U) } :- edge(V,U).
reached(V) :- hc(S,V), start(S).
reached(V) :- reached(U), hc(U,V).
:- node(V), not reached(V).
:- hc(V,U), hc(V,W), U!=W.
:- hc(U,V), hc(W,V), U!=W.
% :- hc(V,U), hc(W,V), U!=W. % uncomment to make the program unsatisfiable & comment the line above
