import "./facts.css";
import React from "react";
import * as Constants from "../constants";
import {Node} from "./Node.react";
import {useTransformations} from "../contexts/transformations";
import {make_default_nodes} from "../utils";
import {useDebouncedAnimateResize} from "../hooks/useDebouncedAnimateResize";

export function Facts() {
    const { state: {currentDragged, transformationNodesMap} } = useTransformations();
    const [fact, setFact] = React.useState(make_default_nodes()[0]);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const branchSpaceRef = React.useRef(null);
    const rowbodyRef = React.useRef(null);
    const transformationIdRef = React.useRef("-1");

    useDebouncedAnimateResize(rowbodyRef, transformationIdRef);

    React.useEffect(() => {
        if (
            transformationNodesMap &&
            transformationNodesMap["-1"]
        ) {
            setFact(transformationNodesMap["-1"][0]);
        }
    }, [transformationNodesMap]);
    
    React.useEffect(() => {
        if (currentDragged.length > 0) {
            setStyle(prevStyle => ({...prevStyle, opacity: 1 - Constants.opacityMultiplier}));
        }
        else {
            setStyle(prevStyle => ({...prevStyle, opacity: 1.0}));
        }
    }, [currentDragged]);



    if (fact === null) {
        return (
            <div className="row_container">
            </div>
        )
    }
    return (
    <div 
        className="row_row" 
        style={style}
        ref={rowbodyRef}
    >
        <div
            className="branch_space"
            key={fact.uuid}
            style={{flex: '0 0 100%'}}
            ref={branchSpaceRef}
        >
            <Node 
                key={fact.uuid} 
                node={fact}
                isSubnode={false}
                branchSpace={branchSpaceRef}/>
        </div>
    </div>
    );
}

Facts.propTypes = {}

