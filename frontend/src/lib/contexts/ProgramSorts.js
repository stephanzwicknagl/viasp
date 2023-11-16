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

const defaultSorts = [];

const SortsContext = React.createContext(defaultSorts);
const SortsProvider = ({ children }) => {
    const [, message_dispatch] = useMessages()
    const { state: settingsState, backendURL } = useSettings();
    const [sorts, setSorts] = React.useState(defaultSorts);
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);

    const hash = ""

    React.useEffect(() => {
        let mounted = true;
        fetchSorts(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get dependency sorts: ${error}`))
        })
            .then(items => {
                if (mounted) {
                    setSorts(items)
                }
            })
        return () => { mounted = false };
    }, []);

    return <SortsContext.Provider value={{ sorts }}>{children}</SortsContext.Provider>
}

const useSorts = () => React.useContext(SortsContext);

SortsProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
export { SortsProvider, useSorts }
