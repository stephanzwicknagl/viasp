import React, {useRef, useEffect, useCallback, Suspense} from "react";
import {Node, RecursiveSuperNode} from "./Node.react";
import './row.css';
import PropTypes from "prop-types";
import {RowHeader} from "./RowHeader.react";
import {toggleTransformation, useTransformations} from "../contexts/transformations";
import {useSettings} from "../contexts/Settings";
import { TRANSFORMATION, TRANSFORMATIONWRAPPER } from "../types/propTypes";
import { ColorPaletteContext } from "../contexts/ColorPalette";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { IconWrapper } from '../LazyLoader';
import dragHandleRounded from '@iconify/icons-material-symbols/drag-handle-rounded';


function loadMyAsyncData(hash, backendURL) {
    return fetch(`${backendURL("graph/children")}/${hash}`).then(r => r.json());
}



export class DragHandle extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        const {dragHandleProps} = this.props;
        return <div className="dragHandle" {...dragHandleProps}>
                <Suspense fallback={<div>=</div>}>
                    <IconWrapper icon={dragHandleRounded} width="24" />
                </Suspense>
            </div>
        }
}

DragHandle.propTypes = {
    /**
     * an object which should be spread as props on the HTML element to be used as the drag handle.
     * The whole item will be draggable by the wrapped element.
     **/
    dragHandleProps: PropTypes.object
};

export class RowTemplate extends React.Component {
    static contextType = ColorPaletteContext;
    constructor(props) {
        super(props);
    }

    render () {
        const { item, itemSelected, anySelected, dragHandleProps } = this.props;
        const transformation = item.transformation;

        const scaleConstant = 0.02;
        const shadowConstant = 15;
        const scale = itemSelected * scaleConstant + 1;
        const shadow = itemSelected * shadowConstant + 0;
        const dragged = itemSelected !== 0;
        const background = Object.values(this.context.twenty)

        const opacity = itemSelected === 0 ? 1-anySelected*0.5 : 1;

        return ((<div
                className="row_container"
                style={{transform: `scale(${scale})`,
                        zIndex: dragged ? 1 : 0,
                        transformOrigin: 'left',
                        boxShadow: `rgba(0, 0, 0, 0.3) 0px ${shadow}px ${2 * shadow}px 0px`,
                        background: background[transformation.id % background.length],
                        opacity: opacity }}
                >
            {transformation === null ? null :
                <Row key={transformation.hash} transformation={transformation} dragHandleProps={dragHandleProps} itemSelected={itemSelected} />}
                </div>)
        );
    }
}

RowTemplate.propTypes = {
    /**
     * The Transformation object to be displayed
     **/
    item: TRANSFORMATIONWRAPPER,
    /**
     * It starts at 0, and quickly increases to 1 when the item is picked up by the user. 
     */
    itemSelected: PropTypes.number,
    /**
     * It starts at 0, and quickly increases to 1 when any item is picked up by the user.
     */
    anySelected: PropTypes.number,
    /**
     * an object which should be spread as props on the HTML element to be used as the drag handle. 
     * The whole item will be draggable by the wrapped element.
     **/
    dragHandleProps: PropTypes.object
};  


export function Row(props) {
    const { transformation, dragHandleProps, itemSelected } = props;

    const {backendURL} = useSettings();
    const [nodes, setNodes] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const rowbodyRef = useRef(null);
    const headerRef = useRef(null);
    const handleRef = useRef(null);
    const backendURLRef = React.useRef(backendURL);
    const transformationhashRef = React.useRef(transformation.hash)
    const {state: {transformations}} = useTransformations();
    const [shownRecursion, ,] = useShownRecursion();

    useEffect(() => {
        if (headerRef.current && handleRef.current) {
            const headerHeight = headerRef.current.offsetHeight;
            handleRef.current.style.top = `${headerHeight}px`;
        }
    }, []);

    React.useEffect(() => {
        let mounted = true;
        loadMyAsyncData(transformationhashRef.current, backendURLRef.current)
            .then(items => {
                if (mounted) {
                    setNodes(items)
                }
            })
        return () => { mounted = false };
    }, [transformation.id]);

    const checkForOverflow = useCallback(() => {
        if (rowbodyRef !== null && rowbodyRef.current) {
            const e = rowbodyRef.current
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
    }, [rowbodyRef, isOverflowH, overflowBreakingPoint]);

    React.useEffect(() => {
        checkForOverflow()
    }, [checkForOverflow, nodes])

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
                                            }) => transformation.id === t.id && shown) !== null;
    // const style1 = { "backgroundColor": background[transformation.id % background.length] };

    return <div>
        <RowHeader transformation={transformation.rules} ref={headerRef} />
        {dragHandleProps === null ? null : <DragHandle dragHandleProps={dragHandleProps} ref={handleRef} />}
        {!showNodes ? null :
            <div ref={rowbodyRef} className="row_row" >{nodes.map((child) => { 
                if (child.recursive && shownRecursion.indexOf(child.uuid) !== -1) {
                    return <RecursiveSuperNode key={child.uuid} node={child}
                    showMini={isOverflowH}/>
                }
                return <Node key={child.uuid} node={child}
                    showMini={isOverflowH} isSubnode={false} />})}</div>
        }</div>
}


Row.propTypes = {
    /**
     * The Transformation object to be displayed
     */
    transformation: TRANSFORMATION,
    /**
     * an object which should be spread as props on the HTML element to be used as the drag handle. 
     * The whole item will be draggable by the wrapped element.
     **/
    dragHandleProps: PropTypes.object
};


