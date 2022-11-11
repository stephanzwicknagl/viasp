import viasp_dash
from dash import Dash, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    viasp_dash.ViaspDash(
        id="myID",
        backendURL="http://localhost:5000"
    ),
    html.Div(id='output')
])


@app.callback(Output('output', 'children'), Input('myID', 'clickedOn'))
def display_output(rule):
    return f"I come from python, you clicked on {rule}"


if __name__ == '__main__':
    app.run_server(debug=False)
