import pandas as pd 
import os
import time
import requests
import numpy as np

def download_data(url,filename):
    age_hours = 10
    if os.path.isfile(filename):
        # check if file is old
        st = os.stat(filename)
        age_hours = (time.time()-st.st_mtime) / 3600.
    # download new data if data is more than 2 hours old
    if age_hours > 0.1:
        myfile = requests.get(url, allow_redirects=True)
        open(filename, 'wb').write(myfile.content)

def read_data(url,filename):
    download_data(url,filename)
    df = pd.read_csv(filename)
    return df

def prep_state_death_histories():
    state_pops = pd.read_csv('nst-est2019-alldata.csv')
    postal_codes = pd.read_csv('postal_codes.csv')

    df = read_data('https://data.cdc.gov/api/views/xkkf-xrst/rows.csv?accessType=DOWNLOAD&bom=true&format=true%20target=','Excess_Deaths_Associated_with_COVID-19.csv')
    df = df[(df['Outcome']=='All causes') & (df['Type']=='Predicted (weighted)')]
    df = df.merge(postal_codes)
    df['datetime'] = pd.to_datetime(df['Week Ending Date'], format='%m/%d/%Y')
    df['year'] = pd.DatetimeIndex(df['datetime']).year
    df['days_into_year'] = 0
    df['population'] = 0
    years = df['year'].unique()
    for year in years:
        df.loc[(df['year']==year,'days_into_year')] = pd.TimedeltaIndex(df.loc[(df['year']==year,'datetime')]-pd.datetime(year,1,1)).days
        for state in df['State'].unique():
            pop_arr = state_pops.loc[(state_pops['NAME']==state),'POPESTIMATE'+str(year-1)]
            if len(pop_arr)>0:
                df.loc[(df['year']==year) & (df['State']==state),'population'] = pop_arr.values[0]

    # annoyingly, NYC is not included in NY, and is instead presented separately
    # so go and add NYC back in to NY
    for date in df['datetime'].unique():
        df.loc[(df['State']=='New York') & (df['datetime']==date),'Observed Number'] += df.loc[(df['State']=='New York City') & (df['datetime']==date),'Observed Number'].values[0]

    # convert raw weekly count into daily per 100,000 rate
    df['daily_deaths_per_hundred_thousand'] = df['Observed Number'] / 7. / df['population'] * 1e5
    df.to_csv('us_death_trends.csv', columns=['datetime','year','days_into_year','State','Code','daily_deaths_per_hundred_thousand'], index=False)

def plot_state_death_histories():
    import matplotlib.pyplot as plt

    todays_date = pd.datetime(2020,5,3)
    days_into_year = (todays_date - pd.datetime(2020,1,1)).days
    lockdown = (pd.datetime(2020,3,11) - pd.datetime(2020,1,1)).days

    df = read_csv('us_death_trends.csv')
    for state in df['State'].unique():
        plt.figure()
        for year in [2017,2018,2019,2020]:
            dff = df[(df['year']==year) & (df['State']==state)]
            sdff = dff.sort_values(by='days_into_year')
            if year == 2020:
                if (state in ['Alaska','Connecticut','Louisiana','North Carolina','Ohio','Virginia','West Virginia']):
                    trim = -5
                else:
                    trim = -2
                color='red'
            else:
                color='gray'
                trim = -1
            plt.plot(sdff['days_into_year'].values[0:trim], sdff['daily_deaths_per_hundred_thousand'].values[0:trim], '-', color=color)
            plt.suptitle(state)
            #maxy = plt.gca().get_ylim()[1]
            maxy=10
            plt.plot([days_into_year,days_into_year],[0,maxy], linewidth=0.1, color='black')
            plt.plot([lockdown,lockdown],[0,maxy], linewidth=0.1, color='black')        
            plt.xlabel('Day of the Year')
            plt.ylabel('Daily Deaths per 100,000')
            plt.ylim(0,maxy)
            plt.xlim(0,365)
        plt.savefig('states/%s.pdf' % (state.replace(' ','_')))
        plt.close()

