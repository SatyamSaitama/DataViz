import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta



# For demonstration, creating a sample loading function
def load_and_preprocess_data():
    """
    Load and preprocess the Amazon sales data
    """
    amazon_sales_data = pd.read_csv('Amazon Sale Report.csv')



    # Convert Order_Date to datetime format if it's not already
    amazon_sales_data['Order_Date'] = pd.to_datetime(amazon_sales_data['Order_Date'])

    # Create a copy of the dataframe with non-cancelled orders for most analyses
    non_cancelled_orders = amazon_sales_data[amazon_sales_data['Order_Status'] != 'Cancelled']

    # Additional preprocessing
    amazon_sales_data['Week'] = amazon_sales_data['Order_Date'].dt.isocalendar().week
    amazon_sales_data['Month'] = amazon_sales_data['Order_Date'].dt.month
    amazon_sales_data['Day'] = amazon_sales_data['Order_Date'].dt.day

    return amazon_sales_data, non_cancelled_orders

# Load and preprocess data
amazon_sales_data, non_cancelled_orders = load_and_preprocess_data()

# Initialize the Dash app with Bootstrap CSS
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for production deployment

# Define colors
colors = {
    'background': '#f9f9f9',
    'text': '#333333',
    'amazon_blue': '#232F3E',
    'amazon_orange': '#FF9900',
    'light_grey': '#EAEDED',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8'
}

# Define functions to create dashboard components

def create_kpi_cards():
    """Create KPI cards for the dashboard"""
    # Calculate KPIs
    total_orders = len(amazon_sales_data)
    total_revenue = non_cancelled_orders['Sale_Amount'].sum()
    cancelled_orders = len(amazon_sales_data[amazon_sales_data['Order_Status'] == 'Cancelled'])
    cancellation_rate = cancelled_orders / total_orders * 100 if total_orders > 0 else 0
    avg_order_value = total_revenue / len(non_cancelled_orders) if len(non_cancelled_orders) > 0 else 0

    # Create KPI cards
    kpi_cards = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Orders", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2(f"{total_orders:,}", className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Revenue", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2([
                        "₹ ", f"{total_revenue:,.2f}"
                    ], className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Cancellation Rate", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2(f"{cancellation_rate:.2f}%", className="card-text",
                           style={'color': 'green' if cancellation_rate < 10 else 'orange' if cancellation_rate < 20 else 'red'})
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Avg. Order Value", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2([
                        "₹ ", f"{avg_order_value:.2f}"
                    ], className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        )
    ])

    return kpi_cards

def create_daily_sales_chart():
    """Create daily sales trend chart"""
    daily_sales = amazon_sales_data.groupby(amazon_sales_data['Order_Date'].dt.date).agg({
        'Order_ID': 'count',
        'Sale_Amount': 'sum'
    }).reset_index()

    daily_sales['Rolling_Avg'] = daily_sales['Sale_Amount'].rolling(window=7, min_periods=1).mean()

    fig = px.line(daily_sales, x='Order_Date', y=['Sale_Amount', 'Rolling_Avg'],
                 labels={'value': 'Amount (INR)', 'Order_Date': 'Date', 'variable': 'Metric'},
                 title='Daily Sales with 7-Day Moving Average',
                 color_discrete_map={'Sale_Amount': colors['amazon_orange'], 'Rolling_Avg': colors['amazon_blue']})

    fig.update_layout(
        legend_title_text='',
        xaxis=dict(tickmode='linear', dtick='D7', tickformat='%d-%b'),
        plot_bgcolor=colors['light_grey'],
        hovermode='x unified'
    )

    return fig

def create_category_sales_chart():
    """Create product category sales chart"""
    category_sales = non_cancelled_orders.groupby('Product_Category').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    category_sales = category_sales.sort_values('Sale_Amount', ascending=False).head(10)

    fig = px.bar(category_sales, x='Product_Category', y='Sale_Amount',
                text='Sale_Amount', title='Top Product Categories by Sales',
                color='Sale_Amount', color_continuous_scale=px.colors.sequential.Bluyl)

    fig.update_traces(texttemplate='₹%{text:.2f}', textposition='outside')
    fig.update_layout(
        plot_bgcolor=colors['light_grey'],
        xaxis_title='Product Category',
        yaxis_title='Sales Amount (INR)'
    )

    return fig

