import React from "react";
import PropTypes from "prop-types";
import {useSettings} from "./Settings";

export const initialState = {activeMessages: []}
export const ERROR = 'APP/MESSAGES/ERROR';
export const WARN = 'APP/MESSAGES/WARN';
export const showError = (message) => ({type: ERROR, text: message})
export const showWarn = (message) => ({type: WARN, text: message})
export const messageReducer = (state = initialState, action) => {
    if (action.type === ERROR) {
        return {
            ...state,
            activeMessages: state.activeMessages.concat({text: action.text, level: "error"})
        }
    }
    if (action.type === WARN) {
        return {
            ...state,
            activeMessages: state.activeMessages.concat({text: action.text, level: "warn"})
        }
    }
    return {...state}
}

function fetchWarnings(backendURL) {
    return fetch(`${backendURL("control/warnings")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

function unpackMessageFromBackend(message) {
    if (message.reason.value === "WARNING") {
        return {
            "type": WARN,
            text: `The program contains a rule that is not supported! The graph shown might be faulty! ${message.ast}`
        }
    }
    if (message.reason.value === "FAILURE") {
        return {
            "type": ERROR,
            text: `The program contains a rule that will cause false behaviour! Remove/Rephrase the following rule: ${message.ast}`
        }
    }
}

const UserMessagesContext = React.createContext([]);
export const useMessages = () => React.useContext(UserMessagesContext);
export const UserMessagesProvider = ({children}) => {

    const [state, dispatch] = React.useReducer(messageReducer, initialState);
    const {state: settingsState, backendURL} = useSettings();
    React.useEffect(() => {
        let mounted = true;
        fetchWarnings(backendURL).catch(error => {
            showError(`Failed to get transformations: ${error}`)
        })
            .then(items => {
                if (mounted) {
                    items.map((e) => unpackMessageFromBackend(e)).map((e) => (dispatch(e)))
                }
            })
        return () => mounted = false;
    }, [settingsState.backend_url]);

    return <UserMessagesContext.Provider value={[state, dispatch]}>{children}</UserMessagesContext.Provider>
}

UserMessagesProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element
}
