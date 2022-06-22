import base64
import datetime
import io

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash import no_update
from dash import dash_table
import dash_bootstrap_components as dbc
# import dash_table
import numpy as np
import pandas as pd
from pandas import DataFrame
import plotly.express as px
import plotly.io as pio

from utils.utilities import Utilities

pio.templates.default = 'plotly_dark'

utils = Utilities()

# df = utils.load_data(fp='./data/sample.csv')
# df['Marks'] = df['Marks'].apply("{0:.3f}".format)

df: DataFrame = None
grade_intervals_df: DataFrame = None
final_df: DataFrame = None
mean_gpa: float = 0.0
grade_dist: DataFrame = None


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, './assets/main.css'])
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.config['suppress_callback_exceptions'] = True

app_header = dbc.Row(children=[
    html.Div(children=[
        html.H1(children=['PyGrader'], className='display-6 text-center'),
        html.P(children=['The application is designed to help you in assigning grades to students on relative grading mechanism'], className='text-muted text-center'),
        html.Div(children=[
            html.H5(children=['Instructions'], className='text-muted'),
            html.Ul(children=[
                html.Li(children='Please perform the steps in exact order as depicted by the numbering with buttons'),
                html.Li(children='You have to first prepare a .csv file'),
                html.Li(children=['The .csv file must only contain three columns i.e. ', html.Mark('<Reg No.>, <Name>, <Marks>')]),
            ])
        ])
    ])
], className='p-4')

app_file_upload = dbc.Row(children=[
    html.Div(children=[
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '1. Drag and Drop or ',
                html.A('Select File', className='fw-bold')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
            },
            # Don't allow multiple files to be uploaded
            multiple=False,
            accept='.csv'
        ),
        html.Div(id='output-data-upload-status'),
    ])
], className='p-4')

app_students_records_table = dbc.Row(children=[
    html.Div(children=[
        html.H5('5. Score Table', className='fw-lighter'),
        html.Hr()
    ]),
    html.Div(id='output-data-upload')
], className='p-4')

app_students_final_table = dbc.Row(children=[
    html.Div(children=[
        html.H5('6. Final Result and Grades', className='fw-lighter'),
        html.Hr()
    ]),
    html.Div(id='final-grades', style={'overflowX': 'scroll'})
], className='p-4')

app_button_group_pre = dbc.Row(dbc.ButtonGroup(
    [
        dbc.Button("2A. Show Statistics", outline=False, color="primary", disabled=True, id='show-stat-btn'),
        dbc.Button("2B. Plot Histogram", outline=False, color="secondary", disabled=True, id='plot-hist-btn'),
    ]
), className='px-4')

student_count = dbc.Row(
    [
        dbc.Col(
            dbc.Label("Student Count", html_for="student-count"),
            className='col-md-6 text-primary'
        ),
        dbc.Col(
            dbc.Input(
                type="text", id="student-count", placeholder="0", disabled=True,
                className='form-control bg-dark text-white-50'
            ),
            className='col-md-6'
        ),
    ],
    className="mt-3 mb-3",
)

student_min = dbc.Row(
    [
        dbc.Col(
            dbc.Label("Minimum Marks", html_for="student-min-marks"),
            className='col-md-6 text-primary'
        ),
        dbc.Col(
            dbc.Input(
                type="text", id="student-min-marks", placeholder="0", disabled=True,
                className='form-control bg-dark text-white-50'
            ),
            className='col-md-6'
        ),
    ],
    className="mb-3",
)

student_avg = dbc.Row(
    [
        dbc.Col(
            dbc.Label("Average Marks", html_for="student-avg-marks"),
            className='col-md-6 text-primary'
        ),
        dbc.Col(
            dbc.Input(
                type="text", id="student-avg-marks", placeholder="0", disabled=True,
                className='form-control bg-dark text-white-50'
            ),
            className='col-md-6'
        ),
    ],
    className="mb-3",
)

student_max = dbc.Row(
    [
        dbc.Col(
            dbc.Label("Maximum Marks", html_for="student-max-marks"),
            className='col-md-6 text-primary'
        ),
        dbc.Col(
            dbc.Input(
                type="text", id="student-max-marks", placeholder="0", disabled=True,
                className='form-control bg-dark text-white-50'
            ),
            className='col-md-6'
        ),
    ],
    className="mb-3",
)

