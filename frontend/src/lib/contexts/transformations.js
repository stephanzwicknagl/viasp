import React from "react";
import {showError, useMessages} from "./UserMessages";
import {useSettings} from "./Settings";
import PropTypes from "prop-types";
import { computeSortHash } from "../utils/index";

function fetchTransformations(backendURL) {
    return fetch(`${backendURL("graph/transformations")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);

    });
}

function fetchSorts(backendURL) {
    return fetch(`${backendURL("graph/sorts")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);

    });
}


const initialState = {
    transformations: [],
    possibleSorts: [],
    currentSort: "",
};

const HIDE_TRANSFORMATION = 'APP/TRANSFORMATIONS/HIDE';
const SHOW_TRANSFORMATION = 'APP/TRANSFORMATIONS/SHOW';
const TOGGLE_TRANSFORMATION = 'APP/TRANSFORMATIONS/TOGGLE';
const SHOW_ONLY_TRANSFORMATION = 'APP/TRANSFORMATIONS/ONLY';
const ADD_TRANSFORMATION = 'APP/TRANSFORMATIONS/ADD';
const ADD_SORT = 'APP/TRANSFORMATIONS/ADDSORT';
const SET_CURRENT_SORT = 'APP/TRANSFORMATIONS/SETCURRENTSORT';
const REORDER_TRANSFORMATION = 'APP/TRANSFORMATIONS/REORDER';
const hideTransformation = (t) => ({type: HIDE_TRANSFORMATION, t})
const showTransformation = (t) => ({type: SHOW_TRANSFORMATION, t})
const toggleTransformation = (t) => ({type: TOGGLE_TRANSFORMATION, t})
const showOnlyTransformation = (t) => ({type: SHOW_ONLY_TRANSFORMATION, t})
const addTransformation = (t) => ({type: ADD_TRANSFORMATION, t})
const addSort = (s) => ({ type: ADD_SORT, s })
const setCurrentSort = (s) => ({ type: SET_CURRENT_SORT, s})
const reorderTransformation = (oldIndex, newIndex) => ({type: REORDER_TRANSFORMATION, oldIndex, newIndex})
const TransformationContext = React.createContext();

const transformationReducer = (state = initialState, action) => {
    if (action.type === ADD_TRANSFORMATION) {
        return {
            ...state,
            transformations: state.transformations.concat({transformation: action.t, shown: true, hash: action.t.hash})
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
        if (state.currentSort === "") {
            return {
                ...state,
                possibleSorts: state.possibleSorts.concat([action.s[1]]),
                currentSort: action.s[1]
            }
        }
        return {
            ...state,
            possibleSorts: state.possibleSorts.concat([action.s[1]])
        }
    }
    if (action.type === SET_CURRENT_SORT) {
        return {
            ...state,
            currentSort: action.s
        }
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
        fetchSorts(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get dependency sorts: ${error}`))
        })
            .then(items => {
                if (mounted) {
                    items.map((s) => dispatch(addSort(s)))
                }
            })
        fetchTransformations(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get transformations: ${error}`))
        })
            .then(items => {
                if (mounted) {
                    items.map((t) => (dispatch(addTransformation(t))))
                }
            })
        return () => { mounted = false };
    }, []);

    return <TransformationContext.Provider value={{state, dispatch}}>{children}</TransformationContext.Provider>
}

const useTransformations = () => React.useContext(TransformationContext);

TransformationProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
export {TransformationProvider, TransformationContext, useTransformations, toggleTransformation, showOnlyTransformation, reorderTransformation}
