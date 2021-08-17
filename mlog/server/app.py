import dash, os, sys
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash.dependencies as dd

app = dash.Dash(
    "mlog-server",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
    ],
    routes_pathname_prefix="/",
)

if not "MLOG_DATABASE" in os.environ:
    print("Environment variable MLOG_DATABASE should be set")
    sys.exit(-1)

import mlog.database
database = mlog.database.Database(os.environ["MLOG_DATABASE"])

import graph_page
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Container(graph_page.layout, id="page-content", fluid=True),
    ]
)
graph_page.register(app, database)

# @app.callback(
#     dd.Output("page-content", "children"), [dd.Input("url", "pathname"), dd.Input("url", "search")]
# )
# def display(pathname, query):
#     print(f"A {dash.callback_context.triggered}")
#     return graph_page.layout




if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True)
