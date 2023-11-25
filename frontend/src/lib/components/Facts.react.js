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

export function Facts() {
    const { backendURL} = useSettings();
    const [fact, setFact] = React.useState(null);
    const backendURLRef = React.useRef(backendURL)
    
    React.useEffect(() => {
        let mounted = true;
        loadFacts(backendURLRef.current)
            .then(items => {
                if (mounted) {
                    setFact(items)
                }
            });
        return () => { mounted = false };
    }, []);

    if (fact === null) {
        return (
            <div className="row_container">
            </div>
        )
    }
    return fact === null ? <div>Loading...</div> :
        <div className="row_row"><Node 
                key={fact.uuid} 
                node={fact}
                showMini={false}/></div>

}

Facts.propTypes = {
    /**
     * The function to be called if the facts are clicked on
     */
    notifyClick: PropTypes.func
}

function FactBanner(props) {
    const {fact} = props;
    const [, dispatchShownNodes] = useShownNodes()
    const colorPalette = useColorPalette();
    const dispatchShownNodesRef = React.useRef(dispatchShownNodes);
    const nodeuuidRef = React.useRef(fact.uuid);

    React.useEffect(() => {
        const dispatch = dispatchShownNodesRef.current;
        const nodeuuid = nodeuuidRef.current
        dispatch(showNode(nodeuuid))
        return () => {
            dispatch(hideNode(nodeuuid))
        }
    }, [])
    const clazzName = `${fact.uuid} facts_banner noselect`
    return <div className={clazzName}
                style={{"color": colorPalette.sixty.dark, "backgroundColor": colorPalette.ten.dark}}>Facts</div>
}

FactBanner.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
    fact: NODE
}
