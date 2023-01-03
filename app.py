#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 16:16:45 2022

@author: ondrejsvoboda
"""

import streamlit as st
import pandas as pd
from keboola_storage_api.connection import add_keboola_table_selection
import keboola_api as kb
#import streamlit_keboola_api.src.keboola_api as kb
import os
from io import StringIO


#st.write("ahoj K7!")

st.sidebar.markdown("# Connect to Keboola")

@st.experimental_memo(ttl=7200)
def read_df(table_id, index_col=None, date_col=None):
    client.tables.export_to_file(table_id, '.')
    table_name = table_id.split(".")[-1]
    return pd.read_csv(table_name, index_col=index_col, parse_dates=date_col)

add_keboola_table_selection()

def saveFile(uploaded):
    with open(os.path.join(os.getcwd(),uploaded.name),"w") as f:
        strIo= StringIO(uploaded.getvalue().decode("utf-8"))
        f.write(strIo.read())
        return os.path.join(os.getcwd(),uploaded.name)

if "kbc_storage_client" in st.session_state:

    st.markdown("# Wine")
    st.sidebar.markdown("# Filter Customers")
    client = st.session_state["kbc_storage_client"]
    df_customers = read_df('in.c-wine.customers')
    df_orders = read_df('in.c-wine.wine_orders', date_col=["order_date"])
    
    col1, col2, col3 = st.columns(3)
    
    customers, orders = st.tabs(["Customers", "Orders"])
    
    with st.sidebar:
        n_past_purchases_low, n_past_purchases_high = st.slider(
                'Number of past purchases',
                1, int(df_customers.n_purchases.max()), (1, int(df_customers.n_purchases.max())))
    
        st.sidebar.markdown("Number of periods since last puchase:")
        st.sidebar.markdown("* 0 - New purchase")
        st.sidebar.markdown("* 1 - About time to repurchase")
        st.sidebar.markdown("* X >> 1 - High time to make a new purchase")
        n_past_periods = st.slider("", 0, 3, 1)
    
        consumer_basket_low, consumer_basket_high = st.slider(
                'Average consumer basket',
                0, int(df_customers.average_order.max()), (0, int(df_customers.average_order.max())))
    
    filter_customers_purchases = (df_customers.n_purchases>=n_past_purchases_low) & (df_customers.n_purchases<=n_past_purchases_high)
    filter_customers_consumer_basket = (df_customers.average_order>=consumer_basket_low) & (df_customers.average_order<=consumer_basket_high)
    filter_customers =  filter_customers_purchases & filter_customers_consumer_basket & (df_customers.ratio_since_last_order>n_past_periods)
    
    df_customers_filtered = df_customers.loc[filter_customers]
    df_orders_filtered = df_orders.loc[df_orders.customer_id.isin(df_customers_filtered.index)]
    
    #fl=st.file_uploader("Drop a csv...",type="csv")    
    #if hasattr(fl,'name'):
        # Streamlit uploader doesn't save the file to disk, only in mem. 
        # We need to save the file to disk to send it to Keboola python client
        #fpath=saveFile(fl)
    df_customers_filtered.to_csv("test.csv", index=False)
    #with st.expander("Keboola Upload files"):    
#     value = kb.keboola_upload(
# #        keboola_URL="https://connection.north-europe.azure.keboola.com",
#         keboola_URL=client.root_url,
# #        keboola_key='10708-41858-5CjFxQGRk8zqw8ahFoUe4nEUVvMIcMMr0f1zuvRf',
#         keboola_key=client._token,

#         keboola_table_name="test-ondra",
#         keboola_bucket_id="out.c-streamlit_out",
#         keboola_file_path="test.csv",
#         keboola_primary_key=['customer_id'],
#         # Button Label
#         label="SEND TO KEBOOLA",
#         # Key is mandatory and has to be unique
#         key="two",
#         # if api_only= True than the button is not shown and the api call is fired directly
#         api_only=False
#     )
    
    value = kb.keboola_create_update(keboola_URL=client.root_url, 
                                keboola_key=client._token, 
                                keboola_table_name="selected_customers", 
                                keboola_bucket_id="out.c-streamlit_out", 
                                keboola_file_path="test.csv", 
                                keboola_primary_key=['customer_id'],
                                #Button Label
                                label="SEND TO KEBOOLA",
                                # Key is mandatory and has to be unique
                                key="two",
                                # if api_only= True than the button is not shown and the api call is fired directly
                                api_only=False
                                )
    value

    
    
    col1.metric("# Customers", df_customers_filtered.shape[0])
    col2.metric("Average Consumer Basket", f"{df_customers_filtered.average_order.mean():.2f}$")
    col3.metric("Average Number of Purchases", f"{df_customers_filtered.n_purchases.mean():.2f}")
    
    
    with customers:
        st.dataframe(df_customers_filtered)
    
    with orders:
        st.dataframe(df_orders_filtered)
        
        
