/* eslint no-magic-numbers: 0 */
import React from 'react';
import colorPaletteData from '../../../backend/src/viasp/server/static/colorPalette.json';

import { ViaspDash } from '../lib';

const App = () => {
    const backend_url = "http://localhost:5050";
    return (
        <div>
            <ViaspDash
                id="myID"
                backendURL={backend_url}
                colorPalette={colorPaletteData}
            />
        </div>
    );
};


export default App;