import React from "react";
import PropTypes from "prop-types";

const defaultShownRecursion = [];

const ShownRecursionContext = React.createContext(defaultShownRecursion);

export const useShownRecursion = () => React.useContext(ShownRecursionContext);
export const ShownRecursionProvider = ({ children }) => {
    const [shownRecursion, setShownRecursion] = React.useState(defaultShownRecursion);

    function toggleShownRecursion(node) {
        var index = shownRecursion.indexOf(node);

        if (index === -1) {
            setShownRecursion(shownRecursion.concat(node));
        } else {
            setShownRecursion(shownRecursion.filter(item => item !== node));
        }
    };

    return <ShownRecursionContext.Provider
        value={[shownRecursion, toggleShownRecursion, setShownRecursion]}>{children}</ShownRecursionContext.Provider>
}

ShownRecursionProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
