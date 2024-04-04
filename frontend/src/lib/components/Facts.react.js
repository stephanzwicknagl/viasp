import "./facts.css";
import React from "react";
import {Node} from "./Node.react";
import {useTransformations} from "../contexts/transformations";
import {make_default_nodes} from "../utils";
import {useAnimationUpdater} from "../contexts/AnimationUpdater";
import useResizeObserver from '@react-hook/resize-observer';


export function Facts() {
    const { state: {currentDragged, transformationNodesMap} } = useTransformations();
    const [fact, setFact] = React.useState(make_default_nodes()[0]);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const opacityMultiplier = 0.8;
    const branchSpaceRef = React.useRef(null);
    const rowbodyRef = React.useRef(null);
    const {setAnimationState} = useAnimationUpdater();
    const setAnimationStateRef = React.useRef(setAnimationState);

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
            setStyle(prevStyle => ({...prevStyle, opacity: 1 - opacityMultiplier}));
        }
        else {
            setStyle(prevStyle => ({...prevStyle, opacity: 1.0}));
        }
    }, [currentDragged, opacityMultiplier]);

    const animateResize = React.useCallback(() => {
        const setAnimationState = setAnimationStateRef.current;
        const element = rowbodyRef.current;
        setAnimationState((oldValue) => ({
            ...oldValue,
            "-1": {
                ...oldValue["-1"],
                width: element.clientWidth,
                height: element.clientHeight,
                top: element.offsetTop,
                left: element.offsetLeft,
            },
        }));
    }, []);
    useResizeObserver(rowbodyRef, animateResize);

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

