import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_editor_components as dec
import dash_html_components as html
import dash.dependencies as dd
import urllib, dash, dash_table, yaml
import mlog.database

multiple_header_rows = True

layout = dbc.Container([
    dcc.Store(id="editor-target", data=None),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(id="graph-factories-parent", width=12, style={"height": "100%"})
            ], className="h-50"),
            dbc.Row([
                dbc.Col(id="experiment-selectors-parent", width=12, style={"height": "100%"})
            ], className="h-50"),
        ], width=3, style={"height": "100%"}),
        dbc.Col([
            dbc.Row(id="graph-parent", className="h-75"),
            dbc.Row([
                # Predefine some elements
                html.Button(id="save-code-button", style={"display": "none"}),
                dec.PythonEditor(id="editor", style={"display": "none"}),
            ], id="tabs-parent", className="h-25"),
        ], width=9, style={"height": "100%"}),
    ], style={"height": "100%"}),
], style={"height": "100vh"}, fluid=True)

def register(app, database):
    @app.callback(
        [
            dd.Output("graph-factories-parent", "children"), dd.Output("experiment-selectors-parent", "children"), dd.Output("graph-parent", "children"),
            dd.Output("tabs-parent", "children"), dd.Output("editor-target", "data")
        ],
        [dd.Input("url", "pathname"), dd.Input("url", "search"), dd.Input("save-code-button", "n_clicks"), dd.State("editor", "value"), dd.State("editor-target", "data")]
    )
    def display(pathname, query, n_clicks, editor_code, editor_target_data):
        # Save previous editor state
        if not editor_target_data is None and not editor_code is None and any([c["prop_id"] == "save-code-button.n_clicks" for c in dash.callback_context.triggered]):
            if editor_target_data["type"] == "experiment":
                prev_editor_target = database.experiment_selectors.get_by_name(editor_target_data["name"])
            else:
                prev_editor_target = database.graph_factories.get_by_name(editor_target_data["name"])
            if not prev_editor_target is None and prev_editor_target.code != editor_code:
                prev_editor_target.code = editor_code
                # print("Updated code for " + prev_editor_target.name + " as:\n" + editor_code)
                prev_editor_target.commit()

        # Parse query
        if query.startswith("?"):
            query = query[1:]
            query = urllib.parse.parse_qs(query)
        else:
            query = {}

        experiment_selector = database.experiment_selectors.get_by_name(query["experiment"][-1] if "experiment" in query else None)
        graph_factory = database.graph_factories.get_by_name(query["graph"][-1] if "graph" in query else None)

        editor_target_type = query["edit"][0] if "edit" in query else "graph"
        editor_target_type = "experiment" if editor_target_type == "experiment" else "graph"
        editor_target = experiment_selector if editor_target_type == "experiment" else graph_factory

        # Construct new layout
        experiments_html = [html.H5("Experiments:"), dbc.ListGroup( # TODO: scrollable
            [dbc.ListGroupItem(
                name,
                active=not experiment_selector is None and experiment_selector.name == name,
                action=True,
                href=pathname + "?" + urllib.parse.urlencode({**query, "experiment": [name], "edit": "experiment"}, doseq=True),
            ) for name in database.experiment_selectors.get_all_names()]
        )]

        graph_factories_html = [html.H5("Graphs:"), dbc.ListGroup( # TODO: scrollable
            [dbc.ListGroupItem(
                name,
                active=not graph_factory is None and graph_factory.name == name,
                action=True,
                href=pathname + "?" + urllib.parse.urlencode({**query, "graph": [name], "edit": "graph"}, doseq=True),
            ) for name in database.graph_factories.get_all_names()]
        )]

        experiment_colors = None
        selected_experiments = None
        if experiment_selector is None:
            graph_html = dcc.Textarea(
                value=f"No experiment selector found",
                style={"width": "100%", "fontFamily": "'Fira code', 'Fira Mono', monospace"},
                readOnly=True,
            )
        elif graph_factory is None:
            graph_html = dcc.Textarea(
                value=f"No graph factory found",
                style={"width": "100%", "fontFamily": "'Fira code', 'Fira Mono', monospace"},
                readOnly=True,
            )
        else:
            selected_experiments, error = experiment_selector.execute(database.experiments.get_all())
            if not error is None:
                graph_html = dcc.Textarea(
                    value=f"Experiment selector caused an exception:\n{error}",
                    style={"width": "100%", "fontFamily": "'Fira code', 'Fira Mono', monospace"},
                    readOnly=True,
                )
            else:
                fig, error = graph_factory.execute(selected_experiments)
                if isinstance(fig, tuple):
                    fig, experiment_colors = fig
                if not error is None:
                    graph_html = dcc.Textarea(
                        value=f"Graph plotter caused an exception:\n{error}",
                        style={"width": "100%", "fontFamily": "'Fira code', 'Fira Mono', monospace"},
                        readOnly=True,
                    )
                else:
                    graph_html = dcc.Graph(
                        id="graph",
                        figure=fig,
                        style={"background-color": "gray", "width": "100%", "height": "100%"}
                    )



        # editor_html = dbc.Col([
        #     dbc.Row([
        #         html.H5(f"Edit {editor_target_type} {editor_target.name}:" if not editor_target is None else "Edit:"),
        #     ], style={"width": "100%"}),
        #     dbc.Row([
        #         dec.PythonEditor(
        #             value=editor_target.code if not editor_target is None else "",
        #             id="editor",
        #             style={"background-color": "white", "width": "100%"},
        #             disabled=editor_target is None,
        #         ),
        #     ], className="flex-grow-1", style={"overflow-y": "scroll"}),
        #     dbc.Row([
        #         html.Button("Save", id="save-code-button", n_clicks=0, disabled=editor_target is None)
        #     ], style={"width": "100%"}),
        # ], className="flex-column d-flex", style={"width": "100%", "height": "100%", "background-color": "yellow"})



        tab1_html = dbc.Col([
            dbc.Row([
                dec.PythonEditor(
                    value=editor_target.code if not editor_target is None else "",
                    id="editor",
                    style={"background-color": "white", "width": "100%"},
                    disabled=editor_target is None,
                ),
            ], style={"width": "100%"}),
            dbc.Row([
                html.Button("Save", id="save-code-button", n_clicks=0, disabled=editor_target is None)
            ], style={"width": "100%"}),
        ], style={"width": "100%"})

        diff_columns=[{"name": "name", "id": "name"}]
        diff_data = []
        diff_style_data_conditional = []
        same_config = ""
        if not selected_experiments is None:
            configs = [{"name": ex.name, **ex.config} for ex in selected_experiments]

            # Find all possible keys
            key_lists = set()
            def recurse(key_list, node):
                if isinstance(node, dict):
                    if not "mlog-type" in node:
                        for key, value in node.items():
                            if not (len(key_list) == 0 and key == "time"):
                                recurse(key_list + [key], value)
                elif isinstance(node, list):
                    for i, value in enumerate(node):
                        recurse(key_list + [i], value)
                else:
                    key_lists.add(tuple(key_list))
            for config in configs:
                recurse([], config)

            # Filter keys with differing values in at least two experiments
            def get(node, key_list, empty=None):
                for key in key_list:
                    if isinstance(node, dict) and isinstance(key, str) and key in node:
                        node = node[key]
                    elif isinstance(node, list) and isinstance(key, int) and 0 <= key and key < len(node):
                        node = node[key]
                    else:
                        return empty
                if isinstance(node, dict):
                    node = str(node)
                return node
            filtered_key_lists = []
            for key_list in key_lists:
                assert len(configs) > 0
                found_differing = False
                value = get(configs[0], key_list)
                for config in configs[1:]:
                    if get(config, key_list) != value:
                        found_differing = True
                        break
                if found_differing:
                    filtered_key_lists.append(key_list)
            same_key_lists = set(key_lists).difference(filtered_key_lists)
            diff_key_lists = filtered_key_lists

            # Diff keys: Convert to datatable format
            if ("name",) in diff_key_lists:
                del diff_key_lists[diff_key_lists.index(("name",))]
            diff_key_lists = sorted(diff_key_lists)
            diff_key_lists = [("name",)] + diff_key_lists
            keys = [".".join([str(k) for k in key_list]) for key_list in diff_key_lists]
            max_len = max([len(key_list) for key_list in diff_key_lists])
            def make_len(key_list):
                if len(key_list) < max_len:
                    key_list = list(key_list) + [""] * (max_len - len(key_list))
                return key_list
            key_lists_for_columns = [make_len(key_list) for key_list in diff_key_lists]
            diff_columns = [{"name": [str(k) for k in key_list] if multiple_header_rows else str(key), "id": key} for key, key_list in zip(keys, key_lists_for_columns)]
            diff_data = [{key: get(config, key_list, "") for key, key_list in zip(keys, diff_key_lists)} for config in configs]
            if not experiment_colors is None:
                diff_style_data_conditional = [
                    {
                        "if": {
                            "column_id": "name",
                            "filter_query": f"{{name}} = {ex.name}",
                        },
                        "backgroundColor": color,
                        "color": "black",
                    } for ex, color in zip(selected_experiments, experiment_colors)
                ]

            # Same keys: Convert to yaml format
            same_config = {}
            for key_list in same_key_lists:
                node = same_config
                for key in key_list[:-1]:
                    if not key in node:
                        node[key] = {}
                    node = node[key]
                node[key_list[-1]] = get(configs[0], key_list)
            same_config = yaml.dump(same_config, default_flow_style=False)
        tab2_html = dbc.Col(dash_table.DataTable(
            columns=diff_columns,
            data=diff_data,
            merge_duplicate_headers=True,
            style_data_conditional=diff_style_data_conditional,
            style_header_conditional=[{
                "backgroundColor": "rgb(230, 230, 230)",
                "color": "black"
            }],
            sort_action="native",
            sort_mode="multi",
        ))

        tab3_html = dbc.Col(html.Code(
            same_config,
            style={"width": "100%", "height": "100%", "whiteSpace": "pre-wrap", "color": "black"},
        ), style={"height": "100%"})

        tab_header_style = {"padding": "0", "height": "100%"}
        tabs_html = dbc.Col([
            dcc.Tabs([
                dcc.Tab(tab1_html, label=f"Editor: {editor_target_type} {editor_target.name}" if not editor_target is None else "Editor", style=tab_header_style, selected_style=tab_header_style),
                dcc.Tab(tab2_html, label="Parameters - Diff", style=tab_header_style, selected_style=tab_header_style),
                dcc.Tab(tab3_html, label="Parameters - Same", style=tab_header_style, selected_style=tab_header_style),
            ], style={"width": "100%", "height": "2em"}, content_style={"width": "100%", "height": "100%", "overflow-y": "scroll"}, parent_style={"width": "100%", "height": "100%"})
        ], style={"padding": "0", "width": "100%", "height": "100%"})

        editor_target_data = {"type": editor_target_type, "name": editor_target.name} if not editor_target is None else None

        return graph_factories_html, experiments_html, graph_html, tabs_html, editor_target_data
