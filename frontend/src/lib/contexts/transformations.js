import React from 'react';
import {showError, useMessages} from './UserMessages';
import {useSettings} from './Settings';
import PropTypes from 'prop-types';
import {make_default_nodes, make_default_clingraph_nodes} from '../utils/index';

function postCurrentSort(backendURL, oldIndex, newIndex) {
    return fetch(`${backendURL('graph/sorts')}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            moved_transformation: {
                old_index: oldIndex,
                new_index: newIndex,
            },
        }),
    }).then((r) => {
        if (r.ok) {
            return r.json();
        }
        throw new Error(r.statusText);
    });
}

function fetchTransformations(backendURL) {
    return fetch(`${backendURL('graph/transformations')}`).then((r) => {
        if (r.ok) {
            return r.json();
        }
        throw new Error(r.statusText);
    });
}

function fetchSortHash(backendURL) {
    return fetch(`${backendURL('graph/sorts')}`).then((r) => {
        if (r.ok) {
            return r.json();
        }
        throw new Error(r.statusText);
    });
}

function fetchSortable(backendURL) {
    return fetch(`${backendURL('graph/sortable')}`).then((r) => {
        if (r.ok) {
            return r.json();
        }
        throw new Error(r.statusText);
    });
}

function loadFacts(backendURL) {
    return fetch(`${backendURL('graph/facts')}`).then((r) => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json();
    });
}

function loadNodeData(hash, backendURL) {
    return fetch(`${backendURL('graph/children')}/${hash}`).then((r) => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json();
    });
}

function loadClingraphChildren(backendURL) {
    return fetch(`${backendURL('clingraph/children')}`).then((r) => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json();
    });
}

function loadEdges(shownRecursion, usingClingraph, backendURL) {
    return fetch(`${backendURL('graph/edges')}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            shownRecursion: shownRecursion,
            usingClingraph: usingClingraph,
        }),
    }).then((r) => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json();
    });
}

const initialState = {
    transformations: [],
    edges: [],
    /** an object mapping transformation ids to a List of Nodes */
    transformationDropIndices: null, 
    currentSort: '',
    transformationNodesMap: null,
    clingraphGraphics: [],
    isSortable: true,
    shownRecursion: [],
};

/**
 * Manage Transformation Set
 * */
const ADD_TRANSFORMATION = 'APP/TRANSFORMATIONS/ADD';
const ADD_TRANSFORMATION_SET = 'APP/TRANSFORMATIONS/ADDSET';
const CLEAR_TRANSFORMATIONS = 'APP/TRANSFORMATIONS/CLEAR';
const REORDER_TRANSFORMATION = 'APP/TRANSFORMATIONS/REORDER';
const SET_TRANSFORMATION_DROP_INDICES =
    'APP/TRANSFORMATIONS/SETTRANSFORMATIONDROPINDICES';
const CHECK_TRANSFORMATION_EXPANDABLE_COLLAPSIBLE = 'APP/TRANSFORMATIONS/CHECKTRANSFORMATIONEXPANDABLECOLLAPSIBLE';
const addTransformation = (t) => ({type: ADD_TRANSFORMATION, t});
const addTransformationSet = (ts) => ({type: ADD_TRANSFORMATION_SET, ts});
const clearTransformations = (t) => ({type: CLEAR_TRANSFORMATIONS});
const reorderTransformation = (oldIndex, newIndex) => ({
    type: REORDER_TRANSFORMATION,
    oldIndex,
    newIndex,
});
const setTransformationDropIndices = (t) => ({
    type: SET_TRANSFORMATION_DROP_INDICES,
    t,
});
const checkTransformationExpandableCollapsible = (tid) => ({type: CHECK_TRANSFORMATION_EXPANDABLE_COLLAPSIBLE, tid});
/**
 * Manage Sorts 
 * */
