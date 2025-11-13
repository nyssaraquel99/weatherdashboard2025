# -*- coding: utf-8 -*-
"""
Created on Thu Sep 18 21:50:58 2025

@author: nyssa
"""

import requests
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as ticker


#api key
key="" #insert personal key

def format_time(epoch,tz):
    """
    convert epoch time (unix) to date time, adjusted for time zone
    """
    epoch+=tz
    formatted_time=time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(epoch))
    return formatted_time
    
def k_to_f(kelvin):
    """
    convert kelvin to fahrenheit
    """
    fahrenheit=round(1.8*(kelvin-273.15)+32)
    return fahrenheit

def mps_to_mph(mps):
    """
    convert speed from meters per second to miles per hour
    """
    mph=round(mps/0.44704)
    return mph

def deg_to_compass(degrees):
    """
    convert degrees to cardinal direction
    """
    sector={
        1:"N",
        2:"NNE",
        3:"NE",
        4:"ENE",
        5:"E",
        6:"ESE",
        7:"SE",
        8:"SSE",
        9:"S",
        10:"SSW",
        11:"SW",
        12:"WSW",
        13:"W",
        14:"WNW",
        15:"NW",
        16:"NNW",
        17:"N"
        }
    #limit direction to 360
    if degrees>360:
        degrees%=360
    #calculate sector index
    index=round(degrees/22.5)+1
    return sector[index]
    
def get_stacks(bins,target):
    """
    bins is a list containing values to split target into list for a stacked bar plot.
    to include remainder in final stacks list, last value of bins should be 0
    """
    target0=target
    stacks=[]
    for i in range(len(bins)):
        if (i==0 and bins[i]>=target):
            stacks.append(target)
            break
        elif i==(len(bins)-1) and target0<=sum(bins):
            stacks.append(target)
        elif bins[i]==0:
            stacks.append(target)
        elif bins[i]<=target:
            stacks.append(bins[i])
            target-=bins[i]
    return stacks

def get_day(epoch,tz):
    """
    Using numpy datetime64 object to extract day data
    """
    epoch+=tz
    day=time.strftime("%d",time.gmtime(epoch))
    return day

def current_weather(key,loc):
    """
    generate current weather stats for given location. returns dictionary
    """
    #declare request variables
    base_url="http://api.openweathermap.org/data/2.5/weather"
    url=base_url+"?q="+loc+"&APPID="+key
    response=requests.get(url)
    res=response.json()
    
    if (res["cod"]=="404"):
        print("Location not found.")
    else:
        #temperature variables in kelvin
        tempK=res["main"]["temp"]
        tempHK=res["main"]["temp_max"]
        tempLK=res["main"]["temp_min"]
        feelK=res["main"]["feels_like"]
        
        #pressure in hectopascals (HPa)
        pres=res["main"]["pressure"]
        
        #humidity in percentage
        humi=res["main"]["humidity"]
        
        #brief weather description
        desc=res["weather"][0]["description"]
        
        #wind speed in meters per second
        windMPS=res["wind"]["speed"]
        #wind direction
        wind_deg=res["wind"]["deg"]
        wind_dir=deg_to_compass(wind_deg)
        
        #convert metric variables to imperial
        tempF=k_to_f(tempK)
        tempHF=k_to_f(tempHK)
        tempLF=k_to_f(tempLK)
        feelF=k_to_f(feelK)
        windMPH=mps_to_mph(windMPS)
        #convert HPa to atm
        pres*=0.0009869233
        
        #get icon code
        icon=res["weather"][0]["icon"]
        
        #create dictionary with values
        cur_wea={
            "Location":loc.split(",")[0],
            "Temp":tempF,
            "High_Temp":tempHF,
            "Low_Temp":tempLF,
            "Temp_Feel":feelF,
            "Humidity":humi,
            "Wind_Speed":windMPH,
            "Wind_Dir":wind_dir,
            "Pressure":round(pres,1),
            "Desc":desc,
            "Icon":icon
            }
    return cur_wea

