import React from 'react';
import './draghandle.css';
import PropTypes from 'prop-types';
import {IconWrapper} from '../LazyLoader';

export class DragHandle extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        const {dragHandleProps} = this.props;
        return (
            <div
                className="dragHandle"
                {...dragHandleProps}
            >
                <React.Suspense fallback={<div>=</div>}>
                    <IconWrapper icon={"dragHandleRounded"} width="24" />
                </React.Suspense>
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

