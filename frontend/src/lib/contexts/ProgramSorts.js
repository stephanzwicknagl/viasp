import React from "react";
import { showError, useMessages } from "./UserMessages";
import { useSettings } from "./Settings";
import PropTypes from "prop-types";

function fetchSorts(backendURL) {
    return fetch(`${backendURL("graph/sorts")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);

    });
}

const initialState = {
    sorts: [],
    currentSort: 0,
};

const ADD_SORT = 'APP/SORTS/ADD';
const SET_CURRENT_SORT = 'APP/SORTS/SET_CURRENT';
const addSort = (s) => ({ type: ADD_SORT, s })
const setCurrentSort = (hash) => ({ type: SET_CURRENT_SORT, hash })

const sortReducer = (state = initialState, action) => {
    if (action.type === ADD_SORT) {
        if (state.currentSort === 0) {
            return {
                ...state,
                sorts: state.sorts.concat({transformations: action.s[0], hash: action.s[1]}),
                currentSort: action.s[1]
            }
        }
        return {
            ...state,
            sorts: state.sorts.concat({transformations: action.s[0], hash: action.s[1]})
        }
    }
    if (action.type === SET_CURRENT_SORT) {
        const s = {
            ...state,
            currentSort: action.hash
        }
        return s
    }
    return state;
}

const SortsContext = React.createContext();
const SortsProvider = ({ children }) => {
    const [, message_dispatch] = useMessages()
    const { state: settingsState, backendURL } = useSettings();
    const [ state, dispatch ] = React.useReducer(sortReducer, initialState);
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
        return () => { mounted = false };
    }, []);

    return <SortsContext.Provider value={{ state, dispatch }}>{children}</SortsContext.Provider>
}

const useSorts = () => React.useContext(SortsContext);

SortsProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
export { SortsProvider, useSorts }