def five_day_weather(key,loc):
    """
    generate five day forecast for given location. returns dataframe
    """
    #declare request variables
    base_url="http://api.openweathermap.org/data/2.5/forecast"
    url=base_url+"?q="+loc+"&APPID="+key
    response=requests.get(url)
    res=response.json()
    
    #create empty dataframe
    headers=["Unix","Format_Date","Temp","Feels_Like_Temp",
             "Weather_Main","Weather_Description","Icon"]
    df=pd.DataFrame(columns=headers)
    
    #pull timezone data
    tz=res["city"]["timezone"]
    
    if (res["cod"]=="404"):
        print("Location not found.")
    else:
        #iterate through each 3 hour increment
        for i in range(len(res["list"])):
            #date data
            unix_date=res["list"][i]["dt"]
            date=format_time(unix_date,tz)
            day=get_day(unix_date,tz)
            #temp data
            tempK=res["list"][i]["main"]["temp"]
            feelK=res["list"][i]["main"]["feels_like"]
            #weather data
            weather=res["list"][i]["weather"][0]["main"]
            desc=res["list"][i]["weather"][0]["description"]
            
            #convert temp data
            tempF=k_to_f(tempK)
            feelF=k_to_f(feelK)
            
            #precipitation chance in percent
            prec=res["list"][i]["pop"]*100
            
            #get icon code
            icon=res["list"][i]["weather"][0]["icon"]
            
            #append to dataframe
            new_row={"Unix":unix_date,
                     "Format_Date":date,
                     "Day":day,
                     "Temp":tempF,
                     "Feels_Like_Temp":feelF,
                     "Weather_Main":weather,
                     "Weather_Description":desc,
                     "Precipitation_Chance":prec,
                     "Icon":icon
                     }
            df=df._append(new_row,ignore_index=True)
    return df

def plot_five_day_temp(df):
    """
    generate plot for temperature across five days
    """
    #convert format date column to array with data type datetime64
    fd_array=np.array(df["Format_Date"],dtype="datetime64[s]")
    
    #generate plot object
    fig,ax=plt.subplots()
    #define limits
    lim=(np.datetime64(df["Format_Date"].min(),"m"),
         np.datetime64(df["Format_Date"].max(),"m"))
    #use locator and formatter to select best axis specs
    locator=mdates.AutoDateLocator(minticks=3,maxticks=7)
    formatter=mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    #force Y axis to only show integers
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    #create plot
    ax.plot(fd_array,df["Temp"],color="mediumpurple")
    ax.set_xlim(lim)
    ax.set_title("5-Day Temperature Forecast",fontsize=20)
    plt.yticks(fontsize=15)
    plt.xticks(fontsize=15)
    
    plt.show()

def group_five_day_weather(df):
    """
    take five_day_weather dataframe and condense to daily data using mode
    """
    headers=["Short_Format_Date","Freq_Weather_Main","Precipitation_Chance"]
    df2=pd.DataFrame(columns=headers)
    
    #extract days covered in five_day_weather dataframe
    days_list=df["Day"].unique()
    
    #iterate through days and pull mode data
    for day in days_list:
        freq_weather_main=df[df["Day"]==day]["Weather_Main"].mode()[0]
        short_format_date=df[df["Day"]==day]["Format_Date"].mode()[0].split(" ")[0]
        max_prec=df[df["Day"]==day]["Precipitation_Chance"].max()
        new_row={
            "Short_Format_Date":short_format_date,
            "Freq_Weather_Main":freq_weather_main,
            "Precipitation_Chance":int(max_prec)
            }
        df2=df2._append(new_row,ignore_index=True)
    return df2

