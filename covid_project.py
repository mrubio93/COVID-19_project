# -*- coding: utf-8 -*-
"""
Spyder Editor

Created 18/12/2021

author: Manuel Rubio

Source (API): https://data.opendatasoft.com/explore/dataset/donnees-hospitalieres-covid-19-dep-france%40public/api/?disjunctive.countrycode_iso_3166_1_alpha3&disjunctive.nom_dep_min&rows=10
"""
#%% Software

# Import packages
import requests as req
import datetime
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter1d
from tabulate import tabulate

### Get the data from the website
now = datetime.datetime.now()
print("|--------------------------------------------------------------------|")
print("Hello, welcome to the COVID-19 software. Today's date is", now.strftime("%A %d %B %Y") + 
      ", it's", now.strftime("%H:%M") + ". The objective of this software is to display information on hospital data relating to the COVID-19 epidemic in France.")
print("|--------------------------------------------------------------------|")

# Ask the user for the department
dept = input("Please enter a French department: ")
url = "https://data.opendatasoft.com/api/records/1.0/search/?dataset=donnees-hospitalieres-covid-19-dep-france%40public&q=&sort=-date&rows=10000&facet=date&facet=countrycode_iso_3166_1_alpha3&facet=region_min&facet=nom_dep_min&facet=sex&refine.sex=Tous&refine.nom_dep_min=" + dept
r = req.get(url)
jdata = r.json()

while jdata["nhits"] == 0:
    dept = input('There is no department with that name, please retry:')
    url = "https://data.opendatasoft.com/api/records/1.0/search/?dataset=donnees-hospitalieres-covid-19-dep-france%40public&q=&sort=-date&rows=10000&facet=date&facet=countrycode_iso_3166_1_alpha3&facet=region_min&facet=nom_dep_min&facet=sex&refine.sex=Tous&refine.nom_dep_min=" + dept
    r = req.get(url)
    t = r.text
    jdata = r.json()

print("|--------------------------------------------------------------------|")
print('You have chosen the', dept, 'department.')

# Create a subfolder called “data” without error if it already exists.
# Save data as a JSon file on the hard disk drive, in the “data” folder that you created previously.
path_json = os.getcwd() + "/data"
if not os.path.exists(path_json):
    os.makedirs(path_json)
with open(path_json + "/jdata.json", 'w+') as fp: # use "with" to close the file after saving it
    fp.write(json.dumps(jdata))
    print("The json file was saved as jdata.json, in the following path:", os.getcwd())

df = pd.DataFrame(columns=['Date','day_hosp_new','day_intcare_new','day_out_new','day_death_new'])
l_date = []
l_hosp = []
l_intcare = []
l_out = []
l_death = []

# Put the data into a dataframe
for doc in jdata["records"]:
    d = doc["fields"]["date"]
  
    if "day_hosp_new" in doc["fields"]:
        din = doc["fields"]["day_hosp_new"]
    else:
        din = 0
    l_hosp.append(din) # store the values in a list
    l_date.append(d)

    if "day_intcare_new" in doc["fields"]:
        din = doc["fields"]["day_intcare_new"]
    else:
        din = 0
    l_intcare.append(din)

    if "day_out_new" in doc["fields"]:
        din = doc["fields"]["day_out_new"]
    else:
        din = 0
    l_out.append(din)
    
    if "day_death_new" in doc["fields"]:
        din = doc["fields"]["day_death_new"]
    else:
        din = 0
    l_death.append(din)

# transfer the values to a df
df["Date"]= l_date
df["day_intcare_new"] = l_intcare
df["day_hosp_new"] = l_hosp
df["day_out_new"] = l_out
df["day_death_new"] = l_death

# Aggregate the data by Year and Month
df['Date'] = pd.to_datetime(df['Date'])
df_grouped = df.groupby([df['Date'].dt.year.rename('Year'), df['Date'].dt.month.rename('Month')]).sum()

# correcting date columns
df_grouped = df_grouped.reset_index()
# Unify the Date column (instead of having Years and Months)
l_YM = []
for i in range(len(df_grouped)):
    d = str(df_grouped["Year"][i]) + "-" + str(df_grouped["Month"][i])
    l_YM.append(d)
df_grouped = df_grouped.drop(columns = ['Year', 'Month'])
df_grouped.insert(loc = 0, column='Date', value = l_YM)
df_grouped['Date'] = pd.to_datetime(df_grouped['Date'], format='%Y-%m')
print(tabulate(df_grouped, headers='keys', tablefmt='psql'))

# export df as csv, depending on the chosen dept 
df_grouped.to_csv(r"data/" + dept + ".csv", sep=',', encoding='utf-8', index=False)

#%% Accumulated
list_accum = []
df_accum = df_grouped.drop(columns = ['Date'])
for column in df_accum:
    accum = 0
    for row in df_accum[column]:
        accum = accum + row
        list_accum.append(accum)
    if list_accum != []:
        df_accum[column] = list_accum
        list_accum = []
df_accum.insert(loc = 0, column='Date', value = l_YM)