def create_fulfillment_pie_chart():
    """Create fulfillment type pie chart"""
    fulfillment_data = non_cancelled_orders.groupby('Fulfillment_Type').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    fig = px.pie(fulfillment_data, values='Sale_Amount', names='Fulfillment_Type',
                title='Sales by Fulfillment Type',
                color_discrete_sequence=[colors['amazon_blue'], colors['amazon_orange']])

    fig.update_traces(textinfo='percent+label', pull=[0.05, 0])
    fig.update_layout(
        legend_title_text='Fulfillment Type'
    )

    return fig

def create_geographic_sales_map():
    """Create geographic sales map by state"""
    state_sales = non_cancelled_orders.groupby('Shipping_State').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    # For a real implementation, you would need state GeoJSON data for India
    # Here we'll create a simple bar chart instead
    fig = px.bar(state_sales.sort_values('Sale_Amount', ascending=False).head(10),
                x='Shipping_State', y='Sale_Amount',
                title='Top 10 States by Sales',
                color='Sale_Amount', color_continuous_scale=px.colors.sequential.Bluyl)

    fig.update_traces(texttemplate='₹%{y:.2f}', textposition='outside')
    fig.update_layout(
        plot_bgcolor=colors['light_grey'],
        xaxis_title='State',
        yaxis_title='Sales Amount (INR)'
    )

    return fig

def create_b2b_b2c_comparison():
    """Create B2B vs B2C comparison chart"""
    b2b_b2c = non_cancelled_orders.groupby('Business_to_Business').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    b2b_b2c['Business_Type'] = b2b_b2c['Business_to_Business'].map({True: 'B2B', False: 'B2C'})

    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]],
                        subplot_titles=['Order Count', 'Sales Amount'])

    fig.add_trace(go.Pie(labels=b2b_b2c['Business_Type'], values=b2b_b2c['Order_ID'],
                         name="Order Count", textinfo='percent+label'),
                 row=1, col=1)

    fig.add_trace(go.Pie(labels=b2b_b2c['Business_Type'], values=b2b_b2c['Sale_Amount'],
                         name="Sales Amount", textinfo='percent+label'),
                 row=1, col=2)

    fig.update_layout(
        title_text="B2B vs B2C Comparison",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="right", x=1)
    )

    return fig

def create_cancellation_analysis():
    """Create cancellation analysis chart"""
    cancel_by_category = amazon_sales_data.groupby(['Product_Category', 'Order_Status']).size().unstack(fill_value=0)

    if 'Cancelled' in cancel_by_category.columns:
        cancel_by_category['Total'] = cancel_by_category.sum(axis=1)
        cancel_by_category['Cancellation_Rate'] = cancel_by_category['Cancelled'] / cancel_by_category['Total'] * 100
        cancel_by_category = cancel_by_category.sort_values('Cancellation_Rate', ascending=False).head(10).reset_index()

        fig = px.bar(cancel_by_category, x='Product_Category', y='Cancellation_Rate',
                    title='Top 10 Categories by Cancellation Rate',
                    color='Cancellation_Rate', color_continuous_scale=px.colors.sequential.Reds)

        fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        fig.update_layout(
            plot_bgcolor=colors['light_grey'],
            xaxis_title='Product Category',
            yaxis_title='Cancellation Rate (%)'
        )
    else:
        # Create empty figure if no cancelled orders
        fig = go.Figure()
        fig.update_layout(
            title_text="No cancellation data available",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )

    return fig

def create_promo_impact_chart():
    """Create promotion impact analysis chart"""
    has_promo = non_cancelled_orders['Promotion_IDs'].notna()
    promo_impact = non_cancelled_orders.groupby(has_promo).agg({
        'Sale_Amount': ['sum', 'mean'],
        'Order_ID': 'count'
    })

    promo_impact.columns = ['Total_Sales', 'Average_Order_Value', 'Order_Count']
    promo_impact = promo_impact.reset_index()
    promo_impact['Promotion'] = promo_impact['Promotion_IDs'].map({True: 'With Promotion', False: 'No Promotion'})

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "bar"}]],
                        subplot_titles=["Total Sales by Promotion"])

    fig.add_trace(
        go.Bar(x=promo_impact['Promotion'], y=promo_impact['Total_Sales'], name='Total Sales',
              marker_color=[colors['success'], colors['warning']]),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(x=promo_impact['Promotion'], y=promo_impact['Average_Order_Value'], name='Average Order Value',
              marker_color=[colors['success'], colors['warning']]),
        row=1, col=2
    )

    fig.update_layout(
        title_text="Impact of Promotions on Sales",
        showlegend=False,
        height=400
    )

    return fig

