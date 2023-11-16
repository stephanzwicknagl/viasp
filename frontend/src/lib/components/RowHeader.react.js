import React from "react";
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";


export function RowHeader(props) {
    const { transformation } = props;
    const colorPalette = useColorPalette();
    return <div style={{
        "backgroundColor": colorPalette.secondary,
        "color": colorPalette.light,
        "borderColor": colorPalette.secondary
    }}
        className="row_header">{transformation.map(rule =>
            <div key={rule}
                style={{ whiteSpace: 'pre' }}
                dangerouslySetInnerHTML={{
                    __html: rule.replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/\n/g, "<br>")
                }} />)}
    </div>
}

RowHeader.propTypes = {
    /**
     * The rule string to be displayed in the header
     */
    transformation: PropTypes.arrayOf(PropTypes.string),
    /**
     * Whether the user has decided to show or hide the content of the row
     */
    contentIsShown: PropTypes.bool,

    /**
     * A callback function when the user clicks on the RuleHeader
     */
    onToggle: PropTypes.func
};
