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
import {showError, useMessages} from '../contexts/UserMessages';
import {useSettings} from '../contexts/Settings';
import {TRANSFORMATION, TRANSFORMATIONWRAPPER} from '../types/propTypes';
import {ColorPaletteContext} from '../contexts/ColorPalette';
import {useShownRecursion} from '../contexts/ShownRecursion';
import {IconWrapper} from '../LazyLoader';
import dragHandleRounded from '@iconify/icons-material-symbols/drag-handle-rounded';
import {make_default_nodes} from '../utils';

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
            this.props.itemSelected > prevProps.itemSelected &&
            this.context.state.currentDragged !==
                this.props.item.transformation.hash &&
            prevProps.itemSelected !== this.props.itemSelected
        ) {
            this.context.dispatch(
                setCurrentDragged(this.props.item.transformation.hash)
            );
        }
        if (
            this.props.itemSelected < prevProps.itemSelected &&
            this.context.state.currentDragged ===
                this.props.item.transformation.hash &&
            prevProps.itemSelected !== this.props.itemSelected
        ) {
            this.context.dispatch(setCurrentDragged(''));
        }
    }

    render() {
        const {item, itemSelected, anySelected, dragHandleProps} = this.props;
        const transformation = item.transformation;

        return (
            <TransformationContext.Consumer>
                {({state: {canDrop}}) => {
                    return (
                        <ColorPaletteContext.Consumer>
                            {({rowShading}) => {
                                const scaleConstant = 0.02;
                                const shadowConstant = 15;
                                const opacityMultiplier = 0.8;
                                const scale = itemSelected * scaleConstant + 1;
                                const shadow =
                                    itemSelected * shadowConstant + 0;
                                const dragged = itemSelected !== 0;
                                const background = rowShading;
                                const thisCanDrop =
                                    canDrop !== null
                                        ? canDrop[item.transformation.hash] ||
                                          ''
                                        : '';

                                const containerStyle = {
                                    position: 'relative',
                                    maxHeight: '100%',
                                    transform: `scale(${scale})`,
                                    zIndex: dragged ? 1 : 0,
                                    transformOrigin: 'left',
                                    boxShadow: `rgba(0, 0, 0, 0.3) 0px ${shadow}px ${
                                        2 * shadow
                                    }px 0px`,
                                    background:
                                        background[
                                            transformation.id %
                                                background.length
                                        ],
                                    opacity:
                                        thisCanDrop.length > 0 || itemSelected
                                            ? 1
                                            : 1 -
                                              opacityMultiplier *
                                                  this.props.anySelected,
                                };
                                return (
                                    <div
                                        className="row_signal_container"
                                        style={containerStyle}
                                        ref={this.rowRef}
                                    >
                                        {transformation === null ? null : (
                                            <Row
                                                key={transformation.hash}
                                                transformation={transformation}
                                                dragHandleProps={
                                                    dragHandleProps
                                                }
                                            />
                                        )}
                                    </div>
                                );
                            }}
                        </ColorPaletteContext.Consumer>
                    );
                }}
            </TransformationContext.Consumer>
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
    const {transformation, dragHandleProps} = props;

    const {
        state: {transformationNodesMap},
    } = useTransformations();
    const [nodes, setNodes] = React.useState(make_default_nodes());
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const rowbodyRef = useRef(null);
    const headerRef = useRef(null);
    const handleRef = useRef(null);
    const {
        state: {transformations},
    } = useTransformations();
    const [shownRecursion, ,] = useShownRecursion();

    React.useEffect(() => {
        if (headerRef.current && handleRef.current) {
            const headerHeight = headerRef.current.offsetHeight;
            handleRef.current.style.top = `${headerHeight}px`;
        }
    }, []);

    React.useEffect(() => {
        if (
            transformationNodesMap &&
            transformationNodesMap[transformation.id]
        ) {
            setNodes(transformationNodesMap[transformation.id]);
        }
    }, [transformationNodesMap, transformation.id]);

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

    const showNodes =
        transformations.find(
            ({transformation: t, shown}) => transformation.id === t.id && shown
        ) !== null;

    return (
        <div className="row_container">
            <RowHeader transformation={transformation.rules} />
            {dragHandleProps === null ? null : (
                <DragHandle dragHandleProps={dragHandleProps} ref={handleRef} />
            )}
            {!showNodes ? null : (
                <div ref={rowbodyRef} className="row_row">
                    {nodes.map((child) => {
                        const space_multiplier = child.space_multiplier * 100;
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