student_std = dbc.Row(
    [
        dbc.Col(
            dbc.Label("Standard Deviation", html_for="std-dev"),
            className='col-md-6 text-primary'
        ),
        dbc.Col(
            dbc.Input(
                type="text", id="std-dev", placeholder="0", disabled=True,
                className='form-control bg-dark text-white-50'
            ),
            className='col-md-6'
        ),
    ],
    className="mb-3",
)

app_pre_stats_view = dbc.Row(
    children=[
        dbc.Col(id='data-hist', children=[
            dcc.Graph(id='data-hist-fig', className='px-4', figure={})
        ], className='col-md-8 col-sm-12'),
        dbc.Col(id='stats', children=[
            student_count,
            student_max,
            student_avg,
            student_min,
            student_std
        ], className='col-md-4 col-sm-12 px-5 align-self-center')
    ],
    className='my-3'
)

app_post_stats_view = dbc.Row(
    children=[
        dbc.Col(children=[
            html.H5("3. Let's do Grading"),
            html.Hr()
        ], className='col-12'),
        dbc.Col(id='select-grade-on-avg', children=[
            html.Div(
                [
                    dbc.Label("Select Grade on Average", html_for="select-goa", className='text-white-50'),
                    dcc.Dropdown(
                        id="select-goa",
                        options=[
                            {"label": "A-", "value": "A-"},
                            {"label": "B+", "value": "B+"},
                            {"label": "B", "value": "B"},
                            {"label": "B-", "value": "B-"},
                            {"label": "C+", "value": "C+"},
                        ],
                        className='text-white-50',
                        placeholder='Grade'
                    ),
                ],
                className="mb-3",
            )
        ], className='col-md-6 col-sm-12'),
        dbc.Col(id='compute-grade-intervals-btn', children=[
            dbc.Button("Apply Manual Update", outline=False, color="primary",
                       id='compute-intervals-btn'),
        ], className='col-md-6 col-sm-12 align-self-md-end mb-md-3'),
        dbc.Row(children=[
            dbc.Col(id='grade-interval-table', children=[

            ], className='col-md-12 col-sm-12 justify-content-center my-3')
        ]),

    ],
    className='my-3 px-4'
)


app_assign_grades_view = dbc.Row(
    children=[
        dbc.Col(children=[
            html.H5("4. Let's Assign Grades"),
            html.Hr()
        ], className='col-12'),
        dbc.Col(children=[
            dbc.Button("Assign Grades", outline=True, color="primary",
                       id='assign-grades-btn', disabled='disabled'),
        ], className='col-md-6 col-sm-12 mb-md-3'),
        dbc.Row(
            children=
            [
                dbc.Col(
                    dbc.Label("Mean Grade Points Average (Class)", html_for="m-gpa"),
                    className='col-md-4 text-primary align-self-center'
                ),
                dbc.Col(
                    dbc.Input(
                        type="text", id="m-gpa", placeholder="0", disabled=True,
                        className='form-control bg-dark text-white-50'
                    ),
                    className='col-md-4'
                ),
            ],
            className="justify-content-center mx-auto my-3"
        ),
        dbc.Row(children=[
            dbc.Col(id='grades-distribution-plot-container', children=[
                dcc.Graph(id='grades-hist-fig', className='mx-0', figure={})
            ], className='col-md-7 col-sm-12 mx-auto my-3'),
            dbc.Col(id='grades-distribution-table-container', children=[

            ], className='col-md-5 col-sm-12 mx-auto align-self-center my-3')
        ]),
        dbc.Row(
            children=[
                html.Div(id='final-grades-status')
            ]
        )

    ],
    className='my-3 px-4'
)

app_footer = dbc.Row(
    html.Footer(
        children=[
            html.P(
                children=[
                    'Ⓒ 2022 Muhammad Mohsin Zafar, All rights reserved'
                ],
                className='text-muted text-center fw-light'
            )
        ],
        className='p-5'
    )
)

