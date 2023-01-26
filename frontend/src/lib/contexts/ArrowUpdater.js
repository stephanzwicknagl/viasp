import React from "react";
import PropTypes from "prop-types";

const defaultArrowUpdater = () => { };

const ArrowUpdater = React.createContext(defaultArrowUpdater);

export const useArrowUpdater = () => React.useContext(ArrowUpdater);
export const ArrowUpdaterProvider = ({children}) => {
    const [value, setValue] = React.useState(0);


    return <ArrowUpdater.Provider
        value={[value, setValue, () => setValue(value => value + 1)]}>{children}</ArrowUpdater.Provider>
}

ArrowUpdaterProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
