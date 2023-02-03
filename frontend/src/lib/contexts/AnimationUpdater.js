import React from "react";
import PropTypes from "prop-types";

const defaultAnimationUpdater = () => { };

const AnimationUpdater = React.createContext(defaultAnimationUpdater);

export const useAnimationUpdater = () => React.useContext(AnimationUpdater);
export const AnimationUpdaterProvider = ({ children }) => {
    const [value, setValue] = React.useState(0);
    const startAnimationUpdater = () => setInterval(() => setValue(value => value + 1), 25);
    const stopAnimationUpdater = () => clearInterval(startAnimationUpdater);

    return <AnimationUpdater.Provider
        value={[value, setValue, startAnimationUpdater, stopAnimationUpdater]}>{children}</AnimationUpdater.Provider>
}

AnimationUpdaterProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