@app.callback(
    [
        Output('grades-hist-fig', 'figure'),
        Output('grades-distribution-table-container', 'children'),
        Output('m-gpa', 'value'),
        Output('final-grades-status', 'children'),
        Output('final-grades', 'children')
    ],
    Input('assign-grades-btn', 'n_clicks'), prevent_initial_call=True
)
def on_assign_grades_btn_click(n_clicks):
    ctx = dash.callback_context
    if (ctx.triggered and ctx.triggered[0]['value'] != 0):
        if n_clicks:
            global final_df
            global mean_gpa
            global grade_dist

            final_df = utils.assign_grades(grade_intervals_df, df)
            mean_gpa, _gd = utils.compute_grade_dist_table(final_df)
            grade_dist = pd.DataFrame(_gd)

            fig = px.bar(
                grade_dist,
                x='Letter Grades',
                y='Count',
                hover_data=['Grade Points'],
                title='Grades Distribution Chart'
            )

            cols = [{"name": i, "id": i} for i in grade_dist.columns]
            grade_table = dash_table.DataTable(
                id='grade-dist-table',
                columns=cols,
                data=grade_dist.to_dict('records'),
                style_cell={'textAlign': 'left'},
                editable=False,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'border': 'none',
                    'border-bottom': '2px solid gray',
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white',
                    'border': 'none',
                    'border-bottom': '1px solid gray',
                },
                export_format='xlsx',
                export_headers='display',
            )

            fcols = [{"name": i, "id": i} for i in final_df.columns]
            final_table = dash_table.DataTable(
                id='final-table',
                columns=fcols,
                data=final_df.to_dict('records'),
                style_cell={'textAlign': 'left'},
                editable=False,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'border': 'none',
                    'border-bottom': '2px solid gray',
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white',
                    'border': 'none',
                    'border-bottom': '1px solid gray',
                },
                export_format='xlsx',
                export_headers='display',
            )

            message = html.Div([
                html.Hr(),
                html.P(['Grades computed...!', html.A('Click here to see', href='#final-grades')],
                       className='font-monospace text-muted'),
            ])

            return fig, grade_table, round(mean_gpa, 2), message, final_table
    else:
        return no_update, no_update, no_update, no_update, no_update


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)

    student_records = None
    message = None
    try:
        if 'csv' in filename:
            # Assuming that the user uploaded a CSV file
            global df
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8'))).sort_values(by=['Reg No.'])
            df['Marks'] = df['Marks'].apply("{0:.3f}".format)
            df.insert(loc=0, column='S/r.', value=np.arange(start=1, stop=len(df) + 1))

            student_records = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True,
                                                       size='sm')
            message = html.Div([
                html.Hr(),
                html.P(['File Upload Successful...! ', html.A('Click here to see', href='#output-data-upload')],
                       className='font-monospace text-muted'),
            ])
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ]), message

    return student_records, message


@app.callback([Output('output-data-upload', 'children'),
               Output('output-data-upload-status', 'children'),
               Output('show-stat-btn', 'disabled'),
               Output('plot-hist-btn', 'disabled')
               ],
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(content, name, date):
    ctx = dash.callback_context
    if (ctx.triggered and ctx.triggered[0]['value'] != 0):

        if content is not None:
            table, message = parse_contents(content, name, date)
            return [table], [message], False, False
    else:
        return no_update, no_update, True, True


def prepare_gi_table(gi_df: DataFrame):
    cols = [{"name": i, "id": i, "editable": True} if i != 'Grade'
                 else {"name": i, "id": i, "editable": False} for i in gi_df.columns
                 ]
    return dash_table.DataTable(
        id='gi-table',
        columns=cols,
        data=gi_df.to_dict('records'),
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'border': 'none',
            'border-bottom': '2px solid gray',
        },
        style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'border': 'none',
            'border-bottom': '1px solid gray',
        },
    )

@app.callback(
    [
        Output("grade-interval-table", "children"),
        Output('assign-grades-btn', 'disabled')
    ],
    [Input("select-goa", "value")]
)
def on_goa(goa_value):
    ctx = dash.callback_context
    if (ctx.triggered and ctx.triggered[0]['value'] != 0):
        if goa_value:
            grade_intervals = utils.create_grade_intervals(df, start_grade=goa_value)
            global grade_intervals_df
            grade_intervals_df = pd.DataFrame(grade_intervals)
            grade_intervals_df = grade_intervals_df.round(2)
            grade_intervals_df['Upper Bound'].iloc[0] = ""
            grade_intervals_df['Lower Bound'].iloc[-1] = ""
            # grade_intervals_table = dbc.Table.from_dataframe(grade_intervals_df, striped=True, bordered=True,
            #                                                  hover=True, dark=True, size='sm', editable=True)
            grade_intervals_table = prepare_gi_table(grade_intervals_df)
            return [grade_intervals_table, False]
    else:
        return no_update, no_update


