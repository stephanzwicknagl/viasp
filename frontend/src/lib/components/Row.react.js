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

export function RowTemplate(props) {
    const { item, itemSelected, anySelected, dragHandleProps, commonProps } = props;
    const transformation = item.transformation;
    const scale = itemSelected * 0.02 + 1;
    const shadow = itemSelected * 15 + 1;
    const dragged = itemSelected !== 0;
    const colorPalette = useColorPalette();
    const background = Object.values(colorPalette.twenty);

    if (transformation === undefined) {
        return <div>teste</div>
    };
    // const d = !isClingraph ?
        // <Row key={transformation.id} transformation={transformation} /> :
        // <Boxrow key={`clingraph_${transformation.id}`} transformation={transformation} />    

    return (<div 
            className="row_container"
            style={{
            transform: `scale(${scale})`,
            boxShadow: `rgba(0, 0, 0, 0.3) 0px ${shadow}px ${2 * shadow}px 0px`,
            background: background[transformation.id % background.length]
        }}><div class="dragHandleContainer"><div className="dragHandle" {...dragHandleProps}/></div>
        <Row key={transformation.id} transformation={transformation} />
    </div>)
};



export function Row(props) {
    const {transformation} = props;

    const [nodes, setNodes] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const ref = React.useRef(null);
    const {state: {transformations}} = useTransformations();
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
            <div >
                <RowHeader transformation={transformation.rules}/>
                <div>Loading Transformations..</div>
            </div>
        )
    }
    const showNodes = transformations.find(({transformation: t,
                                             shown
                                            }) => transformation.id === t.id && shown) !== undefined
    // const style1 = { "backgroundColor": background[transformation.id % background.length] };

    return <div>
        <RowHeader transformation={transformation.rules} />
        {!showNodes ? null :
            <div ref={ref} className="row_row" >{nodes.map((child) => { 
                if (child.recursive && shownRecursion.indexOf(child.uuid) !== -1) {
                    return <RecursiveSuperNode key={child.uuid} node={child}
                    showMini={isOverflowH}/>
                }
                else{
                    return <Node key={child.uuid} node={child}
                    showMini={isOverflowH} isSubnode = {false}/>}})}</div>
        }</div>
}


Row.propTypes = {
    /**
     * The Transformation object to be displayed
     */
    transformation: TRANSFORMATION,
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
