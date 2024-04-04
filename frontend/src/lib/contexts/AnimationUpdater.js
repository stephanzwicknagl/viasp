import React from "react";
import PropTypes from "prop-types";

const defaultAnimationUpdater = () => { };

export const AnimationUpdater = React.createContext(defaultAnimationUpdater);

export const useAnimationUpdater = () => React.useContext(AnimationUpdater);
export const AnimationUpdaterProvider = ({ children }) => {
    const [animationState, setAnimationState] = React.useState(Object());

    return <AnimationUpdater.Provider
        value={{animationState, setAnimationState}}>{children}</AnimationUpdater.Provider>
}

AnimationUpdaterProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
