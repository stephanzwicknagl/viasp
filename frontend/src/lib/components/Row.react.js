import React from 'react';
import {Node, RecursiveSuperNode} from './Node.react';
import * as Constants from '../constants';
import './row.css';
import PropTypes from 'prop-types';
import {RowHeader} from './RowHeader.react';
import {
    useTransformations,
    setTransformationDropIndices,
    TransformationContext,
} from '../contexts/transformations';
import {MAPZOOMSTATE, TRANSFORMATION, TRANSFORMATIONWRAPPER} from '../types/propTypes';
import {ColorPaletteContext} from '../contexts/ColorPalette';
import {useShownRecursion} from '../contexts/ShownRecursion';
import {make_default_nodes} from '../utils';
import {AnimationUpdater} from '../contexts/AnimationUpdater';
import {DragHandle} from './DragHandle.react';
import {useDebouncedAnimateResize} from '../hooks/useDebouncedAnimateResize';


export class RowTemplate extends React.Component {
    static contextType = TransformationContext;
    constructor(props) {
        super(props);
        this.rowRef = React.createRef();
        this.state = {
            canBeDropped: false,
            transformations: [],
            possibleSorts: [],
        };
        this.intervalId = null;
    }

    componentDidMount() {
        this.setState({
            transformations: this.context.state.transformations,
            possibleSorts: this.context.state.possibleSorts,
        });
    }

    componentDidUpdate(prevProps, prevState) {
        if (
            this.props.itemSelected > prevProps.itemSelected &&
            this.context.state.transformationDropIndices !==
                this.props.item.transformation.adjacent_sort_indices &&
            prevProps.itemSelected !== this.props.itemSelected
        ) {
            this.context.dispatch(
                setTransformationDropIndices(this.props.item.transformation.adjacent_sort_indices)
            )
        }
        if (
            this.props.itemSelected < prevProps.itemSelected &&
            this.context.state.transformationDropIndices ===
                this.props.item.transformation.adjacent_sort_indices &&
            prevProps.itemSelected !== this.props.itemSelected
        ) {
            this.context.dispatch(setTransformationDropIndices(null));
        }
        if (this.props.itemSelected > Constants.rowAnimationPickupThreshold && this.intervalId === null) {
            this.intervalId = setInterval(() => {
                const element = this.rowRef.current;
                if (element === null) {
                    return;
                }
                this.setAnimationState((oldValue) => ({
                    ...oldValue,
                    [this.props.item.id]: {
                        ...oldValue[this.props.item.id],
                        width: element.clientWidth,
                        height: element.clientHeight,
                        top: element.offsetTop,
                        left: element.offsetLeft,
                    },
                }));
            }, Constants.rowAnimationIntervalInMs);
        }
        if (this.props.itemSelected < Constants.rowAnimationPickupThreshold && this.intervalId !== null) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    render() {
        const {item, itemSelected, anySelected, dragHandleProps, commonProps} = this.props;
        const transformation = item.transformation;

        return (
            <AnimationUpdater.Consumer>
                {({setAnimationState}) => {
                    this.setAnimationState = setAnimationState;
                    return (
                        <TransformationContext.Consumer>
                            {({state: {transformationDropIndices}}) => {
                                return (
                                    <ColorPaletteContext.Consumer>
                                        {({rowShading}) => {
                                            const scaleConstant = 0.005;
                                            const shadowConstant = 15;
                                            const scale =
                                                itemSelected * scaleConstant +
                                                1;
                                            const shadow =
                                                itemSelected * shadowConstant +
                                                0;
                                            const background = rowShading;
                                            const thisCanDrop =
                                                transformationDropIndices !== null
                                                    ? transformationDropIndices.lower_bound <= (transformation.id) && transformation.id <= transformationDropIndices.upper_bound
                                                    : false;
                                                

                                            const containerStyle = {
                                                position: 'relative',
                                                maxHeight: '100%',
                                                transform: `scale(${scale})`,
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
                                                    thisCanDrop || itemSelected
                                                        ? 1
                                                        : 1 -
                                                          Constants.opacityMultiplier *
                                                              this.props
                                                                  .anySelected,
                                            };
                                            return (
                                                <div
                                                    className="row_signal_container"
                                                    style={containerStyle}
                                                    ref={this.rowRef}
                                                >
                                                    {transformation ===
                                                    null ? null : (
                                                        <Row
                                                            key={
                                                                transformation.hash
                                                            }
                                                            transformation={
                                                                transformation
                                                            }
                                                            dragHandleProps={
                                                                dragHandleProps
                                                            }
                                                            transform = {commonProps.transform}
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
                }}
            </AnimationUpdater.Consumer>
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
    /**
     * The common props for all rows
     **/
    commonProps: PropTypes.shape({
        transform: MAPZOOMSTATE
    }),
};

export function Row(props) {
    const {transformation, dragHandleProps, transform} = props;
    const {
        state: {transformations, transformationNodesMap, isSortable, transformationDropIndices},
    } = useTransformations();
    const [nodes, setNodes] = React.useState(make_default_nodes());
    const rowbodyRef = React.useRef(null);
    const headerRef = React.useRef(null);
    const handleRef = React.useRef(null);
    const [shownRecursion, ,] = useShownRecursion();
    const transformationIdRef = React.useRef(transformation.id);

    useDebouncedAnimateResize(rowbodyRef, transformationIdRef);

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


    const showNodes =
        transformations.find(
            ({transformation: t, shown}) => transformation.id === t.id && shown
        ) !== null;

    const branchSpaceRefs = React.useRef([]);
    React.useEffect(() => {
        branchSpaceRefs.current = nodes.map(
            (_, i) => branchSpaceRefs.current[i] ?? React.createRef()
        );
    }, [nodes]);

    return (
        <div
            className={`row_container ${transformation.hash}`}
            >
            {transformation.rules.str_.length === 0 ? null : (
                <RowHeader
                    ruleContainer={transformation.rules}
                />
            )}
            {dragHandleProps === null || !isSortable ? null : (
                <DragHandle
                    ref={handleRef}
                    dragHandleProps={dragHandleProps}
                />
            )}
            {!showNodes ? null : (
                <div ref={rowbodyRef} 
                className="row_row"
                style={{
                    width: `${nodes.length === 1 ? 100 : transform.scale * 100}%`,
                    transform: `translateX(${nodes.length === 1 ? 0 : transform.translation.x}px)`,
                }}
                >
                    {nodes.map((child, index) => {
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
                                    ref={branchSpaceRefs.current[index]}
                                >
                                    <RecursiveSuperNode
                                        key={child.uuid}
                                        node={child}
                                        branchSpace={
                                            branchSpaceRefs.current[index]
                                        }
                                    />
                                </div>
                            );
                        }
                        return (
                            <div
                                className="branch_space"
                                key={child.uuid}
                                style={{flex: `0 0 ${space_multiplier}%`}}
                                ref={branchSpaceRefs.current[index]}
                            >
                                <Node
                                    key={child.uuid}
                                    node={child}
                                    isSubnode={false}
                                    branchSpace={branchSpaceRefs.current[index]}
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
    /**
     * The current zoom transformation of the graph
     */
    transform: MAPZOOMSTATE,
};
