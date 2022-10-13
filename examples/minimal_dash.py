from viasp.server import startup

app = startup.run()

if __name__ == '__main__':
    app.run_server(debug=True)
