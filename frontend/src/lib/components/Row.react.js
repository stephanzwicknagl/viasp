import React from "react";
import {Node, RecursiveSuperNode} from "./Node.react";
import {Box} from "./Box.react";
import './row.css';
import PropTypes, { any } from "prop-types";
import {RowHeader} from "./RowHeader.react";
import {toggleTransformation, useTransformations} from "../contexts/transformations";
import {useSettings} from "../contexts/Settings";
import {TRANSFORMATION} from "../types/propTypes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useShownRecursion } from "../contexts/ShownRecursion";

function loadMyAsyncData(id, backendURL) {
    return fetch(`${backendURL("graph/children")}/${id}`).then(r => r.json());
}

function loadClingraphChildren(id, backendURL) {
    return fetch(`${backendURL("clingraph/children")}/${id}`).then(r => r.json());
}

export function Row(props) {
    const {transformation, notifyClick, color} = props;

    const [nodes, setNodes] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const ref = React.useRef(null);
    const {state: {transformations}, dispatch} = useTransformations();
    const {backendURL} = useSettings();
    const [shownRecursion, ,] = useShownRecursion();

    React.useEffect(() => {
        let mounted = true;
        loadMyAsyncData(transformation.id, backendURL)
            .then(items => {
                if (mounted) {
                    setNodes(items)
                }
            })
        return () => mounted = false;
    }, []);

    function checkForOverflow() {
        if (ref !== null && ref.current) {
            const e = ref.current
            const wouldOverflowNow = e.offsetWidth < e.scrollWidth;
            // We overflowed previously but not anymore
            if (overflowBreakingPoint <= e.offsetWidth) {
                setIsOverflowH(false);
            }
            if (!isOverflowH && wouldOverflowNow) {
                // We have to react to overflow now but want to remember when we'll not overflow anymore
                // on a resize
                setOverflowBreakingPoint(e.offsetWidth)
                setIsOverflowH(true)
            }
            // We never overflowed and also don't now
            if (overflowBreakingPoint === null && !wouldOverflowNow) {
                setIsOverflowH(false);
            }
        }
    }

    React.useEffect(() => {
        checkForOverflow()
    }, [nodes])

    React.useEffect(() => {
        window.addEventListener('resize', checkForOverflow)
        return _ => window.removeEventListener('resize', checkForOverflow)
    })
    if (nodes === null) {
        return (
            <div className="row_container">
                <RowHeader transformation={transformation.rules}/>
                <div>Loading Transformations..</div>
            </div>
        )
    }
    const showNodes = transformations.find(({
                                                transformation: t,
                                                shown
                                            }) => transformation.id === t.id && shown) !== undefined
    const style1 = { "backgroundColor": color};

    return <div className="row_container" style={style1}>
        <RowHeader transformation={transformation.rules} />
        {!showNodes ? null :
            <div ref={ref} className="row_row" >{nodes.map((child) => { 
                if (child.recursive && shownRecursion.indexOf(child.uuid) !== -1) {
                    return <RecursiveSuperNode key={child.uuid} node={child}
                    showMini={isOverflowH}
                    notifyClick={notifyClick}/>
                }
                else{
                    return <Node key={child.uuid} node={child}
                    showMini={isOverflowH}
                    notifyClick={notifyClick} isSubnode = {false}/>}})}</div>
        }</div>
}


Row.propTypes = {
    /**
     * The Transformation object to be displayed
     */
    transformation: TRANSFORMATION,

    /**
     * A callback function when the user clicks on the RuleHeader
     */
    notifyClick: PropTypes.func,

    /**
     * The backgroundcolor of the row
     */
    color: PropTypes.string
};


export function Boxrow(props) {
    const { transformation } = props;

    const [nodes, setNodes] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const ref = React.useRef(null);
    const { backendURL } = useSettings();

    React.useEffect(() => {
        let mounted = true;
        loadClingraphChildren(transformation.id, backendURL)
            .then(items => {
                if (mounted) {
                    setNodes(items)
                }
            })
        return () => mounted = false;
    }, []);

    function checkForOverflow() {
        if (ref !== null && ref.current) {
            const e = ref.current
            const wouldOverflowNow = e.offsetWidth < e.scrollWidth;
            // We overflowed previously but not anymore
            if (overflowBreakingPoint <= e.offsetWidth) {
                setIsOverflowH(false);
            }
            if (!isOverflowH && wouldOverflowNow) {
                // We have to react to overflow now but want to remember when we'll not overflow anymore
                // on a resize
                setOverflowBreakingPoint(e.offsetWidth)
                setIsOverflowH(true)
            }
            // We never overflowed and also don't now
            if (overflowBreakingPoint === null && !wouldOverflowNow) {
                setIsOverflowH(false);
            }
        }
    }

    React.useEffect(() => {
        checkForOverflow()
    }, [nodes])

    React.useEffect(() => {
        window.addEventListener('resize', checkForOverflow)
        return _ => window.removeEventListener('resize', checkForOverflow)
    })
    if (nodes === null) {
        return (
            <div className="row_container">
                <RowHeader transformation={transformation.rules} />
                <div>Loading Transformations..</div>
            </div>
        )
    }
    return <div className="boxrow_container">
        {/* TODO: make boxrow_header to toggle showing of visualization */}
            <div ref={ref} className="boxrow_row">  
                {nodes.map((child) => <Box  node={child}/>)}</div>
        </div>
}


Boxrow.propTypes = {
    /**
     * The Transformation object to be displayed
     */
    transformation: TRANSFORMATION,

    /**
     * A callback function when the user clicks on the RuleHeader
     */
    notifyClick: PropTypes.func
};
