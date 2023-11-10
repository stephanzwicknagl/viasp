import React from "react";
import { showError, useMessages } from "./UserMessages";
import { useSettings } from "./Settings";
import PropTypes from "prop-types";


function loadClingraphUsed(backendURL) {
    return fetch(`${backendURL("control/clingraph")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

const defaultClingraph = false;
const ClingraphContext = React.createContext(defaultClingraph);

export const useClingraph = () => React.useContext(ClingraphContext);
export const ClingraphProvider = ({ children }) => {
    const [clingraphUsed, setClingraphUsed] = React.useState(defaultClingraph);
    const [, message_dispatch] = useMessages()
    const { backendURL } = useSettings();
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);

    React.useEffect(() => {
        let mounted = true;
        loadClingraphUsed(backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get transformations: ${error}`))
        })
        .then(data => {
            if (mounted) {
                setClingraphUsed(data.using_clingraph)
            }
        }) 
        return () => { mounted = false };
    }, []);

    return <ClingraphContext.Provider
        value={{clingraphUsed, setClingraphUsed}}>{children}</ClingraphContext.Provider>
}

ClingraphProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
