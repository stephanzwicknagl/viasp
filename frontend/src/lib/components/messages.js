import React from 'react';
import PropTypes from 'prop-types';
import {useColorPalette} from '../contexts/ColorPalette';
import {RiErrorWarningFill} from 'react-icons/ri';
import {useMessages} from '../contexts/UserMessages';

function useColor(level) {
    const colorPalette = useColorPalette();
    if (level === 'error') {
        return {background: colorPalette.error, color: colorPalette.dark};
    }
    if (level === 'warn') {
        return {background: colorPalette.warn, color: colorPalette.dark};
    }
    return {};
}

function Message(props) {
    const {message} = props;
    const colors = useColor(message.level);
    return (
        <Expire delay={5000}>
            <div
                className="user_message"
                style={{
                    backgroundColor: colors.background,
                    color: colors.color,
                }}
            >
                <RiErrorWarningFill />
                {message.text}
            </div>
        </Expire>
    );
}

Message.propTypes = {
    message: PropTypes.exact({
        text: PropTypes.string,
        level: PropTypes.oneOf(['error', 'warn']),
    }),
};

export function UserMessages() {
    const [{activeMessages}] = useMessages();
    return !activeMessages || activeMessages.length === 0 ? null : (
        <div className="user_message_list">
            {activeMessages.map((message, index) => (
                <Message key={index} message={message} />
            ))}
        </div>
    );
}

function Expire(props) {
    const [isShowingAlert, setShowingAlert] = React.useState(true);
    const [unmount, setUnmount] = React.useState(false);
    const {delay} = props;

    React.useEffect(() => {
        setTimeout(() => {
            setShowingAlert(false);
        }, delay);
    }, [delay]);

    return unmount ? null : (
        <div
            onTransitionEnd={() => setUnmount(true)}
            className={`alert alert-success ${
                isShowingAlert ? 'alert-shown' : 'alert-hidden'
            }`}
        >
            {props.children}
        </div>
    );
}

Expire.propTypes = {
    children: PropTypes.element,
    delay: PropTypes.number,
};
Expire.defaultProps = {
    delay: 5000,
};
