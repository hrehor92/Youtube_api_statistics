import numpy as np
from googleapiclient.discovery import build
import pandas as pd
import isodate
from datetime import datetime
import dash_bootstrap_components as dbc
import plotly.express as px
import pycountry
from dash import Dash, html, dcc, callback, Output, Input
import calendar

channel_name = input('Please write your favorite Youtube channel')
api_key = '' #write your api key

api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(api_service_name, api_version, developerKey=api_key)
def get_channel_id(channel_name):
    # Call the search.list method to retrieve the channel ID
    request = youtube.search().list(
        part='id',
        q=channel_name,
        type='channel',
        maxResults=1)
    response = request.execute()
    # Extract the channel ID from the response
    if 'items' in response and len(response['items']) > 0:
        channel_id = response['items'][0]['id']['channelId']
        return channel_id
    else:
        return None

channel_id = get_channel_id(channel_name)

def request_info_channel(channel_id, youtube):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id)
    response = request.execute()
    return response


response = request_info_channel(channel_id, youtube)
# for bettter visualization
# print(json.dumps(response, indent=4))
def get_statistics(response):
    data = {'ChannelName':  response['items'][0]['snippet']['title'],
            'Description': response['items'][0]['snippet']['description'],
            'DateCreated': response['items'][0]['snippet']['publishedAt'],
            'PlaylistID': response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
            'Pic': response['items'][0]['snippet']['thumbnails']['high']['url'],
            'Country': response['items'][0]['snippet']['country'],
            'Views': response['items'][0]['statistics']['viewCount'],
            'Subscribers': response['items'][0]['statistics']['subscriberCount'],
            'videoCount': response['items'][0]['statistics']['videoCount']}
    return data


info_data = get_statistics(response)

def get_video_IDs(info_data, youtube):
    video_ids = []
    request_videos = youtube.playlistItems().list(
            part="snippet, ContentDetails",
            playlistId=info_data['PlaylistID'],
            maxResults=50)
    response_videos = request_videos.execute()
    for video in response_videos['items']:
        video_ids.append(video['contentDetails']['videoId'])

    next_page_token = response_videos.get('nextPageToken')
    while next_page_token is not None:
        request_videos = youtube.playlistItems().list(
            part="snippet, ContentDetails",
            playlistId=info_data['PlaylistID'],
            pageToken=next_page_token,
            maxResults=50)
        response_videos = request_videos.execute()
        for video in response_videos['items']:
            video_ids.append(video['contentDetails']['videoId'])
        next_page_token = response_videos.get('nextPageToken')
    return video_ids


video_ids = get_video_IDs(info_data, youtube)
# for better visualization of data
# print(json.dumps(videos, indent=4))