#%% Plots
# Using gaussian filter to make the plots smoother
# In this case, I'm refer to the column I want to label by the column value instead of the column name
x, y1, y2, y3, y4 = df_grouped["Date"], df_grouped["day_hosp_new"], df_grouped["day_intcare_new"], df_grouped["day_out_new"], df_grouped["day_death_new"]
plt.plot(x, gaussian_filter1d(y1, sigma=1), linewidth='1', color='green', label= df_grouped.columns.values[1])
plt.plot(x, gaussian_filter1d(y2, sigma=1), linewidth='1', color='blue', label=df_grouped.columns.values[2])
plt.plot(x, gaussian_filter1d(y3, sigma=1), linewidth='1', color='gray', label=df_grouped.columns.values[3])
plt.plot(x, gaussian_filter1d(y4, sigma=1), linewidth='1', color='red', label=df_grouped.columns.values[4])
plt.xticks(rotation = 45)
plt.legend()
# Export the plot as .png
plt.savefig(r"data/" + dept + '_chart.png', bbox_inches='tight')
plt.show()

# Plotting each feature per plot
plt.plot(x, gaussian_filter1d(y1, sigma=1), linewidth='1', color='green', label= df_grouped.columns.values[1])
plt.xticks(rotation = 45)
plt.title("New admissions to the hospital")
plt.savefig(r"data/" + dept + '_day_hosp_new.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y2, sigma=1), linewidth='1', color='blue', label=df_grouped.columns.values[2])
plt.xticks(rotation = 45)
plt.title("New intensive care admissions")
plt.savefig(r"data/" + dept + '_day_intcare_new.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y3, sigma=1), linewidth='1', color='gray', label=df_grouped.columns.values[3])
plt.xticks(rotation = 45)
plt.title("Amount of home returns")
plt.savefig(r"data/" + dept + '_day_out_new.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y4, sigma=1), linewidth='1', color='red', label=df_grouped.columns.values[4])
plt.xticks(rotation = 45)
plt.title("Amount of deaths")
plt.savefig(r"data/" + dept + '_day_death_new.png', bbox_inches='tight')
plt.show()

### Plots for accumulated data ###

x, y1, y2, y3, y4 = df_accum["Date"], df_accum["day_hosp_new"], df_accum["day_intcare_new"], df_accum["day_out_new"], df_accum["day_death_new"]
plt.plot(x, gaussian_filter1d(y1, sigma=1), linewidth='1', color='green', label= df_accum.columns.values[1])
plt.plot(x, gaussian_filter1d(y2, sigma=1), linewidth='1', color='blue', label=df_accum.columns.values[2])
plt.plot(x, gaussian_filter1d(y3, sigma=1), linewidth='1', color='gray', label=df_accum.columns.values[3])
plt.plot(x, gaussian_filter1d(y4, sigma=1), linewidth='1', color='red', label=df_accum.columns.values[4])
plt.xticks(rotation = 45)
plt.legend()
# Export the plot as .png
plt.savefig(r"data/" + dept + '_chart_acc.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y1, sigma=1), linewidth='1', color='green', label= df_accum.columns.values[1])
plt.xticks(rotation = 45)
plt.title("New admissions to the hospital")
plt.savefig(r"data/" + dept + '_day_hosp_new_acc.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y2, sigma=1), linewidth='1', color='blue', label=df_accum.columns.values[2])
plt.xticks(rotation = 45)
plt.title("New intensive care admissions")
plt.savefig(r"data/" + dept + '_day_intcare_new_acc.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y3, sigma=1), linewidth='1', color='gray', label=df_accum.columns.values[3])
plt.xticks(rotation = 45)
plt.title("Amount of home returns")
plt.savefig(r"data/" + dept + '_day_out_new_acc.png', bbox_inches='tight')
plt.show()

plt.plot(x, gaussian_filter1d(y4, sigma=1), linewidth='1', color='red', label=df_accum.columns.values[4])
plt.xticks(rotation = 45)
plt.title("Amount of deaths")
plt.savefig(r"data/" + dept + '_day_death_new_acc.png', bbox_inches='tight')
plt.show()

#%% HTML
# 1. Set up multiple variables to store the titles, text within the report
page_title_text='COVID report'
title_text = f'{dept} monthly cases report'
text = f'''Welcome, today is {now.strftime("%A %d %B %Y")}. <br>The objective of this software is to display information on hospital data relating to the COVID-19 epidemic in France.</br>'''

summary_text = 'Summary of graphs'
summary_text_acc = 'Summary of accumulated graphs'
tables_text = 'Table data of cases'
tables_text_acc = 'Table data of cases accumulated'
# Transform the Date column in order to show only the year and months (avoiding day and time)
df_grouped['Date'] = df_grouped['Date'].dt.to_period('M')

# 2. Combine them together using a long f-string
html = f'''
    <html>
        <head>
            <title>{page_title_text}</title>
        </head>
        <body>
            <h1>{title_text}</h1>
            <p>{text}</p>
            <h2>{summary_text}</h2>
            <img src='{dept}_chart.png' width="700">
            <img src='{dept}_day_hosp_new.png' width="700">
            <img src='{dept}_day_intcare_new.png' width="700">
            <img src='{dept}_day_out_new.png' width="700">
            <img src='{dept}_day_death_new.png' width="700">
            <h3>{summary_text_acc}</h3>
            <img src='{dept}_chart_acc.png' width="700">
            <img src='{dept}_day_hosp_new_acc.png' width="700">
            <img src='{dept}_day_intcare_new_acc.png' width="700">
            <img src='{dept}_day_out_new_acc.png' width="700">
            <img src='{dept}_day_death_new_acc.png' width="700">
              <h2>{tables_text}</h2>
            {df_grouped.to_html()}
              <h2>{tables_text_acc}</h2>
            {df_accum.to_html()}
        </body>
    </html>
    '''
# 3. Write the html string as an HTML file
with open("data/" + dept + '_html_report.html', 'w') as f:
    f.write(html)
