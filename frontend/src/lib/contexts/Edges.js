import React from "react";
import { showError, useMessages } from "./UserMessages";
import { useSettings } from "./Settings";
import PropTypes from "prop-types";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useShownNodes } from "../contexts/ShownNodes";
import { useFilters } from "../contexts/Filters";
import { useClingraph } from "../contexts/Clingraph";
import { useTransformations } from "../contexts/transformations";


function loadEdges(nodeInfo, backendURL) {
    return fetch(`${backendURL("graph/edges")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(nodeInfo)
    }).then(r => r.json());
}

function loadClingraphEdges(nodeInfo, backendURL) {
    return fetch(`${backendURL("clingraph/edges")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(nodeInfo)
    }).then(r => r.json());
}


const initialState = [];

const EdgeContext = React.createContext();
const EdgeProvider = ({ children }) => {
    const { backendURL } = useSettings();
    const backendUrlRef = React.useRef(backendURL);
    const [, message_dispatch] = useMessages()
    const messageDispatchRef = React.useRef(message_dispatch);
    const { state: { transformations } } = useTransformations()


    const { globalState: {shownNodes} } = useShownNodes();
    const [shownRecursion, ,] = useShownRecursion();
    const [{activeFilters},] = useFilters();
    const { clingraphUsed } = useClingraph();
    
    const [edges, setEdges] = React.useState(initialState);
    const [clingraphEdges, setClingraphEdges] = React.useState(initialState);
    
    const reloadEdges = React.useCallback(() => {
        const nodeInfo = {
            shownNodes: shownNodes,
            shownRecursion: shownRecursion
        }
        loadEdges(nodeInfo, backendUrlRef.current).catch(error => {
            messageDispatchRef.current(showError(`Failed to get edges: ${error}`))
        })
            .then(items => {
                setEdges(items)
            })
        if (clingraphUsed) {
            const nodeInfo = {
                shownNodes: shownNodes,
            }
            loadClingraphEdges(nodeInfo, backendUrlRef.current).catch(error => {
                messageDispatchRef.current(showError(`Failed to get clingraph edges: ${error}`))
            })
            .then(items => {
                setClingraphEdges(items)
                })
            }   
    }, [shownNodes, shownRecursion, clingraphUsed]);

    React.useEffect(() => {
        reloadEdges();
    }, [reloadEdges, shownNodes, shownRecursion, activeFilters, transformations]);

    return <EdgeContext.Provider value={{ edges, clingraphEdges, reloadEdges }}>{children}</EdgeContext.Provider>
}

const useEdges = () => React.useContext(EdgeContext);

EdgeProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
export { EdgeProvider, useEdges }