def state_pops():
    # https://www.census.gov/data/tables/time-series/demo/popest/2010s-state-total.html#par_textimage_1574439295
    df = {}
    df['AL'] = 4903185
    df['AK'] = 731545
    df['AZ'] = 7278717
    df['AR'] = 3017804
    df['CA'] = 39512223
    df['CO'] = 5758736
    df['CT'] = 3565287
    df['DE'] = 973764
    df['DC'] = 705749
    df['FL'] = 21477737
    df['GA'] = 10617423
    df['HI'] = 1415872
    df['ID'] = 1787065
    df['IL'] = 12671821
    df['IN'] = 6732219
    df['IA'] = 3155070
    df['KS'] = 2913314
    df['KY'] = 4467673
    df['LA'] = 4648794
    df['ME'] = 1344212
    df['MD'] = 6045680
    df['MA'] = 6892503
    df['MI'] = 9986857
    df['MN'] = 5639632
    df['MS'] = 2976149
    df['MO'] = 6137428
    df['MT'] = 1068778
    df['NE'] = 1934408
    df['NV'] = 3080156
    df['NH'] = 1359711
    df['NJ'] = 8882190
    df['NM'] = 2096829
    df['NY'] = 19453561
    df['NC'] = 10488084
    df['ND'] = 762062
    df['OH'] = 11689100
    df['OK'] = 3956971
    df['OR'] = 4217737
    df['PA'] = 12801989
    df['RI'] = 1059361
    df['SC'] = 5148714
    df['SD'] = 884659
    df['TN'] = 6829174
    df['TX'] = 28995881
    df['UT'] = 3205958
    df['VT'] = 623989
    df['VA'] = 8535519
    df['WA'] = 7614893
    df['WV'] = 1792147
    df['WI'] = 5822434
    df['WY'] = 578759
    return df

def prep_us_data():
    state_df = read_data('https://covidtracking.com/api/v1/states/daily.csv','daily.csv')
    state_df['datetime'] = pd.to_datetime(state_df['date'], format='%Y%m%d')
    # state_df columns: 'date', 'state', 'positive', 'negative', 'pending',
    #    'hospitalizedCurrently', 'hospitalizedCumulative', 'inIcuCurrently',
    #    'inIcuCumulative', 'onVentilatorCurrently', 'onVentilatorCumulative',
    #    'recovered', 'hash', 'dateChecked', 'death', 'hospitalized', 'total',
    #    'totalTestResults', 'posNeg', 'fips', 'deathIncrease',
    #    'hospitalizedIncrease', 'negativeIncrease', 'positiveIncrease',
    #    'totalTestResultsIncrease'
    state_dates = state_df['datetime'].unique()
    state_pops_df = state_pops()
    state_df['population'] = np.zeros(len(state_df))
    for key,value in state_pops_df.items():
        state_df.loc[(state_df['state']==key),'population'] = value
    state_df['cumulative_deaths_per_hundred_thousand'] = state_df['death'] / state_df['population'] * 1e5
    state_df['cumulative_cases_per_hundred_thousand'] = state_df['positive'] / state_df['population'] * 1e5
    for state in state_pops_df.keys():
        state_df.loc[(state_df['state']==state),'7day_avg_deaths_per_hundred_thousand'] = state_df.loc[(state_df['state']==state),'deathIncrease'].rolling(window=7, win_type='boxcar').mean().shift(-6) / state_df['population'] * 1e5   # shift is to effectively reverse the direction of the rolling mean
        state_df.loc[(state_df['state']==state),'7day_avg_cases_per_hundred_thousand'] = state_df.loc[(state_df['state']==state),'positiveIncrease'].rolling(window=7, win_type='boxcar').mean().shift(-6) / state_df['population'] * 1e5   # shift is to effectively reverse the direction of the rolling mean
    fields = ['cumulative_deaths_per_hundred_thousand','cumulative_cases_per_hundred_thousand','7day_avg_deaths_per_hundred_thousand','7day_avg_cases_per_hundred_thousand']
    for field in fields:
        state_df['log_'+field] = np.log10(state_df[field])
        state_df[field] = state_df[field].round(2)
    #date = (max(state_dates)-start_of_2020).days
    state_df = state_df.replace([np.inf, -np.inf], np.nan)
    state_df.to_csv('us_data.csv', columns=['datetime','state','log_cumulative_deaths_per_hundred_thousand','log_cumulative_cases_per_hundred_thousand','log_7day_avg_deaths_per_hundred_thousand','log_7day_avg_cases_per_hundred_thousand','cumulative_deaths_per_hundred_thousand','cumulative_cases_per_hundred_thousand','7day_avg_deaths_per_hundred_thousand','7day_avg_cases_per_hundred_thousand'], index=False)

if __name__ == '__main__':
    prep_us_data()