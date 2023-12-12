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

    const canBeDroppedAbove = React.useCallback(
        () => {
            // console.log('Calculating if it can be dropped above...');
            const itemSelected = item.props.itemSelected;

            if (currentDragged !== '' && itemSelected === 0 && transformations) {
                const sort = transformations.map((t) => t.hash);
                const oldIndex = sort.findIndex(
                    (h) => h === currentDragged
                );
                const newIndex =
                    sort.findIndex(
                        (h) => h === item.props.item.hash
                    ) - 1;
                const [removed] = sort.splice(oldIndex, 1);
                sort.splice(newIndex, 0, removed);
                // generate hash
                computeSortHash(sort).then((newHash) => {
                    // compare hash to potential sorts
                    // console.log('Calculating:', {
                    //     newHash: newHash,
                    //     possibleSorts: possibleSorts,
                    //     includes: possibleSorts?.includes(newHash),
                    // });
                    return possibleSorts?.includes(newHash);
                });
            }
            return false;
        }, [transformations, possibleSorts, currentDragged, item.props.itemSelected, item.props.item.hash]
    );

    const canBeDroppedBelow = React.useCallback(
        () => {
            return true;
        }, []
    );

    React.useEffect(
        () => {
            setTopColor(canBeDroppedAbove() ? 'green' : 'red');
        }, [
        canBeDroppedAbove,
        transformations,
        possibleSorts,
        currentDragged,
        item.props.itemSelected,
        item.props.item.hash,
        ]
    );


    
    const brightGreen = '#00ff00';
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
    const height = showMultiplier * heightMultiplier;

    const blurRadiusMultiplier = 20;
    const shadowSpreadRadiusMultiplier = 10;
    const shadowBlurRadius = showMultiplier * blurRadiusMultiplier;
    const shadowSpreadRadius = showMultiplier * shadowSpreadRadiusMultiplier;
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