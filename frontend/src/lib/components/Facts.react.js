import './facts.css';
import React from 'react';
import * as Constants from '../constants';
import {MAPZOOMSTATE} from '../types/propTypes';
import {Node} from './Node.react';
import {OverflowButton} from './OverflowButton.react';
import {useTransformations} from '../contexts/transformations';
import {make_default_nodes} from '../utils';
import {useDebouncedAnimateResize} from '../hooks/useDebouncedAnimateResize';
export function Facts(props) {
    const {transform} = props;
    const {
        state: {transformationDropIndices, transformationNodesMap},
    } = useTransformations();
    const [fact, setFact] = React.useState(make_default_nodes()[0]);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const branchSpaceRef = React.useRef(null);
    const rowbodyRef = React.useRef(null);
    const transformationIdRef = React.useRef('-1');

    useDebouncedAnimateResize(rowbodyRef, transformationIdRef);

    React.useEffect(() => {
        if (transformationNodesMap && transformationNodesMap['-1']) {
            setFact(transformationNodesMap['-1'][0]);
        }
    }, [transformationNodesMap]);

    React.useEffect(() => {
        if (transformationDropIndices !== null) {
            setStyle((prevStyle) => ({
                ...prevStyle,
                opacity: 1 - Constants.opacityMultiplier,
            }));
        } else {
            setStyle((prevStyle) => ({...prevStyle, opacity: 1.0}));
        }
    }, [transformationDropIndices]);

    React.useEffect(() => {
        if (transform.scale < 1) {
            setStyle((prevStyle) => ({
                ...prevStyle,
                width: `${transform.scale * 100}%`,
            }));
        } else {
            setStyle((prevStyle) => ({
                ...prevStyle,
                width: '100%',
            }));
        }
    }, [transform.scale]);

    if (fact === null) {
        return <div className="row_container"></div>;
    }
    return (
        <div className="row_container">
            <div className="row_row" style={style} ref={rowbodyRef}>
                <div
                    className="branch_space"
                    key={fact.uuid}
                    style={{flex: '0 0 100%'}}
                    ref={branchSpaceRef}
                >
                    <Node
                        key={fact.uuid}
                        node={fact}
                        isSubnode={false}
                        branchSpace={branchSpaceRef}
                        transformationId={transformationIdRef.current}
                    />
                </div>
            </div>
            { !fact.showMini && (fact.isExpandableV || fact.isCollapsibleV) ?  (
            <OverflowButton
                transformationId={transformationIdRef.current}
                nodes={[fact]}
            /> ) : null }
        </div>
    );
}

Facts.propTypes = {
    transform: MAPZOOMSTATE,
};