const ADD_SORT = 'APP/SORT/ADD';
const SET_CURRENT_SORT = 'APP/TRANSFORMATIONS/SETCURRENTSORT';
const SET_SORTABLE = 'APP/TRANSFORMATIONS/SETSORTABLE';
const addSort = (s) => ({type: ADD_SORT, s});
const setCurrentSort = (s) => ({type: SET_CURRENT_SORT, s});
const setSortable = (s) => ({type: SET_SORTABLE, s});
/**
 * Manage Nodes
*/
const SET_NODES = 'APP/NODES/SET';
const CLEAR_NODES = 'APP/NODES/CLEAR';
const setNodes = (nodesRes, t) => ({type: SET_NODES, nodesRes, t});
const clearNodes = () => ({type: CLEAR_NODES});
/**
 * Manage Edges
*/
const SET_EDGES = 'APP/EDGES/SET';
const setEdges = (e) => ({type: SET_EDGES, e});
/**
 * Manage Shown Transformations
 * */
const HIDE_TRANSFORMATION = 'APP/TRANSFORMATIONS/HIDE';
const SHOW_TRANSFORMATION = 'APP/TRANSFORMATIONS/SHOW';
const TOGGLE_TRANSFORMATION = 'APP/TRANSFORMATIONS/TOGGLE';
const SHOW_ONLY_TRANSFORMATION = 'APP/TRANSFORMATIONS/ONLY';
const hideTransformation = (t) => ({type: HIDE_TRANSFORMATION, t});
const showTransformation = (t) => ({type: SHOW_TRANSFORMATION, t});
const toggleTransformation = (t) => ({type: TOGGLE_TRANSFORMATION, t});
const showOnlyTransformation = (t) => ({type: SHOW_ONLY_TRANSFORMATION, t});
/**
 * Manage Shown Recursion
 */
const TOGGLE_SHOWN_RECURSION = 'APP/TRANSFORMATIONS/RECURSION/TOGGLE';
const CLEAR_SHOWN_RECURSION = 'APP/TRANSFORMATIONS/RECURSION/CLEAR';
const toggleShownRecursion = (n) => ({type: TOGGLE_SHOWN_RECURSION, n});
const clearShownRecursion = () => ({type: CLEAR_SHOWN_RECURSION});
/**
 * Manage Node Expansion (vertical overflow)
 * */
const SET_NODE_IS_EXPANDABLE_V = 'APP/NODE/OVERFLOWV/SETEXPANDABLE';
const SET_NODE_IS_COLLAPSIBLE_V = 'APP/NODE/OVERFLOWV/SETCOLLAPSIBLE';
const SET_NODE_IS_EXPAND_ALL_THE_WAY = 'APP/NODE/OVERFLOWV/SETEXPANDALLTHEWAY';
const setNodeIsExpandableV = (tid, uuid, v) => ({type: SET_NODE_IS_EXPANDABLE_V, tid, uuid, v});
const setNodeIsCollapsibleV = (tid, uuid, v) => ({type: SET_NODE_IS_COLLAPSIBLE_V, tid, uuid, v});
const setNodeIsExpandAllTheWay = (tid, uuid, v) => ({type: SET_NODE_IS_EXPAND_ALL_THE_WAY, tid, uuid, v});
/**
 * Manage Node Overflow Horizontal
 */
const SET_NODE_SHOW_MINI = 'APP/NODE/OVERFLOWH/SETSHOWMINI';
const setNodeShowMini = (tid, uuid, v) => ({type: SET_NODE_SHOW_MINI, tid, uuid, v});
/**
 * Manage Clingraph
 */
const SET_CLINGRAPH_GRAPHICS = 'APP/CLINGRAPH/SETGRAPHICS';
const CLEAR_CLINGRAPH_GRAHICS = 'APP/CLINGRAPH/CLEAR';
const setClingraphGraphics = (g) => ({type: SET_CLINGRAPH_GRAPHICS, g});
const clearClingraphGraphics = () => ({type: CLEAR_CLINGRAPH_GRAHICS});

const TransformationContext = React.createContext();