def daily_weather(key,loc):
    """
    generate daily forecast at 3-hour increment for given location
    """
    #declare request variables
    base_url="http://api.openweathermap.org/data/2.5/forecast"
    url=base_url+"?q="+loc+"&APPID="+key
    response=requests.get(url)
    res=response.json()
    
    #create empty dataframe
    headers=["Unix","Format_Date","Temp","Feels_Like_Temp","Weather_Main","Weather_Description"]
    df=pd.DataFrame(columns=headers)
    
    #pull timezone data
    tz=res["city"]["timezone"]
    
    if (res["cod"]=="404"):
        print("Location not found.")
    else:
        #iterate through each day
        for i in range(8):
            #date data
            unix_date=res["list"][i]["dt"]
            date=format_time(unix_date, tz)
            #temp data
            tempK=res["list"][i]["main"]["temp"]
            feelK=res["list"][i]["main"]["feels_like"]
            #weather data
            weather=res["list"][i]["weather"][0]["main"]
            desc=res["list"][i]["weather"][0]["description"]
            
            #convert temp data
            tempF=k_to_f(tempK)
            feelF=k_to_f(feelK)
            
            #append to dataframe
            new_row={"Unix":unix_date,
                     "Format_Date":date,
                     "Temp":tempF,
                     "Feels_Like_Temp":feelF,
                     "Weather_Main":weather,
                     "Weather_Description":desc
                     }
            df=df._append(new_row,ignore_index=True)
    return df

def plot_daily_temp(df):
    """
    generate plot for daily temperature in 3 hour increments
    """
    #convert format date column to array with data type datetime64
    fd_array=np.array(df["Format_Date"],dtype="datetime64[s]")
    
    #cast temp columns to int for fill_between
    # temp_array=np.array(df["Temp"],dtype="int32")
    # feel_array=np.array(df["Feels_Like_Temp"],dtype="int32")
    
    #generate plot object
    fig,ax=plt.subplots()
    #define limits
    lim=(np.datetime64(df["Format_Date"].min(),"m"),
         np.datetime64(df["Format_Date"].max(),"m"))
    #use locator and formatter to select best axis specs
    locator=mdates.AutoDateLocator(minticks=3,maxticks=7)
    formatter=mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    #force Y axis to only show integers
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    #create plot
    ax.plot(fd_array,df["Feels_Like_Temp"],linestyle="dotted",color="cornflowerblue",linewidth=2)
    ax.plot(fd_array,df["Temp"],color="mediumpurple",linewidth=3)
    ax.set_xlim(lim)
    
    ax.set_title("24-Hour Temperature Forecast",fontsize=20)
    plt.yticks(fontsize=15)
    plt.xticks(fontsize=15)
    #ax.fill_between(fd_array,temp_array,feel_array,color="gainsboro")
    
    plt.show()

def air_quality(key,loc):
    """
    generate air quality report
    """
    #use geocoding api to retrieve latitude and longitude based on location
    geo_base_url="http://api.openweathermap.org/geo/1.0/direct"
    geo_url=geo_base_url+"?q="+loc+"&APPID="+key
    geo_response=requests.get(geo_url)
    geo_res=geo_response.json()
        
    lat=str(geo_res[0]["lat"])
    lon=str(geo_res[0]["lon"])
    
    #declare request variables
    base_url="http://api.openweathermap.org/data/2.5/air_pollution"
    url=base_url+"?lat="+lat+"&lon="+lon+"&APPID="+key
    response=requests.get(url)
    res=response.json()
    
    #air quality index
    aqi=res["list"][0]["main"]["aqi"]
    
    #index values
    aqi_scale={
        1:"Good",
        2:"Fair",
        3:"Moderate",
        4:"Poor",
        5:"Very Poor"
        }
    
    #air components in ug/m^3
    co=res["list"][0]["components"]["co"]
    no=res["list"][0]["components"]["no"]
    no2=res["list"][0]["components"]["no2"]
    o3=res["list"][0]["components"]["o3"]
    so2=res["list"][0]["components"]["so2"]
    pm2_5=res["list"][0]["components"]["pm2_5"]
    pm10=res["list"][0]["components"]["pm10"]
    nh3=res["list"][0]["components"]["nh3"]
    
    #create dictionary with values
    air_quality={
        "Location":loc.split(",")[0],
        "AQI":aqi,
        "AQI_Scale":aqi_scale[aqi],
        "Components":{
            "CO":co,
            "NO":no,
            "NO2":no2,
            "O3":o3,
            "SO2":so2,
            "PM2_5":pm2_5,
            "PM10":pm10,
            "NH3":nh3
            }
        }
    return air_quality

