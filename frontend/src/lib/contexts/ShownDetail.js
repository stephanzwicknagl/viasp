import React from "react";
import PropTypes from "prop-types";

const defaultShownDetail = null;

const ShownDetailContext = React.createContext(defaultShownDetail);

export const useShownDetail = () => React.useContext(ShownDetailContext);
export const ShownDetailProvider = ({ children }) => {
    const [shownDetail, setShownDetail] = React.useState(defaultShownDetail);

    return <ShownDetailContext.Provider
        value={{shownDetail, setShownDetail}}>{children}</ShownDetailContext.Provider>
}

ShownDetailProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
