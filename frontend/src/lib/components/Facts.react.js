import "./facts.css";
import React from "react";
import PropTypes from "prop-types";
import {hideNode, showNode, useShownNodes} from "../contexts/ShownNodes";
import {useColorPalette} from "../contexts/ColorPalette";
import {useSettings} from "../contexts/Settings";
import {NODE} from "../types/propTypes";
import {Node} from "./Node.react";

function loadFacts(backendURL) {
    return fetch(`${backendURL("graph/facts")}`).then(r => r.json());
}

export function Facts(props) {
    const {notifyClick} = props;
    const {state, backendURL} = useSettings();
    const [fact, setFact] = React.useState(null);
    React.useEffect(() => {
        let mounted = true;
        loadFacts(backendURL)
            .then(items => {
                if (mounted) {
                    setFact(items)
                }
            })
        return () => mounted = false;
    }, [state.backend_url]);
    if (fact === null) {
        return (
            <div className="row_container">
            </div>
        )
    }
    return fact === null ? null :
        <div className="row_row"><Node key={fact.uuid} node={fact}
                                       showMini={false}
                                       notifyClick={notifyClick}/></div>

}

Facts.propTypes = {
    /**
     * The function to be called if the facts are clicked on
     */
    notifyClick: PropTypes.func
}