def get_video_details(video_ids, youtube):
    all_stat_video = []
    for i in range(0, len(video_ids), 50):
        request_videos_info = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50]))
        response = request_videos_info.execute()
        for video in response['items']:
            stat_video = {'id': video['id'],
                        'title': video['snippet']['title'],
                        'date': datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d-%m-%Y'),
                        'date_day': int(datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d')),
                        'date_month': calendar.month_name[int(datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%m'))],
                        'date_year': datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y'),
                        'description': video['snippet']['description'],
                        'duration_total': isodate.parse_duration(video['contentDetails']['duration']),
                        'duration_minutes': isodate.parse_duration(video['contentDetails']['duration']).total_seconds() // 60,
                        'duration_seconds': isodate.parse_duration(video['contentDetails']['duration']).total_seconds(),
                        'definition': video['contentDetails']['definition'],
                        'caption': bool(video['contentDetails']['caption']),
                        }
            try:
                stat_video['Views'] = int(video['statistics']['viewCount'])
            except:
                stat_video['Views'] = 0
            try:
                stat_video['Likes'] = int(video['statistics']['likeCount'])
            except:
                stat_video['Likes'] = np.nan
            try:
                stat_video['Comments'] = int(video['statistics']['commentCount'])
            except:
                stat_video['Comments'] = np.nan
            all_stat_video.append(stat_video)

    return all_stat_video

all_stat_videos = get_video_details(video_ids, youtube)
all_stat_video_df = pd.DataFrame(all_stat_videos)

#min and max revenue per video
all_stat_video_df['min_revenue'] = all_stat_video_df['Views'] * 0.01
all_stat_video_df['max_revenue'] = all_stat_video_df['Views'] * 0.03

#top 3 viewed videos
top3_views = sorted(all_stat_video_df['Views'].tolist(), reverse=True)[:3]
top_1_views = all_stat_video_df[all_stat_video_df['Views'] == top3_views[0]]
top_2_views = all_stat_video_df[all_stat_video_df['Views'] == top3_views[1]]
top_3_views = all_stat_video_df[all_stat_video_df['Views'] == top3_views[2]]

#top 3 viewed videos
top3_comment = sorted(all_stat_video_df['Comments'].tolist(), reverse=True)[:3]
top_1_comment = all_stat_video_df[all_stat_video_df['Comments'] == top3_comment[0]]
top_2_likes = all_stat_video_df[all_stat_video_df['Comments'] == top3_comment[1]]
top_3_likes = all_stat_video_df[all_stat_video_df['Comments'] == top3_comment[2]]

#country name
country = pycountry.countries.get(alpha_2=info_data['Country'])

#group by month and year for analysis
months = ['All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
month_days = {
    'January': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    'February': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    'March': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    'April': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    'Mai': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    'June': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    'July': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    'August': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    'September': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    'October': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    'November': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    'December': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
}
cat_type = pd.CategoricalDtype(categories=months[1:], ordered=True)
group_by_month = all_stat_video_df.groupby(['date_year', 'date_month']).agg({'id': 'count', 'min_revenue': 'sum', 'max_revenue': 'sum', 'Likes': 'sum', 'Views': 'sum'}).reset_index()
group_by_year = all_stat_video_df.groupby('date_year').agg({'id': 'count', 'min_revenue': 'sum', 'max_revenue': 'sum', 'Likes': 'sum', 'Views': 'sum'}).reset_index()

group_by_month['date_month'] = group_by_month['date_month'].astype(cat_type)
group_by_month = group_by_month.sort_values(['date_month', 'date_year'])
group_by_year = group_by_year.sort_values('date_year')
# initialize app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
color_discrete_sequence = ['#0a9396','#94d2bd','#e9d8a6','#ee9b00', '#ca6702', '#bb3e03', '#ae2012']

controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label('X variable'),
                dcc.Dropdown(
                    id='x-month',
                    options=[
                        {'label': month, 'value': month} for month in months
                    ],
                    value=months[datetime.now().month - 2] #show alwayas the current month
                ),
                dcc.Dropdown(
                    id='x-year',
                    options=[
                        {'label': year, 'value': year} for year in group_by_year['date_year'].tolist()
                    ],
                    value=datetime.now().year
                )
            ]
        ),
        html.Div(
            [
                dbc.Label('Y variable'),
                dcc.Dropdown(
                    id='y-variable',
                    options=[
                        {"label": param, "value": param} for param in ['Views', 'Likes', 'Profit']
                    ],
                    value='Views'
                )
            ]
        )
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.H1(children=f'{info_data['ChannelName']} | Youtube statistics', style={'textAlign':'left', 'padding-left': '20px'}),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.CardImg(
                                        src=info_data['Pic'],
                                        className='img-fluid rounded-start'
                                    ),
                                    className='col-md-4',
                                ),
                                dbc.Col(
                                    dbc.CardBody([html.H4('Total subs'),
                                          html.H6(info_data['Subscribers']),
                                          html.H4('Total videos'),
                                          html.H6(len(all_stat_video_df['id'].unique())),
                                          html.H4('Country'),
                                          html.H6(country.name + country.flag)])
                                )
                            ]
                        )
                    )
                ),
                dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [html.H4('Top 3 viewed videos'),
                                dbc.ListGroup(
                                    [dbc.ListGroupItem(dbc.CardLink(top_1_views['title'], href=f'https://www.youtube.com/watch?v={top_1_views['id'].values[0]}')),
                                            dbc.ListGroupItem(dbc.CardLink(top_2_views['title'], href=f'https://www.youtube.com/watch?v={top_2_views['id'].values[0]}')),
                                            dbc.ListGroupItem(dbc.CardLink(top_3_views['title'], href=f'https://www.youtube.com/watch?v={top_3_views['id'].values[0]}')),
                                            ],
                                    flush=True,)
                                ]
                            )
                        )),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [html.H4('Top 3 commented videos'),
                             dbc.ListGroup(
                                 [dbc.ListGroupItem(dbc.CardLink(top_1_comment['title'], href=f'https://www.youtube.com/watch?v={top_1_comment['id'].values[0]}')),
                                  dbc.ListGroupItem(dbc.CardLink(top_2_likes['title'], href=f'https://www.youtube.com/watch?v={top_2_likes['id'].values[0]}')),
                                  dbc.ListGroupItem(dbc.CardLink(top_3_likes['title'],href=f'https://www.youtube.com/watch?v={top_3_likes['id'].values[0]}')),
                                  ],
                                 flush=True, )
                             ]
                        )
                    )),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(controls, width=2),
                dbc.Col(dcc.Graph(id='chart'))
            ],
            align='center'
        ),
        dbc.Row(
            [
                html.H6('The Profit calculation is based on the assumption that a video view is paid by youtube between 0.01$ and 0.03$. However, this information is an approximation and should not taken as real.'),
                html.A('Info', href='https://www.qqtube.com/article/how-much-does-youtube-pay-for-100k-views#:~:text=YouTube%20pays%20%240.01%20to%20%240.03,video%2C%20and%20several%20other%20variables.')
            ], id='disclaimer'
        )
    ],
    fluid=True,
)