@app.callback(
    Output('gi-table', 'data'),
    [Input('gi-table', 'data_timestamp'),
     Input('compute-intervals-btn', 'n_clicks')],
    [State('gi-table', 'data'), State('gi-table', 'active_cell')],
    prevent_initial_call=True
)
def update_columns(timestamp, n_clicks, rows, cell):
    if cell:
        updated_row = rows[cell['row']]
        updated_value = float(updated_row[cell['column_id']])

        old_row = grade_intervals_df.iloc[cell['row']]

        if old_row['Upper Bound'] != '' and old_row['Lower Bound'] != '':
            if (old_row['Upper Bound'] <= float(updated_row['Lower Bound'])) or (
                    old_row['Lower Bound'] >= float(updated_row['Upper Bound'])):
                rows[cell['row']][cell['column_id']] = old_row[cell['column_id']]
            else:
                # 1. When Lower Bound is changed
                if cell['column_id'] == 'Lower Bound':
                    if int(cell['row']) != len(rows) - 1:
                        rows[cell['row'] + 1]['Upper Bound'] = updated_value
                        grade_intervals_df.iloc[cell['row'] + 1]['Upper Bound'] = updated_value
                # 2. When Upper Bound is changed
                elif cell['column_id'] == 'Upper Bound':
                    if int(cell['row']) != 0:
                        rows[cell['row'] - 1]['Lower Bound'] = updated_value
                        grade_intervals_df.iloc[cell['row'] - 1]['Lower Bound'] = updated_value

                grade_intervals_df.iloc[cell['row']][cell['column_id']] = updated_value
        else:
            if cell['column_id'] == 'Upper Bound' and old_row['Upper Bound'] != '':
                grade_intervals_df.iloc[cell['row']][cell['column_id']] = updated_value
                rows[cell['row'] - 1]['Lower Bound'] = updated_value
                grade_intervals_df.iloc[cell['row'] - 1]['Lower Bound'] = updated_value
            elif cell['column_id'] == 'Lower Bound' and old_row['Lower Bound'] != '':
                grade_intervals_df.iloc[cell['row']][cell['column_id']] = updated_value
                rows[cell['row'] + 1]['Upper Bound'] = updated_value
                grade_intervals_df.iloc[cell['row'] + 1]['Upper Bound'] = updated_value
            else:
                rows[cell['row']][cell['column_id']] = ''

        return rows

    return no_update

@app.callback(
    [Output("student-count", "value"),
     Output("student-min-marks", "value"),
     Output("student-avg-marks", "value"),
     Output("student-max-marks", "value"),
     Output("std-dev", "value")
     ], [Input("show-stat-btn", "n_clicks")]
)
def on_show_stat_button_click(n):
    ctx = dash.callback_context
    if (ctx.triggered and ctx.triggered[0]['value'] != 0):
        if n:
            scores = pd.to_numeric(df['Marks'], downcast='float')
            scount = len(scores)
            min_marks = str(round(scores.min(), 3))
            avg_marks = str(round(scores.mean(), 3))
            max_marks = str(round(scores.max(), 3))
            std_dev = str(round(scores.std(), 3))

        return scount, min_marks, avg_marks, max_marks, std_dev
    else:
        return no_update, no_update, no_update, no_update, no_update

@app.callback(
    Output("data-hist-fig", "figure"), Input("plot-hist-btn", "n_clicks")
)
def on_plot_hist_button_click(n):
    ctx = dash.callback_context
    if (ctx.triggered and ctx.triggered[0]['value'] != 0):
        if n:
            fig = px.histogram(data_frame=df, x='Marks', nbins=20, range_x=[0, 100])
            fig.update_layout(bargap=0.2)

        return fig
    else:
        return no_update


app.layout = dbc.Container(
    children=[
        app_header,
        app_file_upload,
        app_button_group_pre,
        app_pre_stats_view,
        app_post_stats_view,
        app_assign_grades_view,
        app_students_records_table,
        app_students_final_table,
        app_footer
    ],
    fluid='sm'
)

app.run_server(debug=True)
