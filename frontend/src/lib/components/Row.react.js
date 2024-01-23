import React, {useRef, useEffect, useCallback, Suspense} from 'react';
import {Node, RecursiveSuperNode} from './Node.react';
import './row.css';
import PropTypes from 'prop-types';
import {RowHeader} from './RowHeader.react';
import {
    useTransformations,
    setCurrentDragged,
    TransformationContext,
} from '../contexts/transformations';
import {useSettings} from '../contexts/Settings';
import {TRANSFORMATION, TRANSFORMATIONWRAPPER} from '../types/propTypes';
import {ColorPaletteContext} from '../contexts/ColorPalette';
import {useShownRecursion} from '../contexts/ShownRecursion';
import {IconWrapper} from '../LazyLoader';
import dragHandleRounded from '@iconify/icons-material-symbols/drag-handle-rounded';
import {computeSortHash} from '../utils';

function loadMyAsyncData(hash, backendURL) {
    return fetch(`${backendURL('graph/children')}/${hash}`).then((r) =>
        r.json()
    );
}

async function canBeDropped(
    transformations,
    possibleSorts,
    currentDragged,
    hash
) {
    if (currentDragged !== '' && transformations) {
        const sort = transformations.map((t) => t.hash);
        const oldIndex = sort.findIndex((h) => h === currentDragged);
        const [removed] = sort.splice(oldIndex, 1);
        let newIndex = sort.findIndex((h) => h === hash);
        if (newIndex >= oldIndex) {
            newIndex += 1;
        }
        sort.splice(newIndex, 0, removed);
        const newHash = await computeSortHash(sort);
        return possibleSorts?.includes(newHash);
    }
    return false;
}

export class DragHandle extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        const {dragHandleProps} = this.props;
        return (
            <div className="dragHandle" {...dragHandleProps}>
                <Suspense fallback={<div>=</div>}>
                    <IconWrapper icon={dragHandleRounded} width="24" />
                </Suspense>
            </div>
        );
    }
}

DragHandle.propTypes = {
    /**
     * an object which should be spread as props on the HTML element to be used as the drag handle.
     * The whole item will be draggable by the wrapped element.
     **/
    dragHandleProps: PropTypes.object,
};

export class RowTemplate extends React.Component {
    static contextType = TransformationContext;
    constructor(props) {
        super(props);
        this.rowRef = React.createRef();
        this.state = {
            canBeDropped: false,
            transformations: [],
            possibleSorts: [],
            currentDragged: '',
        };
    }

    componentDidMount() {
        this.setState({
            transformations: this.context.state.transformations,
            possibleSorts: this.context.state.possibleSorts,
            currentDragged: this.context.state.currentDragged,
        });
    }

    componentDidUpdate(prevProps, prevState) {
        if (
            this.props.itemSelected > 0 &&
            this.context.state.currentDragged !==
                this.props.item.transformation.hash &&
            prevProps.itemSelected !== this.props.itemSelected
        ) {
            this.context.dispatch(
                setCurrentDragged(this.props.item.transformation.hash)
            );
        }
        if (
            this.context.state.transformations !== prevState.transformations ||
            this.context.state.possibleSorts !== prevState.possibleSorts ||
            this.context.state.currentDragged !== prevState.currentDragged ||
            prevProps.item.transformation.hash !==
                this.props.item.transformation.hash
        ) {
            canBeDropped(
                    this.context.state.transformations,
                    this.context.state.possibleSorts,
                    this.context.state.currentDragged,
                    this.props.item.transformation.hash
                ).then((ans) => {
                    if (this.state.canBeDropped !== ans) {
                        this.setState({
                            canBeDropped: ans,
                        });
                    }
                });
        }
    }