const transformationReducer = (state = initialState, action) => {
    if (action.type === ADD_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.concat({
                transformation: action.t,
                shown: true,
                hash: action.t.hash,
                isExpandableV: false,
                isCollapsibleV: false,
                allNodesShowMini: false,
            }),
        };
    }
    if (action.type === ADD_TRANSFORMATION_SET) {
        return {
            ...state,
            transformations: action.ts.map((t) => ({
                transformation: t,
                shown: true,
                hash: t.hash,
                isExpandableV: false,
                isCollapsibleV: false,
                allNodesShowMini: false,
            })),
        };
    }
    if (action.type === SET_NODE_IS_EXPANDABLE_V) {
        return state.transformationNodesMap && action.tid ? {
            ...state,
            transformationNodesMap: {
                ...state.transformationNodesMap, 
                [action.tid]: state.transformationNodesMap[action.tid]?.map((node) => {
                        if (node.uuid === action.uuid) {
                            return {
                                ...node,
                                isExpandableV: action.v,
                            };
                        }
                        if (node.recursive) {
                            return {
                                ...node,
                                recursive: node.recursive.map((subnode) => {
                                    if (subnode.uuid === action.uuid) {
                                        return {
                                            ...subnode,
                                            isExpandableV: action.v,
                                        }
                                    }
                                    return subnode
                                }),
                            }
                        }
                        return node;
                    })
                }
            } : state
    }
    if (action.type === SET_NODE_IS_COLLAPSIBLE_V) {
        return state.transformationNodesMap && action.tid ? {
            ...state,
            transformationNodesMap: {
                ...state.transformationNodesMap, 
                [action.tid]: state.transformationNodesMap[action.tid]?.map((node) => {
                        if (node.uuid === action.uuid) {
                            return {
                                ...node,
                                isCollapsibleV: action.v,
                            };
                        }
                        if (node.recursive) {
                            return {
                                ...node,
                                recursive: node.recursive.map((subnode) => {
                                    if (subnode.uuid === action.uuid) {
                                        return {
                                            ...subnode,
                                            isCollapsibleV: action.v,
                                        }
                                    }
                                    return subnode
                                }),
                            }
                        }
                        return node;
                    })
                }
            } : state
    }
    if (action.type === SET_NODE_IS_EXPAND_ALL_THE_WAY) {
        return state.transformationNodesMap && action.tid ? {
            ...state,
            transformationNodesMap: {
                ...state.transformationNodesMap, 
                [action.tid]: state.transformationNodesMap[action.tid]?.map((node) => {
                        if (node.uuid === action.uuid) {
                            return {
                                ...node,
                                isExpandVAllTheWay: action.v,
                            };
                        }
                        if (node.recursive) {
                            return {
                                ...node,
                                recursive: node.recursive.map((subnode) => {
                                    if (subnode.uuid === action.uuid) {
                                        return {
                                            ...subnode,
                                            isExpandVAllTheWay: action.v,
                                        }
                                    }
                                    return subnode
                                }),
                            }
                        }
                        return node;
                    })
                }
            } : state
    }
    if (action.type === SET_NODE_SHOW_MINI) {
        return state.transformationNodesMap && action.tid ? {
            ...state,
            transformationNodesMap: {
                ...state.transformationNodesMap, 
                [action.tid]: state.transformationNodesMap[action.tid]?.map((node) => {
                        if (node.uuid === action.uuid) {
                            return {
                                ...node,
                                showMini: action.v,
                            };
                        }
                        if (node.recursive) {
                            return {
                                ...node,
                                recursive: node.recursive.map((subnode) => {
                                    if (subnode.uuid === action.uuid) {
                                        return {
                                            ...subnode,
                                            showMini: action.v,
                                        }
                                    }
                                    return subnode
                                }),
                            }
                        }
                        return node;
                    })
                }
            } : state
    }       
    if (action.type === CLEAR_TRANSFORMATIONS) {
        return {
            ...state,
            transformations: [],
        };
    }
    if (action.type === SHOW_ONLY_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map((container) =>
                container.transformation.id !== action.t.id
                    ? {
                          ...container,
                          shown: false,
                      }
                    : {
                          ...container,
                          shown: true,
                      }
            ),
        };
    }
    if (action.type === SHOW_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map((container) =>
                container.transformation === action.t
                    ? {
                          ...container,
                          shown: true,
                      }
                    : container
            ),
        };
    }
    if (action.type === HIDE_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map((container) =>
                container.transformation === action.t
                    ? {
                          ...container,
                          shown: false,
                      }
                    : container
            ),
        };
    }
    if (action.type === TOGGLE_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map((container) =>
                container.transformation === action.t
                    ? {
                          transformation: container.transformation,
                          shown: !container.shown,
                      }
                    : container
            ),
        };
    }
    if (action.type === REORDER_TRANSFORMATION) {
        let transformations = [...state.transformations];
        const [removed] = transformations.splice(action.oldIndex, 1);
        transformations.splice(action.newIndex, 0, removed);
        transformations = transformations.map((container, i) => {
            return {
                ...container,
                transformation: {...container.transformation, id: i},
            };
        });

        let nodesMap = Object.values(state.transformationNodesMap);
        const [removedNodes] = nodesMap.splice(action.oldIndex, 1);
        nodesMap.splice(action.newIndex, 0, removedNodes);
        nodesMap = nodesMap.reduce((obj, key, i) => {
            obj[key] = Object.values(nodesMap)[i];
            return obj;
        }, {});
        return {
            ...state,
            transformations: transformations,
            transformationNodesMap: nodesMap,
        };
    }
    if (action.type === ADD_SORT) {
        return {
            ...state,
            currentSort: action.s,
        };
    }
    if (action.type === SET_CURRENT_SORT) {
        return {
            ...state,
            currentSort: action.s,
        };
    }
    if (action.type === SET_NODES) {
        return {
            ...state,
            transformationNodesMap: action.nodesRes.reduce(
                (map, items, i) => {
                    map[action.t[i].id] = items.map(
                        (node) => {
                            return {
                                ...node,
                                recursive: node.recursive.map((n) => ({
                                    ...n,
                                    loading: false,
                                    shownRecursion: false,
                                    isExpandableV: false,
                                    isCollapsibleV: false,
                                    isExpandVAllTheWay: false,  
                                    showMini: false,
                                })),
                                loading: false,
                                shownRecursion: false,
                                isExpandableV: false,
                                isCollapsibleV: false,
                                isExpandVAllTheWay: false,
                                showMini: false,
                                };
                            }
                        );
                        return map;
                    },
                    {}
                ),
        };
    }
    if (action.type === CLEAR_NODES) {
        if (state.transformationNodesMap === null) {
            return {
                ...state,
                transformationNodesMap: state.transformations.map((n) => {
                    return make_default_nodes();
                }),
            };
        }
        return {
            ...state,
            transformationNodesMap: Object.keys(
                state.transformationNodesMap
            ).reduce((obj, key) => {
                obj[key] = make_default_nodes(
                    state.transformationNodesMap[key]
                );
                return obj;
            }, {}),
        };
    }
    if (action.type === SET_CLINGRAPH_GRAPHICS) {
        return {
            ...state,
            clingraphGraphics: action.g.map((n) => {
                n.loading = false;
                return n;
            }),
        };
    }
    if (action.type === CLEAR_CLINGRAPH_GRAHICS) {
        if (state.clingraphGraphics === null) {
            return {
                ...state,
            };
        }
        return {
            ...state,
            clingraphGraphics: make_default_clingraph_nodes(
                state.clingraphGraphics
            ),
        };
    }
    if (action.type === SET_SORTABLE) {
        return {
            ...state,
            isSortable: action.s,
        };
    }
    if (action.type === SET_TRANSFORMATION_DROP_INDICES) {
        return {
            ...state,
            transformationDropIndices: action.t,
        };
    }
    if (action.type === CHECK_TRANSFORMATION_EXPANDABLE_COLLAPSIBLE) {
        return {
            ...state,
            transformations: state.transformations.map((container) => {
                if (container.transformation.id === action.tid) {
                    container.isExpandableV = state.transformationNodesMap[action.tid].some((node) => node.isExpandableV);
                    container.isCollapsibleV = state.transformationNodesMap[action.tid].some((node) => node.isCollapsibleV);
                    container.allNodesShowMini = state.transformationNodesMap[action.tid].every((node) => node.showMini);
                }
                return container;
            }),
        };
    }
    if (action.type === SET_EDGES) {
        return {
            ...state,
            edges: action.e,
        };
    }
    if (action.type === TOGGLE_SHOWN_RECURSION) {
        let shownRecursion = [...state.shownRecursion];
        if (shownRecursion.includes(action.n)) {
            shownRecursion = shownRecursion.filter((n) => n !== action.n);
        } else {
            shownRecursion.push(action.n);
        }

        const transformationNodesMap = Object.keys(state.transformationNodesMap)
            .reduce((obj, key) => {
            obj[key] = state.transformationNodesMap[key].map((node) => {
                if (node.uuid === action.n) {
                    return {
                        ...node,
                        shownRecursion: !node.shownRecursion,
                    };
                }
                return node;
            });
            return obj;
        }, {});
        return {
            ...state,
            transformationNodesMap: transformationNodesMap,
            shownRecursion: shownRecursion,
        };
    }
    if (action.type === CLEAR_SHOWN_RECURSION) {
        return {
            ...state,
            shownRecursion: [],
        };
    }
    return {...state};
};

