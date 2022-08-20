import viasp_dash
from dash import Dash
from viasp import start_backend

start_backend.run()
app = Dash(__name__)

app.layout = viasp_dash.ViaspDash(
    id="myID",
    backendURL="http://localhost:5050"
)

if __name__ == '__main__':
    app.run_server(debug=True)