@app.callback(
    Output("chart", "figure"),
    [
        Input("x-year", "value"),
        Input("x-month", "value"),
        Input("y-variable", "value")
    ],
)
def make_graph(x_year, x_month, y_variable):
    y_axis = y_variable if y_variable != 'Profit' else ['min_revenue', 'max_revenue']
    bar_mode = 'relative' if y_variable != 'Profit' else 'group'
    if x_month == 'All':
        df = group_by_month[(group_by_month['date_year'] == str(x_year))]
        if df['date_month'].tolist() == months[1:]:
            fig = px.bar(df, x=months[1:], y=y_axis, barmode=bar_mode)
        else:
            missing_months = set(months[1:]) - set(df['date_month'].tolist())
            for month in list(missing_months):
                to_append = {
                    'date_year': str(x_year),
                    'date_month': month,
                    'id': 0,
                    'min_revenue': 0,
                    'max_revenue': 0,
                    'Likes': 0,
                    'Views': 0}
                df = df._append(to_append, ignore_index=True)
            df['date_month'] = df['date_month'].astype(cat_type)
            df = df.sort_values(['date_month'])
            fig = px.bar(df, x=months[1:], y=y_axis, barmode=bar_mode)
        fig.update_xaxes(title_text='Months')
        fig.update_layout(title_text=f'Total {y_variable} for {x_year}')
    else:
        df_temp = all_stat_video_df[(all_stat_video_df['date_year'] == str(x_year)) & (all_stat_video_df['date_month'] == str(x_month))]
        df = df_temp.groupby(['date_day']).agg({'id': 'count', 'min_revenue': 'sum', 'max_revenue': 'sum', 'Likes': 'sum', 'Views': 'sum'}).reset_index()
        if df['date_day'].tolist() == month_days[x_month]:
            fig = px.bar(df, x=month_days[x_month], y=y_axis, barmode=bar_mode)
        else:
            missing_days = set(month_days[x_month]) - set(df['date_day'].tolist())
            for day in list(missing_days):
                to_append = {
                    'id': '',
                    'title': '',
                    'date': '',
                    'date_day': day,
                    'date_month': x_month,
                    'date_year': x_year,
                    'description': '',
                    'duration_total': 0,
                    'duration_minutes': 0,
                    'duration_seconds': 0,
                    'definition': '',
                    'caption': True,
                    'Views': 0,
                    'Likes': 0,
                    'Comments': 0,
                    'min_revenue': 0,
                    'max_revenue': 0}
                df = df._append(to_append, ignore_index=True)
            df = df.sort_values(['date_day'])
            fig = px.bar(df, x=month_days[x_month], y=y_axis, barmode=bar_mode)
        fig.update_xaxes(tickvals=df['date_day'], ticktext=[str(day) for day in df['date_day']], title_text='Days')
        fig.update_yaxes(title_text=y_variable)
        fig.update_layout(title_text=f'Total {y_variable} for {x_month}')
    return fig

@app.callback(
    Output('disclaimer', 'style'),
    [Input('y-variable', 'value')]
)
def visibility_disclaimer(selected_dropdown):
    if selected_dropdown == "Profit":
        return {'display': 'block'}
    else:
        return {'display': 'none'}


if __name__ == '__main__':
    app.run(debug=False)
