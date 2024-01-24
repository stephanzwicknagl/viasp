import "./facts.css";
import React from "react";
import PropTypes from "prop-types";
import {showError, useMessages} from '../contexts/UserMessages';
import {useSettings} from "../contexts/Settings";
import {Node} from "./Node.react";
import {useTransformations} from "../contexts/transformations";

function loadFacts(backendURL) {
    return fetch(`${backendURL('graph/facts')}`).then((r) => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json();
    });
}

export function Facts() {
    const { backendURL} = useSettings();
    const { state: {currentDragged} } = useTransformations();
    const [, message_dispatch] = useMessages();
    const messageDispatchRef = React.useRef(message_dispatch);
    const backendURLRef = React.useRef(backendURL)
    const [fact, setFact] = React.useState(null);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const opacityMultiplier = 0.8;

    React.useEffect(() => {
        let mounted = true;
        loadFacts(backendURLRef.current)
            .then((items) => {
                if (mounted) {
                    setFact(items);
                }
            })
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get facts ${error}`)
                );
            });
        return () => { mounted = false };
    }, []);
    
    React.useEffect(() => {
        if (currentDragged.length > 0) {
            setStyle(prevStyle => ({...prevStyle, opacity: 1 - opacityMultiplier}));
        }
        else {
            setStyle(prevStyle => ({...prevStyle, opacity: 1.0}));
        }
    }, [currentDragged, opacityMultiplier]);

    if (fact === null) {
        return (
            <div className="row_container">
            </div>
        )
    }
    return fact === null ? <div>Loading...</div> :
        <div className="row_row" style={style}><Node 
                key={fact.uuid} 
                node={fact}
                showMini={false}/></div>

}

Facts.propTypes = {}