    render() {
        const {item, itemSelected, anySelected, dragHandleProps} = this.props;
        const transformation = item.transformation;

        return (
            <ColorPaletteContext.Consumer>
                {({rowShading}) => {
                    const scaleConstant = 0.02;
                    const shadowConstant = 15;
                    const opacityMultiplier = 0.8;
                    const scale = itemSelected * scaleConstant + 1;
                    const shadow = itemSelected * shadowConstant + 0;
                    const dragged = itemSelected !== 0;
                    const background = Object.values(rowShading);


                    const containerStyle = {
                        position: 'relative',
                        transform: `scale(${scale})`,
                        zIndex: dragged ? 1 : 0,
                        transformOrigin: 'left',
                        boxShadow: `rgba(0, 0, 0, 0.3) 0px ${shadow}px ${
                            2 * shadow
                        }px 0px`,
                        background:
                            background[transformation.id % background.length],
                        opacity: this.state.canBeDropped || itemSelected
                            ? 1
                            : 1 - opacityMultiplier * this.props.anySelected,
                    };
                    return (
                        <div
                            className="row_signal_container"
                            style={containerStyle}
                            ref={this.rowRef}
                        >
                            {transformation === null ? null : (
                                <>
                                    {/* <HereDropSignaler
                                        hash={transformation.hash}
                                        itemSelected={itemSelected}
                                        anySelected={anySelected}
                                        rowRef={this.rowRef}
                                    /> */}
                                    <Row
                                        key={transformation.hash}
                                        transformation={transformation}
                                        dragHandleProps={dragHandleProps}
                                        itemSelected={itemSelected}
                                    />
                                </>
                            )}
                        </div>
                    );
                }}
            </ColorPaletteContext.Consumer>
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
    dragHandleProps: PropTypes.object,
};

export function Row(props) {
    const {transformation, dragHandleProps, itemSelected} = props;

    const {backendURL} = useSettings();
    const [nodes, setNodes] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const rowbodyRef = useRef(null);
    const headerRef = useRef(null);
    const handleRef = useRef(null);
    const backendURLRef = React.useRef(backendURL);
    const transformationhashRef = React.useRef(transformation.hash);
    const {
        state: {transformations, currentDragged},
        dispatch: dispatchTransformation,
    } = useTransformations();
    const dispatchTransformationRef = React.useRef(dispatchTransformation);
    const [shownRecursion, ,] = useShownRecursion();

    useEffect(() => {
        if (headerRef.current && handleRef.current) {
            const headerHeight = headerRef.current.offsetHeight;
            handleRef.current.style.top = `${headerHeight}px`;
        }
    }, []);

    React.useEffect(() => {
        let mounted = true;
        loadMyAsyncData(
            transformationhashRef.current,
            backendURLRef.current
        ).then((items) => {
            if (mounted) {
                setNodes(items);
            }
        });
        return () => {
            mounted = false;
        };
    }, [transformation.id]);

    const checkForOverflow = useCallback(() => {
        if (rowbodyRef !== null && rowbodyRef.current) {
            const e = rowbodyRef.current;
            const wouldOverflowNow = e.offsetWidth < e.scrollWidth;
            // We overflowed previously but not anymore
            if (overflowBreakingPoint <= e.offsetWidth) {
                setIsOverflowH(false);
            }
            if (!isOverflowH && wouldOverflowNow) {
                // We have to react to overflow now but want to remember when we'll not overflow anymore
                // on a resize
                setOverflowBreakingPoint(e.offsetWidth);
                setIsOverflowH(true);
            }
            // We never overflowed and also don't now
            if (overflowBreakingPoint === null && !wouldOverflowNow) {
                setIsOverflowH(false);
            }
        }
    }, [rowbodyRef, isOverflowH, overflowBreakingPoint]);

    React.useEffect(() => {
        checkForOverflow();
    }, [checkForOverflow, nodes]);

    React.useEffect(() => {
        window.addEventListener('resize', checkForOverflow);
        return (_) => window.removeEventListener('resize', checkForOverflow);
    });
    if (nodes === null) {
        return (
            <div>
                <RowHeader transformation={transformation.rules} />
                <div>Loading Transformations..</div>
            </div>
        );
    }
    const showNodes =
        transformations.find(
            ({transformation: t, shown}) => transformation.id === t.id && shown
        ) !== null;
    // const style1 = { "backgroundColor": background[transformation.id % background.length] };

    return (
        <div className="row_container">
            <RowHeader transformation={transformation.rules} ref={headerRef} />
            {dragHandleProps === null ? null : (
                <DragHandle dragHandleProps={dragHandleProps} ref={handleRef} />
            )}
            {!showNodes ? null : (
                <div ref={rowbodyRef} className="row_row">
                    {nodes.map((child) => {
                        const space_multiplier = 25;
                        // const space_multiplier = child.space_multiplier * 100;
                        if (
                            child.recursive &&
                            shownRecursion.indexOf(child.uuid) !== -1
                        ) {
                            return (
                                <div
                                    className="branch_space"
                                    key={child.uuid}
                                    style={{flex: `0 0 ${space_multiplier}%`}}
                                >
                                    <RecursiveSuperNode
                                    key={child.uuid}
                                    node={child}
                                    showMini={isOverflowH}
                                />
                                </div>
                            );
                        }
                        return (
                            <div
                                className="branch_space"
                                key={child.uuid}
                                style={{flex: `0 0 ${space_multiplier}%`}}
                            >
                                <Node
                                    key={child.uuid}
                                    node={child}
                                    showMini={isOverflowH}
                                    isSubnode={false}
                                />
                            </div>
                            );
                    })}
                </div>
            )}
        </div>
    );
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
    dragHandleProps: PropTypes.object,
    /**
     * It starts at 0, and quickly increases to 1 when the item is picked up by the user.
     */
    itemSelected: PropTypes.number,
};
