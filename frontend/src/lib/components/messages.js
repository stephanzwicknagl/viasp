import React from "react";
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import {RiErrorWarningFill} from "react-icons/ri";
import {useMessages} from "../contexts/UserMessages";


function useColor(level) {
    const colors = useColorPalette();
    if (level === "error") {
        return {ten: colors.error.ten, thirty: colors.error.thirty, sixty: colors.error.sixty}
    }
    if (level === "warn") {
        return {ten: colors.warn.ten, thirty: colors.warn.thirty, sixty: colors.warn.sixty}
    }
    return {}
}

function Message(props) {
    const {message} = props;
    const colors = useColor(message.level);
    return <Expire delay={2000}>
        <div className="user_message" style={{backgroundColor: colors.sixty, color: colors.thirty}}>
            <RiErrorWarningFill/>{message.text}</div>
    </Expire>
}

Message.propTypes = {
    message: PropTypes.exact({
        text: PropTypes.string,
        level: PropTypes.oneOf(["error", "warn"])
    })
}

export function UserMessages() {
    const [{activeMessages},] = useMessages();
    return !activeMessages || activeMessages.length === 0 ? null :
        <div className="user_message_list">{activeMessages.map(message => <Message key={message}
                                                                                   message={message}/>)}</div>
}

function Expire(props) {
    const [isShowingAlert, setShowingAlert] = React.useState(true);
    const [unmount, setUnmount] = React.useState(false);
    const {delay} = props;

    React.useEffect(() => {
        setTimeout(() => {
            setShowingAlert(false);
        }, delay);
    }, []);

    return unmount ? null : <div onTransitionEnd={() => setUnmount(true)}
                                 className={`alert alert-success ${isShowingAlert ? 'alert-shown' : 'alert-hidden'}`}>{props.children}</div>

}

Expire.propTypes = {
    children: PropTypes.element,
    delay: PropTypes.number
}
Expire.defaultProps = {
    delay: 5000
}
