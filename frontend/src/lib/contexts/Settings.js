// https://www.thisdot.co/blog/creating-a-global-state-with-react-hooks
import React from "react"
import PropTypes from "prop-types";

export const DEFAULT_BACKEND_URL = "http://localhost:5050";
// REDUCER STUFF
const TOGGLE_SHOW = "APP/SETTINGS/TOGGLE_SHOW"
const SET_BACKEND_URL = "APP/SETTINGS/BACKEND_URL/SET"

export const toggleShowAll = () => ({type: TOGGLE_SHOW})
export const setBackendURL = (url) => ({type: SET_BACKEND_URL, backend_url: url})
const reducer = (state, action) => {
    switch (action.type) {
        case TOGGLE_SHOW:
            return {
                ...state,
                show_all: !state.show_all
            }
        case SET_BACKEND_URL:
            window.sessionStorage.setItem("backend_url", action.backend_url);
            return {
                ...state,
                backend_url: action.backend_url
            }

        default:
            return state
    }
}

export function initSettings(initialArgs) {
    return initialArgs
}

// PROVIDER STUFF
export const Settings = React.createContext({
    state: initSettings(),
    dispatch: () => null
})


export const useSettings = () => {

    const [state, dispatch] = React.useContext(Settings)
    const backend_url = window.sessionStorage.getItem("backend_url") || DEFAULT_BACKEND_URL
    state.backend_url = backend_url

    function backendURL(route) {
        return `${backend_url}/${route}`
    }

    return {state, dispatch, backendURL}
}
export const SettingsProvider = ({children, backendURL}) => {
    const [state, dispatch] = React.useReducer(reducer, {show_all: false, backend_url: backendURL}, initSettings);
    window.sessionStorage.setItem("backend_url", state.backend_url);

    return (
        <Settings.Provider value={[state, dispatch]}>
            {children}
        </Settings.Provider>
    )
}

SettingsProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
    /**
     * The backendURL viASP that provides the graph
     */
    backendURL: PropTypes.string
}
