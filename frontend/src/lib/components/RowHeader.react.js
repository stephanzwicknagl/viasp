import React from "react";
import {useColorPalette} from "../contexts/ColorPalette";
import { RULECONTAINER } from "../types/propTypes";

export function RowHeader(props) {
    const { ruleContainer } = props;
    const colorPalette = useColorPalette();
        

    return (
        <div
            style={{
                backgroundColor: colorPalette.primary,
                color: colorPalette.light,
                borderColor: colorPalette.primary,
            }}
            className="row_header"
        >
            {ruleContainer.str_.map((rule) => (
                <div
                    key={rule}
                    style={{whiteSpace: 'pre-wrap', padding: '4px 0'}}
                    dangerouslySetInnerHTML={{
                        __html: rule
                            .replace(/</g, '&lt;')
                            .replace(/>/g, '&gt;')
                            .replace(/\n/g, '<br>'),
                    }}
                />
            ))}
        </div>
    );
}

RowHeader.propTypes = {
    /**
     * The rule container of the transformation
     */
    ruleContainer: RULECONTAINER
};