# Define the app layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("Amazon Sales Dashboard",
                         style={'color': colors['amazon_blue'], 'textAlign': 'center', 'marginTop': '20px'}),
               width=12)
    ]),

    html.Hr(),

    # Date range filter
    dbc.Row([
        dbc.Col([
            html.Label("Date Range Filter:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=amazon_sales_data['Order_Date'].min().date(),
                max_date_allowed=amazon_sales_data['Order_Date'].max().date(),
                start_date=amazon_sales_data['Order_Date'].min().date(),
                end_date=amazon_sales_data['Order_Date'].max().date(),
                display_format='MMM DD, YYYY'
            )
        ], width=6),
        dbc.Col([
            html.Label("Filter by Category:"),
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label': cat, 'value': cat} for cat in amazon_sales_data['Product_Category'].unique()],
                value='All Categories',
                clearable=False
            )
        ], width=6)
    ], className="mb-4"),

    # KPI Cards
    html.Div(id='kpi-cards-container'),

    # Sales Trends
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='daily-sales-chart')
                ])
            ], className="mb-4")
        ], width=12)
    ]),

    # Product & Fulfillment Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='category-sales-chart')
                ])
            ], className="mb-4")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='fulfillment-pie-chart')
                ])
            ], className="mb-4")
        ], width=4)
    ]),

    # Geographic Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='geographic-sales-map')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
      # Heatmap
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='heatmap')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    # order_fig
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='order_fig')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    # B2B/B2C and Cancellation Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='b2b-b2c-comparison')
                ])
            ], className="mb-4")
        ], width=12),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='cancellation-analysis')
                ])
            ], className="mb-4")
        ], width=12)
    ]),

    # Promotion Impact
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='promo-impact-chart')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
  

    # Footer
    dbc.Row([
        dbc.Col(html.P("Amazon Sales Data Analysis Dashboard | Created with Dash and Plotly by Satyam Kumar",
                      style={'textAlign': 'center', 'color': colors['text'], 'marginTop': '20px'}),
               width=12)
    ])
], fluid=True, style={'backgroundColor': colors['background'], 'padding': '20px'})

# Define callbacks

