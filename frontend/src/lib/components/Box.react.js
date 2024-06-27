import React from 'react';
import './box.css';
import PropTypes from 'prop-types';
import {CLINGRAPHNODE} from '../types/propTypes';
import {useColorPalette} from '../contexts/ColorPalette';
import {useSettings} from '../contexts/Settings';
import {useHighlightedNode} from '../contexts/HighlightedNode';
import {
    useTransformations,
    setClingraphShowMini,
} from '../contexts/transformations';
import {useAnimationUpdater} from '../contexts/AnimationUpdater';
import {debounce} from 'lodash';
import useResizeObserver from '@react-hook/resize-observer';
import * as Constants from '../constants';

function useHighlightedNodeToCreateClassName(node) {
    const [highlightedBox] = useHighlightedNode();
    const [classNames, setClassNames] = React.useState(
        `box_border mouse_over_shadow ${node.uuid} ${
            highlightedBox === node.uuid ? 'highlighted_box' : null
        }`
    );

    React.useEffect(() => {
        setClassNames(
            `box_border mouse_over_shadow ${node.uuid} ${
                highlightedBox === node.uuid ? 'highlighted_box' : null
            }`
        );
    }, [node.uuid, highlightedBox]);
    return classNames;
}

function checkForOverflowE(
    branchSpace,
    imageWidth,
    showMini,
    overflowBreakingPoint,
    setOverflowBreakingPoint,
    setShowMini
) {
    if (
        typeof branchSpace !== 'undefined' &&
        branchSpace !== null &&
        branchSpace.current
    ) {
        const e = branchSpace.current;
        const wouldOverflowNow =
            imageWidth > 0
                ? imageWidth > e.offsetWidth - Constants.overflowThreshold
                : false;
        // We overflowed previously but not anymore
        if (
            overflowBreakingPoint <=
            e.offsetWidth - Constants.overflowThreshold
        ) {
            setShowMini(false);
        }
        if (!showMini && wouldOverflowNow) {
            // We have to react to overflow now but want to remember when we'll not overflow anymore
            // on a resize
            setOverflowBreakingPoint(e.offsetWidth);
            setShowMini(true);
        }
        // We never overflowed and also don't now
        if (overflowBreakingPoint === null && !wouldOverflowNow) {
            setShowMini(false);
        }
    }
}

export function Box(props) {
    const {node, branchSpace} = props;
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const colorPalette = useColorPalette();
    const {backendURL} = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const [imageSize, setImageSize] = React.useState({width: 0, height: 0});
    const {dispatch: dispatchTransformation} = useTransformations();
    const {animationState} = useAnimationUpdater();

    React.useEffect(() => {
        let mounted = true;
        if (mounted && node.uuid && !node.loading) {
            const img = new Image();
            img.onload = function () {
                setImageSize({width: this.width, height: this.height});
            };
            img.src = `${backendURL('graph/clingraph')}/${node.uuid}`;
        }
        return () => {
            mounted = false;
        };
    }, [backendURL, node.uuid, node.loading]);

    const checkForOverflow = React.useCallback(() => {
        checkForOverflowE(
            branchSpace,
            imageSize.width,
            node.showMini,
            overflowBreakingPoint,
            setOverflowBreakingPoint,
            (showMini) => {
                dispatchTransformation(
                    setClingraphShowMini(node.uuid, showMini)
                );
            }
        );
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        branchSpace,
        overflowBreakingPoint,
        animationState.graph_zoom,
        node.showMini,
    ]);

    const debouncedCheckForOverflow = React.useMemo(() => {
        return debounce(checkForOverflow, Constants.DEBOUNCETIMEOUT);
    }, [checkForOverflow]);

    React.useEffect(() => {
        checkForOverflow();
    }, [checkForOverflow, node.showMini]);

    useResizeObserver(
        document.getElementById('content'),
        debouncedCheckForOverflow
    );

    return (
        <div
            className={classNames}
            style={{
                backgroundColor: colorPalette.primary,
                color: colorPalette.primary,
            }}
            id={node.uuid}
        >
            {node.showMini ? (
                <div
                    style={{
                        backgroundColor: colorPalette.primary,
                        color: colorPalette.primary,
                    }}
                    className="mini"
                />
            ) : (
                <div
                    style={{
                        backgroundColor: colorPalette.primary,
                        color: colorPalette.primary,
                    }}
                >
                    {node.loading ? (
                        <div className={'loading'} style={imageSize}></div>
                    ) : (
                        <img
                            src={`${backendURL('graph/clingraph')}/${
                                node.uuid
                            }`}
                            // width={`30px`}
                            alt="Clingraph"
                        />
                    )}
                </div>
            )}
        </div>
    );
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: CLINGRAPHNODE,
    /**
     * The ref to the branch space the node sits in
     */
    branchSpace: PropTypes.object,
};
