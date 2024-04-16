import React from "react";
import {showError, useMessages} from "./UserMessages";
import {useSettings} from "./Settings";
import PropTypes from "prop-types";
import { make_default_nodes, make_default_clingraph_nodes } from "../utils/index";

function fetchTransformations(backendURL) {
    return fetch(`${backendURL("graph/transformations")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);

    });
}

function fetchSortHash(backendURL) {
    return fetch(`${backendURL("graph/sorts")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);

    });
}

function fetchSortable(backendURL) {
    return fetch(`${backendURL("graph/sortable")}`).then(r => {
        if (r.ok) {
            return r.json()
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


const initialState = {
    transformations: [],
    transformationDropIndices: null,
    currentSort: '',
    transformationNodesMap: null,
    clingraphGraphics: [],
    isSortable: true,
};

const HIDE_TRANSFORMATION = 'APP/TRANSFORMATIONS/HIDE';
const SHOW_TRANSFORMATION = 'APP/TRANSFORMATIONS/SHOW';
const TOGGLE_TRANSFORMATION = 'APP/TRANSFORMATIONS/TOGGLE';
const SHOW_ONLY_TRANSFORMATION = 'APP/TRANSFORMATIONS/ONLY';
const ADD_TRANSFORMATION = 'APP/TRANSFORMATIONS/ADD';
const ADD_TRANSFORMATION_SET = 'APP/TRANSFORMATIONS/ADDSET'
const CLEAR_TRANSFORMATIONS = 'APP/TRANSFORMATIONS/CLEAR';
const ADD_SORT = 'APP/TRANSFORMATIONS/ADDSORT';
const SET_CURRENT_SORT = 'APP/TRANSFORMATIONS/SETCURRENTSORT';
const SET_SORTABLE = 'APP/TRANSFORMATIONS/SETSORTABLE';
const REORDER_TRANSFORMATION = 'APP/TRANSFORMATIONS/REORDER';
const SET_NODES = 'APP/NODES/SET';
const CLEAR_NODES = 'APP/NODES/CLEAR';
const SET_CLINGRAPH_GRAPHICS = 'APP/CLINGRAPH/SETGRAPHICS';
const CLEAR_CLINGRAPH_GRAHICS = 'APP/CLINGRAPH/CLEAR';
const SET_TRANSFORMATION_DROP_INDICES = 'APP/TRANSFORMATIONS/SETTRANSFORMATIONDROPINDICES';
const hideTransformation = (t) => ({type: HIDE_TRANSFORMATION, t})
const showTransformation = (t) => ({type: SHOW_TRANSFORMATION, t})
const toggleTransformation = (t) => ({type: TOGGLE_TRANSFORMATION, t})
const showOnlyTransformation = (t) => ({type: SHOW_ONLY_TRANSFORMATION, t})
const addTransformation = (t) => ({type: ADD_TRANSFORMATION, t})
const addTransformationSet = (ts) => ({type: ADD_TRANSFORMATION_SET, ts})
const clearTransformations = (t) => ({type: CLEAR_TRANSFORMATIONS});
const addSort = (s) => ({ type: ADD_SORT, s })
const setCurrentSort = (s) => ({ type: SET_CURRENT_SORT, s})
const setSortable = (s) => ({type: SET_SORTABLE, s});
const reorderTransformation = (oldIndex, newIndex) => ({type: REORDER_TRANSFORMATION, oldIndex, newIndex})
const setNodes = (t) => ({type: SET_NODES, t});
const clearNodes = () => ({type: CLEAR_NODES});
const setClingraphGraphics = (g) => ({type: SET_CLINGRAPH_GRAPHICS, g});
const clearClingraphGraphics = () => ({type: CLEAR_CLINGRAPH_GRAHICS});
const setTransformationDropIndices = (t) => ({type: SET_TRANSFORMATION_DROP_INDICES, t});
const TransformationContext = React.createContext();

const transformationReducer = (state = initialState, action) => {
    if (action.type === ADD_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.concat({transformation: action.t, shown: true, hash: action.t.hash})
        }
    }
    if (action.type === ADD_TRANSFORMATION_SET) {
        console.log("Adding Transformation Set", action.ts)
        return {
            ...state,
            transformations: action.ts.map(t => ({transformation: t, shown: true, hash: t.hash}))
        };
    }
    if (action.type === CLEAR_TRANSFORMATIONS) {
        return {
            ...state,
            transformations: []
        }
    }
    if (action.type === SHOW_ONLY_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map(container => container.transformation.id !== action.t.id ? {
                transformation: container.transformation,
                shown: false
            } : {
                transformation: container.transformation,
                shown: true
            })
        }
    }
    if (action.type === SHOW_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map(container => container.transformation === action.t ? {
                transformation: container.transformation,
                shown: true
            } : container)
        }
    }
    if (action.type === HIDE_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map(container => container.transformation === action.t ? {
                transformation: container.transformation,
                shown: false
            } : container)
        }
    }
    if (action.type === TOGGLE_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.map(container => container.transformation === action.t ? {
                transformation: container.transformation,
                shown: !container.shown
            } : container)
        }
    }
    if (action.type === REORDER_TRANSFORMATION) {
        let transformations = [...state.transformations];
        const [removed] = transformations.splice(action.oldIndex, 1);
        transformations.splice(action.newIndex, 0, removed);
        transformations = transformations.map((t,i) => {
            return {transformation: {...t.transformation, id: i}, shown: t.shown, hash: t.hash}
        })
        return {
            ...state,
            transformations
        }
    }
    if (action.type === ADD_SORT) {
        return {
            ...state,
            currentSort: action.s,
        }
    }
    if (action.type === SET_CURRENT_SORT) {
        return {
            ...state,
            currentSort: action.s
        }
    }
    if (action.type === SET_NODES) {
        return {
            ...state,
            transformationNodesMap: action.t,
        };
    }
    if (action.type === CLEAR_NODES) {
        if (state.transformationNodesMap === null) {
            return {
                ...state,
                transformationNodesMap: state.transformations.map((n) => {
                    return make_default_nodes();
                }),
            }
        }
        return {
            ...state,
            transformationNodesMap:  Object.keys(
                state.transformationNodesMap
            )
            .reduce((obj, key) => {
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
        console.log("New Transformation Drop Indices", action.t)
        return {
            ...state,
            transformationDropIndices: action.t,
        };
    }
    return {...state}
}

const TransformationProvider = ({children}) => {
    const [, message_dispatch] = useMessages()
    const { backendURL} = useSettings();
    const [state, dispatch] = React.useReducer(transformationReducer, initialState);
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);

    React.useEffect(() => {
        let mounted = true;
        fetchSortHash(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get dependency sorts: ${error}`))
        })
            .then(hash => {
                if (mounted) {
                    dispatch(addSort(hash))
                }
            })
        fetchSortable(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get sortable: ${error}`))
        })
            .then((answer) => {
                if (mounted) {
                    dispatch(setSortable(answer))
                }
            })
            return () => { mounted = false };
        }, []);
        
    const loadtransformationNodesMap = React.useCallback((items) => {
        dispatch(clearNodes());
        dispatch(clearClingraphGraphics());
        const transformations = items.map((t) => ({id: t.id, hash: t.hash}));
        const promises = transformations.map(t =>
            loadNodeData(t.hash, backendUrlRef.current));

        // load facts
        promises.push(loadFacts(backendUrlRef.current));
        transformations.push({id: -1});
        // load clingraph
        promises.push(loadClingraphChildren(backendUrlRef.current));
            
        // Wait for all promises to resolve
        Promise.all(promises)
            .then((allItems) => {
                const nodesRes = allItems.slice(0, allItems.length -1)
                const clingraphNodes = allItems[allItems.length - 1]

                const transformationNodesMap = nodesRes.reduce(
                    (map, items, i) => {
                        map[transformations[i].id] = items.map((node) => {
                            return {
                                ...node,
                                loading: false,
                            };
                        });
                        return map;
                    },
                    {}
                );
                dispatch(setNodes(transformationNodesMap));
                dispatch(setClingraphGraphics(clingraphNodes));
            })
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get node data ${error}`)
                );
            });
    }, [])

    React.useEffect(() => {
        let mounted = true;
        if (state.currentSort !== '') {
            fetchTransformations(backendUrlRef.current)
                .catch((error) => {
                    messageDispatchRef.current(
                        showError(`Failed to get transformations: ${error}`)
                    );
                })
                .then((items) => {
                    if (mounted) {
                        dispatch(clearTransformations());
                        dispatch(addTransformationSet(items));
                        loadtransformationNodesMap(items);
                    }
            });
        }
        return () => {
            mounted = false;
        };
    }, [state.currentSort, loadtransformationNodesMap]);

    
    return <TransformationContext.Provider value={{state, dispatch}}>{children}</TransformationContext.Provider>
}

const useTransformations = () => React.useContext(TransformationContext);

TransformationProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
export {
    TransformationProvider,
    TransformationContext,
    useTransformations,
    toggleTransformation,
    showOnlyTransformation,
    reorderTransformation,
    setCurrentSort,
    setTransformationDropIndices,
};
