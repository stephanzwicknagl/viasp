import React from 'react';
import './box.css';
import {CLINGRAPHNODE} from '../types/propTypes';
import {useColorPalette} from '../contexts/ColorPalette';
import {useSettings} from '../contexts/Settings';
import {useHighlightedNode} from '../contexts/HighlightedNode';

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

export function Box(props) {
    const {node} = props;
    const colorPalette = useColorPalette();
    const {backendURL} = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const [imageSize, setImageSize] = React.useState({width: 0, height: 0});

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

    return (
        <div
            className={classNames}
            style={{
                backgroundColor: colorPalette.primary,
                color: colorPalette.primary,
            }}
            id={node.uuid}
        >
            <div
                style={{
                    backgroundColor: colorPalette.primary,
                    color: colorPalette.primary,
                }}
            >
                {node.loading ? (
                    <div className={'loading'} style={imageSize}>
                    </div>
                ) : (
                    <img
                        src={`${backendURL('graph/clingraph')}/${node.uuid}`}
                        alt="Clingraph"
                    />
                )}
            </div>
        </div>
    );
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: CLINGRAPHNODE,
};
