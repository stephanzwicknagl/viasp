import React from "react";
import LineTo from "react-lineto";
import PropTypes from "prop-types";
import useResizeObserver from "@react-hook/resize-observer";
import {useShownNodes} from "../contexts/ShownNodes";
import {useSettings} from "../contexts/Settings";
import {useFilters} from "../contexts/Filters";
import {useHighlightedSymbol} from "../contexts/HighlightedSymbol";
import Xarrow from "react-xarrows";
import {useColorPalette} from "../contexts/ColorPalette";

function loadEdges(shownNodes, backendURL) {
    return fetch(`${backendURL("graph/edges")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(shownNodes)
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
    const {state, backendURL} = useSettings();
    const [{activeFilters},] = useFilters();
    const [lastIndex, setLastIndex] = React.useState(0);
    
    
    React.useEffect(() => {
        let mounted = true;
        
        loadEdges(shownNodes, backendURL)
        .then(items => {
            if (mounted) {
                setEdges(items)
                setLastIndex(items.length - 1)
            }
        })
        return () => mounted = false;
    }, [shownNodes, state, activeFilters]);

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

    
    return <div ref={target} className="edge_container">
            {edges.map(link => <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={-1} borderColor={"black"} borderStyle={"solid"} borderWidth={1} />)}
            {!usingClingraph ? null:
            clingraphEdges.map(link => <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={-1} borderColor={"black"} borderStyle={"dashed"} borderWidth={2} />)}
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
    const colorPalette = useColorPalette();
    
    return <div className="arrows_container">
        {highlightedSymbol.map(arrow => {
            return arrow.map(a => {
                return <Xarrow
                    key={a[0] + "-" + a[1]} start={a[0]} end={a[1]} startAnchor={"top"} endAnchor={"bottom"} color={colorPalette.warn.ten} strokeWidth={2} headSize={5}/>
            })
        })}
    </div> 
}

Arrows.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