const TransformationProvider = ({children}) => {
    const [, message_dispatch] = useMessages();
    const {backendURL} = useSettings();
    const [state, dispatch] = React.useReducer(
        transformationReducer,
        initialState
    );
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);

    const loadTransformationNodesMap = (items) => {
        dispatch(clearNodes());
        dispatch(clearClingraphGraphics());
        const transformations = items.map((t) => ({id: t.id, hash: t.hash}));
        const promises = transformations.map((t) =>
            loadNodeData(t.hash, backendUrlRef.current)
        );

        // load facts
        promises.push(loadFacts(backendUrlRef.current));
        transformations.push({id: -1});
        // load clingraph
        promises.push(loadClingraphChildren(backendUrlRef.current));

        // Wait for all promises to resolve
        return Promise.all(promises);
    };

    const reloadEdges = (shownRecursion, usingClingraph) => {
        loadEdges(
                shownRecursion,
                usingClingraph,
                backendUrlRef.current
            )
                .catch((error) => {
                    messageDispatchRef.current(
                        showError(`Failed to get edges: ${error}`)
                    );
                })
                .then((items) => {
                    dispatch(setEdges(items));
                });
    }


    const fetchGraph = (shownRecursion) => {
        fetchTransformations(backendUrlRef.current)
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get transformations: ${error}`)
                );
            })
            .then((items) => {
                dispatch(clearTransformations());
                dispatch(addTransformationSet(items));
                loadTransformationNodesMap(items)
                    .catch((error) => {
                        messageDispatchRef.current(
                            showError(`Failed to get nodes: ${error}`)
                        );
                    })
                    .then((allItems) => {
                        const nodesRes = allItems.slice(0, allItems.length - 1);
                        const clingraphNodes = allItems[allItems.length - 1];

                        const transformations = [
                            ...items.map((t) => ({id: t.id})),
                            {id: -1},
                        ];

                        dispatch(setNodes(nodesRes, transformations));
                        dispatch(setClingraphGraphics(clingraphNodes));
                        reloadEdges(shownRecursion, clingraphNodes.length > 0);
                   });
            });
    };
    const fetchGraphRef = React.useRef(fetchGraph);

    const setSortAndFetchGraph = (oldIndex, newIndex) => {
        dispatch(reorderTransformation(oldIndex, newIndex));
        dispatch(clearShownRecursion());
        postCurrentSort(backendUrlRef.current, oldIndex, newIndex)
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to set new current graph: ${error}`)
                );
            })
            .then((r) => {
                if (r && r.hash) {
                    dispatch(setCurrentSort(r.hash));
                }
                fetchGraph(
                    state.shownRecursion,
                    state.clingraphGraphics.length > 0
                );
            });
    };

    React.useEffect(() => {
        let mounted = true;
        fetchSortHash(backendUrlRef.current)
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get dependency sorts: ${error}`)
                );
            })
            .then((hash) => {
                if (mounted) {
                    dispatch(addSort(hash));
                }
            });
        fetchSortable(backendUrlRef.current)
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get sortable: ${error}`)
                );
            })
            .then((answer) => {
                if (mounted) {
                    dispatch(setSortable(answer));
                }
            });
        fetchGraphRef.current([]);
        return () => {
            mounted = false;
        };
    }, []);

    return (
        <TransformationContext.Provider
            value={{state, dispatch, setSortAndFetchGraph, reloadEdges}}
        >
            {children}
        </TransformationContext.Provider>
    );
};

const useTransformations = () => React.useContext(TransformationContext);

TransformationProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
};
export {
    TransformationProvider,
    TransformationContext,
    useTransformations,
    toggleTransformation,
    showOnlyTransformation,
    reorderTransformation,
    setCurrentSort,
    setTransformationDropIndices,
    toggleShownRecursion,
    setNodeIsExpandableV,
    setNodeIsCollapsibleV,
    setNodeIsExpandAllTheWay,
    setNodeShowMini,
    checkTransformationExpandableCollapsible,
};
