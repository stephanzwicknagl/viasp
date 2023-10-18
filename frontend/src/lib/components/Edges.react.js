import React from "react";
import LineTo from "react-lineto";
import PropTypes, { node } from "prop-types";
import useResizeObserver from "@react-hook/resize-observer";
import {useShownNodes} from "../contexts/ShownNodes";
import {useSettings} from "../contexts/Settings";
import {useColorPalette} from "../contexts/ColorPalette";
import {useFilters} from "../contexts/Filters";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";

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
    const colorPalete = useColorPalette();
    const [edges, setEdges] = React.useState([]);
    const [clingraphEdges, setClingraphEdges] = React.useState([]);
    const target = React.useRef(null)
    useResize(target)
    const [{shownNodes},] = useShownNodes();
    const [shownRecursion, ,] = useShownRecursion();
    const {state, backendURL} = useSettings();
    const [{activeFilters},] = useFilters();
    // state to update Edges after height animation of node
    const [value, , , ] = useAnimationUpdater();
    
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
                to={link.tgt} zIndex={1} borderColor={colorPalete.seventy.dark} borderStyle={"solid"} borderWidth={1} />)}
            {!usingClingraph ? null:
            clingraphEdges.map(link => <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={1} borderColor={colorPalete.seventy.bright} borderStyle={"dashed"} borderWidth={2} />)}
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
