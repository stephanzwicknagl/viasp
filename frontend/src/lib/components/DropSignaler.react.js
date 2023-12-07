import React from 'react';
import PropTypes, { any } from 'prop-types';

export class DropSignaler extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        const {itemSelected, anySelected} = this.props;
        const brightGreen = '#00ff00';

        const showMultiplier = anySelected && !itemSelected ? anySelected : 0;
        const height = showMultiplier * 0.5;
        const shadowBlurRadius = showMultiplier * 20;
        const shadowSpreadRadius = showMultiplier * 10;
        const backgroundColor = itemSelected ? 'red' : brightGreen;

        const style = {
            position: 'absolute',
            width: '80%',
            left: '10%',
            top: `${height * -0.5}rem`,
            height: `${height}rem`,
            boxShadow: `0px 0px ${shadowBlurRadius}px ${shadowSpreadRadius}px rgba(0, 255, 0, 0.2)`,            backgroundColor: `${backgroundColor}`,
            borderRadius: '5rem',
            zIndex: 100,
        };

        return <div className="dropSignaler" style={style}></div>
        }
}

DropSignaler.propTypes = {
    /**
     * It starts at 0, and quickly increases to 1 when the item is picked up by the user.
     */
    itemSelected: PropTypes.number,
    /**
     * It starts at 0, and quickly increases to 1 when any item is picked up by the user.
     */
    anySelected: PropTypes.number,
};