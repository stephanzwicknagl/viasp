import React from "react";
import PropTypes from "prop-types";

export const initialState = {
    shownNodes: [],
};
export const HIDE_NODE = 'APP/NODES/HIDE';
export const SHOW_NODE = 'APP/NODES/SHOW';
export const hideNode = (node) => ({type: HIDE_NODE, node})
export const showNode = (node) => ({type: SHOW_NODE, node})
export const nodeReducer = (state = initialState, action) => {
    if (action.type === SHOW_NODE) {
        return {
            ...state,
            shownNodes: state.shownNodes.concat(action.node)
        }
    }
    if (action.type === HIDE_NODE) {
        return {
            ...state,
            shownNodes: state.shownNodes.filter(item => item !== action.node)
        }
    }
    return {...state}
}
const ShownNodesContext = React.createContext([]);
export const useShownNodes = () => React.useContext(ShownNodesContext);
export const ShownNodesProvider = ({children}) => {
    const [globalState, dispatch] = React.useReducer(nodeReducer, initialState);
    return <ShownNodesContext.Provider value={{globalState, dispatch}}>{children}</ShownNodesContext.Provider>
}

ShownNodesProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