def plot_air_quality(dic):
    """
    use air quality dictionary to generate plot of air particulates
    """
    #generate plot object
    fig,axes=plt.subplots(1,7,figsize=(8,5))
    fig.tight_layout(pad=2)
    
    colors=["mediumpurple","cornflowerblue","lightgreen","gold","tomato"]

    #index dataset
    values=[0,1,2,3,4,5]
    scale_values=["","Good","Fair","Moderate","Poor","Very Poor"]
    #split aqi values for color bars
    bins_in=[1,1,1,1,0]
    stacks_in=get_stacks(bins_in, dic["AQI"])
    for i in range(len(stacks_in)):
        axes[0].bar("AQI",stacks_in[i],bottom=np.sum(stacks_in[:i],axis=0),color=colors[i])
    axes[0].set_ylim(0,5)
    #replace number ticks with qualitative categories
    axes[0].yaxis.set_major_locator(ticker.FixedLocator(values))
    axes[0].yaxis.set_major_formatter(ticker.FixedFormatter(scale_values))

    #SO2 dataset
    #split SO2 values for color bars
    bins_so2=[20,60,170,150,50]
    stacks_so2=get_stacks(bins_so2, dic["Components"]["SO2"])
    for i in range(len(stacks_so2)):
        axes[1].bar("SO2",stacks_so2[i],bottom=np.sum(stacks_so2[:i],axis=0),color=colors[i])
    axes[1].set_yticks(np.arange(0,401,400/5))
    axes[1].set_ylabel("μg/m^3")

    #NO2 dataset
    #split NO2 values for color bars
    bins_no2=[40,30,80,50,50]
    stacks_no2=get_stacks(bins_no2, dic["Components"]["NO2"])
    for i in range(len(stacks_no2)):
        axes[2].bar("NO2",stacks_no2[i],bottom=np.sum(stacks_no2[:i],axis=0),color=colors[i])
    axes[2].set_yticks(np.arange(0,251,250/5))

    #PM10 dataset
    #split PM10 values for color bars
    bins_pm10=[20,30,50,100,150]
    stacks_pm10=get_stacks(bins_pm10, dic["Components"]["PM10"])
    for i in range(len(stacks_pm10)):
        axes[3].bar("PM10",stacks_pm10[i],bottom=np.sum(stacks_pm10[:i],axis=0),color=colors[i])
    axes[3].set_yticks(np.arange(0,251,250/5))
    axes[3].set_title("Air Quality Report",fontsize=20)

    #PM2.5 dataset
    #split PM2.5 values for color bars
    bins_pm2_5=[10,15,25,25,25]
    stacks_pm2_5=get_stacks(bins_pm2_5, dic["Components"]["PM2_5"])
    for i in range(len(stacks_pm2_5)):
        axes[4].bar("PM2.5",stacks_pm2_5[i],bottom=np.sum(stacks_pm2_5[:i],axis=0),color=colors[i])
    axes[4].set_yticks(np.arange(0,101,100/5))

    #O3 dataset
    #split O3 values for color bars
    bins_o3=[60,40,40,40,20]
    stacks_o3=get_stacks(bins_o3, dic["Components"]["O3"])
    for i in range(len(stacks_o3)):
        axes[5].bar("O3",stacks_o3[i],bottom=np.sum(stacks_o3[:i],axis=0),color=colors[i])
    axes[5].set_yticks(np.arange(0,201,200/5))

    #CO dataset
    #split CO values for color bars
    bins_co=[4400,5000,3000,3000,4600]
    stacks_co=get_stacks(bins_co, dic["Components"]["CO"])
    for i in range(len(stacks_co)):
        axes[6].bar("CO",stacks_co[i],bottom=np.sum(stacks_co[:i],axis=0),color=colors[i])
    axes[6].set_yticks(np.arange(0,20001,20000/5))



