import React from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import './DropSignaler.css';
import { useTransformations } from '../contexts/transformations';
import {computeSortHash} from '../utils';


export function DropSignalerContainer(props) {
    const {transformations, draggableList} = props;
    const [items, setItems] = React.useState(null);

    React.useEffect(() => {
        getItemInstances(transformations, draggableList);
    }, [transformations, draggableList]);

    function getItemInstances(transformations, draggableList) {
        const dragElements = transformations?.map(t => draggableList?.getItemInstance(t.hash));
        setItems(dragElements);
    };

    return <div className="dropSignalerContainer">
            {items?.map((item, index) => {
                return (
                    <DropSignaler
                        key={`dragSignaler_${item.props.item.hash}`}
                        item={item}
                        isLastElement={index === transformations.length-1}
                    />
                );
            })
            }
    </div>
}

DropSignalerContainer.propTypes = {
    /**
     * The transformations in the order they are displayed
     */
    transformations: PropTypes.array,
    /**
     * A reference to the current draggable list
     */
    draggableList: PropTypes.object,
};


function DropSignaler(props) {
    const {item, isLastElement} = props;
    const [topSignalerParent, setTopSignalerParent] = React.useState(null);
    const [bottomSignalerParent, setBottomSignalerParent] = React.useState(null);
    const [topColor, setTopColor] = React.useState('red');
    const {
        state: {transformations, possibleSorts, currentDragged}
    } = useTransformations();

    // on mount and unmount
    React.useEffect(
        () => {
            // Create a new div at the start of the parent element
            // to position the upperDropSignaler
            const parentElement = item.rowRef.current;
            const div = document.createElement('div');
            parentElement.insertBefore(div, parentElement.firstChild);
            setTopSignalerParent(div);

            if (isLastElement) {
                setBottomSignalerParent(parentElement);
            }

            return () => {
                // Remove the div at the start of the parent element
                const parentElement = item.rowRef.current;
                parentElement.removeChild(parentElement.firstChild);
                setTopSignalerParent(null);
                setBottomSignalerParent(null);
            };
        }, [] /* eslint-disable-line react-hooks/exhaustive-deps */
    );

    React.useEffect(
        () => {
            setTopColor(
                canBeDropped(
                    transformations,
                    possibleSorts,
                    currentDragged,
                    item.props.item.hash,
                    true
                )
                    ? 'green'
                    : 'red'
            );
        }, [
        transformations,
        possibleSorts,
        currentDragged,
        item.props.itemSelected,
        item.props.item.hash,
        ]
    );


    
    // todo: when does showMultiplier rerender, or what?
    const [showMultiplier, setShowMultiplier] = React.useState(1);

    React.useEffect(() => {
        if (item.props.anySelected && !item.props.itemSelected) {
            setShowMultiplier(item.props.anySelected);
        } else {
            setShowMultiplier(0);
        }
    }, [item.props.anySelected, item.props.itemSelected]);
    
    const heightMultiplier = 0.5;
    const height = item.props.anySelected * heightMultiplier;

    const blurRadiusMultiplier = 20;
    const shadowSpreadRadiusMultiplier = 10;
    const shadowBlurRadius = item.props.anySelected * blurRadiusMultiplier;
    const shadowSpreadRadius =
        item.props.anySelected * shadowSpreadRadiusMultiplier;
    const topStyle = {
        position: 'relative',
        top: `-${0.5*height}rem`,
        height: `${height}rem`,
        // boxShadow: `0px 0px ${shadowBlurRadius}px ${shadowSpreadRadius}px rgba(0, 255, 0, 0.2)`,
        backgroundColor: `${topColor}`,
    };

    // const myStyleBottom = {
    //     position: 'relative',
    //     bottom: `-${0.5 * height}px`,
    //     // top: `-${0.5 * height}px`,
    //     height: `${height}rem`,
    //     boxShadow: `0px 0px ${shadowBlurRadius}px ${shadowSpreadRadius}px rgba(0, 255, 0, 0.2)`,
    // };

    // if (this.props.isLastElement) {
    //     myStyleBottom.backgroundColor = this.canBeDroppedBelow()
    //         ? brightGreen
    //         : 'red';
    // }

    return (<>
                {
                    topSignalerParent &&
                        ReactDOM.createPortal(
                            <div
                                className="dropSignaler"
                                style={topStyle}
                            ></div>,
                            topSignalerParent
                        )
                }
                {
                //         isLastElement &&
                //         bottomSignalerParent &&
                //         ReactDOM.createPortal(
                //             <div
                //                 className="dropSignaler"
                //                 style={myStyleBottom}
                //             ></div>,
                //             bottomSignalerParent
                //         );
                //
                }

            </>);
}

