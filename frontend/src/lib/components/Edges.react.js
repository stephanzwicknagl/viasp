import React from "react";
import LineTo from "react-lineto";
import PropTypes, { node } from "prop-types";
import useResizeObserver from "@react-hook/resize-observer";
import {useShownNodes} from "../contexts/ShownNodes";
import {useSettings} from "../contexts/Settings";
import {useFilters} from "../contexts/Filters";
import {useHighlightedSymbol} from "../contexts/HighlightedSymbol";
import Xarrow from "react-xarrows";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useArrowUpdater } from "../contexts/ArrowUpdater";

function loadEdges(nodeInfo, backendURL) {
    return fetch(`${backendURL("graph/edges")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(nodeInfo)
    }).then(r => r.json());
}

function loadClingraphEdges(shownNodes, backendURL) {
    return fetch(`${backendURL("clingraph/edges")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(shownNodes)
    }).then(r => r.json());
}

const useResize = (target) => {
    const [size, setSize] = React.useState()

    React.useLayoutEffect(() => {
        setSize(target.current.getBoundingClientRect())
    }, [target])

    useResizeObserver(target, (entry) => setSize(entry.contentRect))
    return size
}

export function Edges(props) {
    const { usingClingraph } = props;
    const [edges, setEdges] = React.useState([]);
    const [clingraphEdges, setClingraphEdges] = React.useState([]);
    const target = React.useRef(null)
    useResize(target)
    const [{shownNodes},] = useShownNodes();
    const [shownRecursion, ,] = useShownRecursion();
    const {state, backendURL} = useSettings();
    const [{activeFilters},] = useFilters();
    // state to update Edges after height animation of node
    const [value, , , ] = useArrowUpdater();
    
    React.useEffect(() => {
        let mounted = true;
        
        const nodeInfo = {
            shownNodes: shownNodes,
            shownRecursion: shownRecursion
        }
        loadEdges(nodeInfo, backendURL)
        .then(items => {
            if (mounted) {
                setEdges(items)
            }
        })
        return () => mounted = false;
    }, [shownNodes, shownRecursion, state, activeFilters]);

    if (usingClingraph) {
        React.useEffect(() => {
            let mounted = true;

            loadClingraphEdges(shownNodes, backendURL)
                .then(items => {
                    if (mounted) {
                        setClingraphEdges(items)
                        // setEdges(edges.concat(items))
                    }
                })
            return () => mounted = false;
        }, [shownNodes, state, activeFilters]);
    };

    
    return <div ref={target} className="edge_container" >
            {edges.map(link => <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={1} borderColor={"black"} borderStyle={"solid"} borderWidth={1} />)}
            {!usingClingraph ? null:
            clingraphEdges.map(link => <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={1} borderColor={"black"} borderStyle={"dashed"} borderWidth={2} />)}
        </div>

        
}

Edges.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * The using Clingraph boolean
     * */
    usingClingraph: PropTypes.bool
}

export function Arrows(){
    const [highlightedSymbol,,] = useHighlightedSymbol();
    // state to update Arrows after height animation of node
    const [value, , , ] = useArrowUpdater();
    
    return <div className="arrows_container">
        {highlightedSymbol.filter(arrow => document.getElementById(arrow.src) && document.getElementById(arrow.tgt)).map(arrow => {
            return <Xarrow
                key={arrow.src + "-" + arrow.tgt} start={arrow.src} end={arrow.tgt} startAnchor={"top"} endAnchor={"bottom"} color={arrow.color} strokeWidth={2} headSize={5} zIndex={10}/>
        })}
    </div> 
}

Arrows.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
