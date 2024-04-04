import React from 'react';
import PropTypes from 'prop-types';

const defaultGraphZoomState = () => {
    return {
        translation: {x: 0, y: 0},
        scale: 1,
    };
};

export const GraphZoomState = React.createContext(defaultGraphZoomState);

export const useGraphZoomState = () => React.useContext(GraphZoomState);
export const GraphZoomStateProvider = ({children}) => {
    const [graphZoom, setGraphZoom] = React.useState(Object());

    return (
        <GraphZoomState.Provider
            value={{graphZoom, setGraphZoom}}
        >
            {children}
        </GraphZoomState.Provider>
    );
};

GraphZoomStateProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
};