DropSignaler.propTypes = {
    /**
     * The row DOM element to which this signaler belongs
     */
    item: PropTypes.object,
    /**
     * Whether this is the last element in the list of transformations
     */
    isLastElement: PropTypes.bool,
};

async function canBeDropped (transformations, possibleSorts, currentDragged, hash, dropAbove) {
    if (currentDragged !== '' && transformations) {
        const sort = transformations.map((t) => t.hash);
        const oldIndex = sort.findIndex(
            (h) => h === currentDragged
        );
        const [removed] = sort.splice(oldIndex, 1);
        let newIndex = sort.findIndex((h) => h === hash);
        if (!dropAbove) {
            newIndex += 1;
        };
        sort.splice(newIndex, 0, removed);
        const newHash = await computeSortHash(sort);
        return possibleSorts?.includes(newHash);
    }
    return false;
}

export function HereDropSignaler(props) {
    const {hash, itemSelected, anySelected, rowRef} = props;
    const green = '#00ff00';
    const red = '#ff0000';
    const [topColor, setTopColor] = React.useState(red);
    const [belowColor, setBelowColor] = React.useState(red);
    const {
        state: {transformations, possibleSorts, currentDragged},
    } = useTransformations();

    const isLastElement = transformations[transformations.length-1].hash === hash;

    React.useEffect(() => {
        canBeDropped(
            transformations, 
            possibleSorts, 
            currentDragged, 
            hash, 
            true
        ).then((ans) => {
                setTopColor(ans ? green : red);
        })
        if (isLastElement) {
            canBeDropped(
                transformations,
                possibleSorts,
                currentDragged,
                hash,
                false
            ).then((ans) => {
                setBelowColor(ans ? green : red);
            });
        }
    }, [
        transformations,
        possibleSorts,
        currentDragged,
        hash,
        isLastElement,
    ]);


    const showMultiplier = anySelected && !itemSelected ? anySelected : 0;
    const heightMultiplier = 0.5;

    const height = showMultiplier * heightMultiplier;
    const blurRadiusMultiplier = 20;
    const shadowSpreadRadiusMultiplier = 10;
    const shadowOpacity = '33';
    const shadowBlurRadius = showMultiplier * blurRadiusMultiplier;
    const shadowSpreadRadius = showMultiplier * shadowSpreadRadiusMultiplier;
    const topStyle = {
        top: `-${0.5 * height}rem`,
        height: `${height}rem`,
        boxShadow: `0px 0px ${shadowBlurRadius}px ${shadowSpreadRadius}px ${topColor}${shadowOpacity}`,
        backgroundColor: `${topColor}`,
    };

    const myStyleBottom = {
        position: 'relative',
        bottom: `-${0.5 * height}px`,
        height: `${height}rem`,
        boxShadow: `0px 0px ${shadowBlurRadius}px ${shadowSpreadRadius}px ${belowColor}${shadowOpacity}`,
        backgroundColor: `${belowColor}`,
    };

    const [bottomSignalerParent, setBottomSignalerParent] =
            React.useState(null);
    React.useEffect(
        () => {
            const rowRefcurrent = rowRef.current;
            // Create a new div at the start of the parent element
            // to position the upperDropSignaler
            const parentElement = rowRefcurrent;
            const div = document.createElement('div');
            parentElement.insertBefore(div, parentElement.firstChild);

            if (isLastElement) {
                setBottomSignalerParent(parentElement);
            }

            return () => {
                // Remove the div at the start of the parent element
                const parentElement = rowRefcurrent;
                parentElement.removeChild(parentElement.firstChild);
                setBottomSignalerParent(null);
            };
        },
        [] /* eslint-disable-line react-hooks/exhaustive-deps */
    );

    return (
        <>
            <div className="dropSignaler" style={topStyle}></div>
            {
                isLastElement &&
                bottomSignalerParent &&
                ReactDOM.createPortal(
                    <div
                        className="dropSignaler"
                        style={myStyleBottom}
                    ></div>,
                    bottomSignalerParent
                )
            }
        </>
    );
}

HereDropSignaler.propTypes = {
    /**
     * The corresponding transformation hash the signaler belongs to
     * */
    hash: PropTypes.string,
    /**
     * It starts at 0, and quickly increases to 1 when the item is picked up by the user.
     */
    itemSelected: PropTypes.number,
    /**
     * It starts at 0, and quickly increases to 1 when any item is picked up by the user.
     */
    anySelected: PropTypes.number,
    /**
     * The row DOM element to which this signaler belongs
     */
    rowRef: PropTypes.object,
};