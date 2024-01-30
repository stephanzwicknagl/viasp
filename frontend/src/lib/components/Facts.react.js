import "./facts.css";
import React from "react";
import {Node} from "./Node.react";
import {useTransformations} from "../contexts/transformations";
import {make_default_nodes} from "../utils";

export function Facts() {
    const { state: {currentDragged, transformationNodesMap} } = useTransformations();
    const [fact, setFact] = React.useState(make_default_nodes()[0]);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const opacityMultiplier = 0.8;

    React.useEffect(() => {
        if (
            transformationNodesMap &&
            transformationNodesMap[-1]
        ) {
            setFact(transformationNodesMap[-1]);
        } else {
            setFact(oldFact => make_default_nodes([oldFact])[0]);
        }
    }, [transformationNodesMap]);
    
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
    return <div className="row_row" style={style}><Node 
                key={fact.uuid} 
                node={fact}
                showMini={false}/>
        </div>
}

Facts.propTypes = {}