@app.callback(
    Output('kpi-cards-container', 'children'),
    Output('daily-sales-chart', 'figure'),
    Output('category-sales-chart', 'figure'),
    Output('fulfillment-pie-chart', 'figure'),
    Output('geographic-sales-map', 'figure'),
    Output('heatmap','figure'),
    Output('order_fig','figure'),

    Output('b2b-b2c-comparison', 'figure'),
    Output('cancellation-analysis', 'figure'),
    #add heatmap
    # Output('cancellation-by_state', 'figure'),
    Output('promo-impact-chart', 'figure'),
    
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('category-dropdown', 'value')
)
def update_dashboard(start_date, end_date, selected_category):
    # Filter data by date range
    filtered_data = amazon_sales_data.copy()
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        filtered_data = filtered_data[(filtered_data['Order_Date'] >= start_date) &
                                      (filtered_data['Order_Date'] <= end_date)]

    # Filter by category if selected
    if selected_category and selected_category != 'All Categories':
        filtered_data = filtered_data[filtered_data['Product_Category'] == selected_category]

    # Filter non-cancelled orders
    filtered_non_cancelled = filtered_data[filtered_data['Order_Status'] != 'Cancelled']

    # Set the filtered data
    global amazon_sales_data_filtered, non_cancelled_orders_filtered
    amazon_sales_data_filtered = filtered_data
    non_cancelled_orders_filtered = filtered_non_cancelled

    # Generate all charts with filtered data
    # This is a simplified approach - in a real app, you would update each chart separately
    # Create KPI cards
    # Calculate KPIs
    total_orders = len(filtered_data)
    total_revenue = filtered_non_cancelled['Sale_Amount'].sum()
    cancelled_orders = len(filtered_data[filtered_data['Order_Status'] == 'Cancelled'])
    cancellation_rate = cancelled_orders / total_orders * 100 if total_orders > 0 else 0
    avg_order_value = total_revenue / len(filtered_non_cancelled) if len(filtered_non_cancelled) > 0 else 0

    # Create KPI cards
    kpi_cards = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Orders", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2(f"{total_orders:,}", className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Revenue", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2([
                        "₹ ", f"{total_revenue:,.2f}"
                    ], className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Cancellation Rate", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2(f"{cancellation_rate:.2f}%", className="card-text",
                           style={'color': 'green' if cancellation_rate < 10 else 'orange' if cancellation_rate < 20 else 'red'})
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Avg. Order Value", className="card-title", style={'color': colors['amazon_blue']}),
                    html.H2([
                        "₹ ", f"{avg_order_value:.2f}"
                    ], className="card-text")
                ])
            ], color="light", outline=True, className="mb-4 h-100"),
            width=3
        )
    ])

    # Now recreate each chart with the filtered data
    # Daily sales chart
     #Group by date and calculate daily sales and 7-day rolling average

    # Group daily and compute rolling average
    daily_sales = filtered_data.groupby(filtered_data['Order_Date'].dt.date).agg({
        'Order_ID': 'count',
        'Sale_Amount': 'sum'
    }).reset_index()

    daily_sales['Rolling_Avg'] = daily_sales['Sale_Amount'].rolling(window=7, min_periods=1).mean()

    # Chart
    daily_chart = px.line(
        daily_sales,
        x='Order_Date',
        y=['Sale_Amount', 'Rolling_Avg'],
        labels={
            'value': 'Amount (INR)',
            'Order_Date': 'Date',
            'variable': 'Metric'
        },
        title='Daily Sales with 7-Day Moving Average',
        color_discrete_map={
            'Sale_Amount': colors['amazon_orange'],
            'Rolling_Avg': colors['amazon_blue']
        }
    )

    # Update layout: hide most ticks, keep spacing clean, and allow zoom
    daily_chart.update_layout(
        legend_title_text='',
        xaxis=dict(
            tickformat='%d-%b',
            tickangle=-45,
            tickmode='array',
            tickvals=daily_sales['Order_Date'][::14],  # Show every 2 weeks
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=3, label='3m', step='month', stepmode='backward'),
                    dict(step='all')
                ])
            )
        ),
        plot_bgcolor=colors['light_grey'],
        hovermode='x unified'
    )




    # Category sales chart
    category_sales = filtered_non_cancelled.groupby('Product_Category').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    category_sales = category_sales.sort_values('Sale_Amount', ascending=False).head(10)

    category_chart = px.bar(category_sales, x='Product_Category', y='Sale_Amount',
                text='Sale_Amount', title='Top Product Categories by Sales',
                color='Sale_Amount', color_continuous_scale=px.colors.sequential.Bluyl)

    category_chart.update_traces(texttemplate='₹%{text:.2f}', textposition='outside')
    category_chart.update_layout(
        plot_bgcolor=colors['light_grey'],
        xaxis_title='Product Category',
        yaxis_title='Sales Amount (INR)'
    )

    # Fulfillment pie chart
    fulfillment_data = filtered_non_cancelled.groupby('Fulfillment_Type').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    fulfillment_chart = px.pie(fulfillment_data, values='Sale_Amount', names='Fulfillment_Type',
                title='Sales by Fulfillment Type',
                color_discrete_sequence=[colors['amazon_blue'], colors['amazon_orange']])

    fulfillment_chart.update_traces(textinfo='percent+label', pull=[0.05, 0])
    fulfillment_chart.update_layout(
        legend_title_text='Fulfillment Type'
    )

    # Geographic chart (states) using Treemap
    state_sales = filtered_non_cancelled.groupby('Shipping_State').agg({
        'Sale_Amount': 'sum',
        'Order_ID': 'count'
    }).reset_index()

    geo_chart = px.treemap(
        state_sales.sort_values('Sale_Amount', ascending=False).head(10),
        path=['Shipping_State'],
        values='Sale_Amount',
        title='Top 10 States by Sales',
        color='Sale_Amount',
        color_continuous_scale=px.colors.sequential.Bluyl
    )

    geo_chart.update_layout(
        plot_bgcolor=colors['light_grey']
    )


    # B2B vs B2C comparison
    # Grouping and aggregating data
    # b2b_b2c = (
    #     filtered_non_cancelled
    #     .groupby('Business_to_Business')
    #     .agg({
    #         'Sale_Amount': 'sum',
    #         'Order_ID': 'count'
    #     })
    #     .reset_index()
    # )

    # # Mapping boolean to business type labels
    # b2b_b2c['Business_Type'] = b2b_b2c['Business_to_Business'].map({True: 'B2B', False: 'B2C'})

    # # Create a dual pie chart layout for Order Count and Sales Amount
    # b2b_chart = make_subplots(
    #     rows=1, cols=2,
    #     specs=[[{'type': 'domain'}, {'type': 'domain'}]],
    #     subplot_titles=['Order Count', 'Sales Amount']
    # )

    # # Pie chart for Order Count
    # b2b_chart.add_trace(
    #     go.Pie(
    #         labels=b2b_b2c['Business_Type'],
    #         values=b2b_b2c['Order_ID'],
    #         name="Order Count",
    #         textinfo='percent+label'
    #     ),
    #     row=1, col=1
    # )

    # # Pie chart for Sales Amount
    # b2b_chart.add_trace(
    #     go.Pie(
    #         labels=b2b_b2c['Business_Type'],
    #         values=b2b_b2c['Sale_Amount'],
    #         name="Sales Amount",
    #         textinfo='percent+label'
    #     ),
    #     row=1, col=2
    # )

    # # Layout customization
    # b2b_chart.update_layout(
    #     title_text="B2B vs B2C Comparison",
    #     height=450,
    #     legend=dict(
    #         orientation="h",
    #         yanchor="bottom",
    #         y=0,
    #         xanchor="right",
    #         x=1
    #     )
    # )

    # Cancellation analysis
    # Group data by category and order status, then reshape into a wide format
    cancel_by_category = filtered_data.groupby(['Product_Category', 'Order_Status']) \
                                      .size() \
                                      .unstack(fill_value=0)

    if 'Cancelled' in cancel_by_category.columns:
        # Calculate total orders
        cancel_by_category['Total_Orders'] = cancel_by_category.sum(axis=1)

        # Calculate not cancelled orders
        cancel_by_category['Not_Cancelled'] = cancel_by_category['Total_Orders'] - cancel_by_category['Cancelled']

        # Compute cancellation % for label
        cancel_by_category['Cancelled_%'] = (
            cancel_by_category['Cancelled'] / cancel_by_category['Total_Orders'] * 100
        ).round(2).astype(str) + '%'

        # Reset index and prep data
        plot_data = cancel_by_category[['Cancelled', 'Not_Cancelled', 'Cancelled_%', 'Total_Orders']].reset_index()

        # Create "label" column: % for Cancelled, empty for Not_Cancelled
        plot_data['Cancelled_Label'] = plot_data['Cancelled_%']
        plot_data['Not_Cancelled_Label'] = ''

        # Melt count values
        count_data = plot_data.melt(
            id_vars=['Product_Category', 'Total_Orders'],
            value_vars=['Cancelled', 'Not_Cancelled'],
            var_name='Status',
            value_name='Count'
        )

        # Melt labels
        label_data = plot_data.melt(
            id_vars='Product_Category',
            value_vars=['Cancelled_Label', 'Not_Cancelled_Label'],
            var_name='Status',
            value_name='Label'
        )

        # Clean status names to match
        label_data['Status'] = label_data['Status'].str.replace('_Label', '')

        # Merge counts and labels
        final_data = count_data.merge(label_data, on=['Product_Category', 'Status'])

        # Sort by total orders
        final_data = final_data.sort_values(by='Total_Orders', ascending=False)

        # Plot
        cancel_chart = px.bar(
            final_data,
            y='Product_Category',
            x='Count',
            color='Status',
            orientation='h',
            title='Cancelled vs Not Cancelled Orders by Category (Volume)',
            text='Label',
            color_discrete_map={
                'Cancelled': 'red',
                #light green
                'Not_Cancelled': 'lightgreen'
            }
        )

        cancel_chart.update_layout(
            xaxis_title='Number of Orders',
            yaxis_title='Product Category',
            barmode='stack',
            plot_bgcolor=colors.get('light_grey', '#f4f4f4')
        )

    else:
        # No cancellations found, show placeholder chart
        cancel_chart = go.Figure()
        cancel_chart.update_layout(
            title_text="No cancellation data available",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )




    cancelled_orders_df = amazon_sales_data[amazon_sales_data['Order_Status'] == 'Cancelled'].copy()

    # 2. Group by state and count cancellations
    cancellations_by_state = cancelled_orders_df.groupby('Shipping_State').size().reset_index(name='Cancellation_Count')

    # 3. Sort states by cancellation count in descending order
    cancellations_by_state = cancellations_by_state.sort_values('Cancellation_Count', ascending=False)

# 1. Calculate total cancellations
    total_cancellations = cancellations_by_state['Cancellation_Count'].sum()

    # 2. Add percentage column
    cancellations_by_state['Cancellation_Percent'] = (
        cancellations_by_state['Cancellation_Count'] / total_cancellations * 100
    ).round(2)

    # 3. Top N states
    top_n = 10
    top_cancellations = cancellations_by_state.head(top_n)

    # 4. Create a custom hover text
    top_cancellations['Hover_Text'] = top_cancellations.apply(
        lambda row: f"{row['Shipping_State']}<br>Count: {row['Cancellation_Count']}<br>Percent: {row['Cancellation_Percent']}%", axis=1
    )

    # 5. Bubble chart
    fig_cancellations_bubble = px.scatter(
        top_cancellations,
        x='Shipping_State',
        y='Cancellation_Count',
        size='Cancellation_Count',
        color='Cancellation_Count',
        hover_name='Shipping_State',
        hover_data={'Shipping_State': False, 'Cancellation_Count': False, 'Cancellation_Percent': False, 'Hover_Text': True},
        text=top_cancellations['Cancellation_Percent'].astype(str) + '%',
        size_max=80,
        color_continuous_scale=px.colors.sequential.Reds,
        title=f'Top {top_n} States by Order Cancellation (Bubble Chart with %)'
    )
    fig_cancellations_bubble.update_traces(
    textposition='middle center',
    marker=dict(line=dict(width=2, color='white'))
)

    # fig_cancellations_bubble.update_traces(textposition='top center', hovertemplate=top_cancellations['Hover_Text'])

    fig_cancellations_bubble.update_layout(
        xaxis_title='Shipping State',
        yaxis_title='Number of Cancellations',
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='#f9f9f9',
        showlegend=False
    )
    b2b_chart = fig_cancellations_bubble
    # 1. Group by State and Category and count the number of orders
    state_category_orders = non_cancelled_orders.groupby(['Shipping_State', 'Product_Category']).size().reset_index(name='Order_Count')

    # Optional: Filter for Top N States by total orders if the chart becomes too crowded
    # Calculate total orders per state
    total_orders_per_state = non_cancelled_orders.groupby('Shipping_State').size().reset_index(name='Total_State_Orders')
    # Sort states by total orders
    top_states = total_orders_per_state.sort_values('Total_State_Orders', ascending=False)
    # Select Top N (e.g., Top 15)
    N = 15
    top_n_states_list = top_states.head(N)['Shipping_State'].tolist()
    # Filter the main aggregation to include only these top states
    state_category_orders_filtered = state_category_orders[state_category_orders['Shipping_State'].isin(top_n_states_list)]


    # --- Visualization 1: Heatmap ---

    # Pivot the data for the heatmap: States as rows, Categories as columns, Order_Count as values
    heatmap_data = state_category_orders_filtered.pivot(
        index='Shipping_State',
        columns='Product_Category',
        values='Order_Count'
    ).fillna(0) # Fill missing state-category combinations with 0 orders

    # Create the heatmap
    fig_heatmap = px.imshow(
        heatmap_data,
        text_auto=True, # Display the counts on the heatmap cells
        aspect="auto",   # Adjust aspect ratio if needed
        color_continuous_scale=px.colors.sequential.Blues, # Choose a color scale
        title=f'Heatmap of Order Counts: Product Category vs. Shipping State (Top {N} States)'
    )

    fig_heatmap.update_layout(
        xaxis_title="Product Category",
        yaxis_title="Shipping State",
        xaxis={'side': 'top'}, # Move category labels to the top if preferred
        yaxis_tickangle=0,
        xaxis_tickangle=45,
        margin=dict(l=40, r=40, t=80, b=40) # Adjust margins if labels overlap
    )
    fig_heatmap.update_traces(hovertemplate="State: %{y}<br>Category: %{x}<br>Orders: %{z}<extra></extra>")



    # --- Visualization 2: Stacked Bar Chart ---

    # Sort the filtered data by state based on the total order count for consistent bar ordering
    state_category_orders_filtered['Shipping_State'] = pd.Categorical(
        state_category_orders_filtered['Shipping_State'],
        categories=top_n_states_list,
        ordered=True
    )
    state_category_orders_filtered = state_category_orders_filtered.sort_values('Shipping_State')

    # Create the stacked bar chart
    fig_stacked_bar = px.bar(
        state_category_orders_filtered,
        x='Shipping_State',
        y='Order_Count',
        color='Product_Category',
        title=f'Stacked Bar Chart of Orders by Category per State (Top {N} States)',
        labels={'Order_Count': 'Number of Orders', 'Shipping_State': 'Shipping State', 'Product_Category': 'Product Category'},
        # Optional: Specify color sequence if needed: color_discrete_sequence=px.colors.qualitative.Plotly
    )

    fig_stacked_bar.update_layout(
        xaxis_tickangle=-45,
        yaxis_title="Total Number of Orders",
        xaxis_title="Shipping State",
        legend_title="Product Category",
        barmode='stack' # Explicitly set barmode to stack
    )
    fig_stacked_bar.update_traces(hovertemplate="State: %{x}<br>Category: %{fullData.name}<br>Orders: %{y}<extra></extra>")
    # Promotion impact analysis
    has_promo = filtered_non_cancelled['Promotion_IDs'].notna()

    # Aggregate promo impact
    promo_impact = filtered_non_cancelled.groupby(has_promo).agg({
        'Sale_Amount': ['sum', 'mean'],
        'Order_ID': 'count'
    })
    promo_impact.columns = ['Total_Sales', 'Average_Order_Value', 'Order_Count']
    promo_impact = promo_impact.reset_index()
    promo_impact['Promotion'] = promo_impact[has_promo.name].map({True: 'With Promotion', False: 'No Promotion'})

    # Create subplots: 1 row, 2 columns (Bar + Pie)
    promo_chart = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "bar"}, {"type": "domain"}]],
        subplot_titles=["Total Sales by Promotion", "Order Distribution"]
    )

    # Bar chart: Total Sales
    promo_chart.add_trace(
        go.Bar(
            x=promo_impact['Promotion'],
            y=promo_impact['Total_Sales'],
            name='Total Sales',
            marker_color=['#2ca02c', '#ff7f0e']  # success and warning colors
        ),
        row=1, col=1
    )

    # Pie chart: Order Distribution
    promo_chart.add_trace(
        go.Pie(
            labels=promo_impact['Promotion'],
            values=promo_impact['Order_Count'],
            name="Order Distribution",
            marker=dict(colors=['#2ca02c', '#ff7f0e'])  # match bar colors
        ),
        row=1, col=2
    )

    # Layout updates
    promo_chart.update_layout(
        title_text="Impact of Promotions on Sales",
        showlegend=True,
        height=500
    )
    

    # Ensure 'Order_Date' is in datetime format
    amazon_sales_data['Order_Date'] = pd.to_datetime(amazon_sales_data['Order_Date'])

    # Extract month name from the Order_Date
    amazon_sales_data['Month_Name'] = amazon_sales_data['Order_Date'].dt.strftime('%B')

    # Identify top 2 categories based on total order count
    top_categories = amazon_sales_data['Product_Category'].value_counts().nlargest(2).index

    # Filter data for only the top 2 categories
    filtered_data = amazon_sales_data[amazon_sales_data['Product_Category'].isin(top_categories)]

    # Group by Month Name and Product Category, then count the number of orders
    monthly_category_sales = filtered_data.groupby(['Month_Name', 'Product_Category']).size().reset_index(name='Order_Count')

    # Order the months chronologically

    # Sort Month_Name if it's a string (e.g., 'January', 'February', etc.)
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    monthly_category_sales['Month_Name'] = pd.Categorical(monthly_category_sales['Month_Name'], categories=month_order, ordered=True)
    monthly_category_sales = monthly_category_sales.sort_values('Month_Name')

    # Initialize a figure
    order_fig = go.Figure()

    # Add a bar trace for each Product Category
    for category in monthly_category_sales['Product_Category'].unique():
        df_cat = monthly_category_sales[monthly_category_sales['Product_Category'] == category]
        order_fig.add_trace(go.Bar(
            x=df_cat['Month_Name'],
            y=df_cat['Order_Count'],
            name=category
        ))

    # Update layout
    order_fig.update_layout(
        barmode='group',
        title='Number of Orders for Top 2 Product Categories per Month',
        xaxis_title='Month',
        yaxis_title='Number of Orders',
        xaxis=dict(type='category')
    )



    return kpi_cards, daily_chart, category_chart, fulfillment_chart, geo_chart,fig_stacked_bar,order_fig, b2b_chart, cancel_chart, promo_chart

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
