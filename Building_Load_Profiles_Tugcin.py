import numpy as np
import pandas as pd

# Load the new building data file
boston_building_data_path = 'Boston_Load_profile_Example.csv'
boston_building_data = pd.read_csv(boston_building_data_path, delimiter=';')

# Load the COMStock profiles
comstock_hotel_path = 'COMStock_hotel_15_minute_timeseries_data_Tugcin.csv'
comstock_large_office_path = 'COMStock_large_office_15_minute_timeseries_data_Tugcin.csv'

comstock_hotel = pd.read_csv(comstock_hotel_path, delimiter=';')
comstock_large_office = pd.read_csv(comstock_large_office_path, delimiter=';')

# Normalize the COMStock patterns
comstock_hotel['Timestamp'] = pd.to_datetime(comstock_hotel['Timestamp (EST)'])
comstock_hotel.set_index('Timestamp', inplace=True)
comstock_hotel['Normalized Load'] = comstock_hotel['upgrade.out.electricity.total.energy_consumption.kwh'] / comstock_hotel['upgrade.out.electricity.total.energy_consumption.kwh'].max()

comstock_large_office['Timestamp'] = pd.to_datetime(comstock_large_office['Timestamp (EST)'])
comstock_large_office.set_index('Timestamp', inplace=True)
comstock_large_office['Normalized Load'] = comstock_large_office['upgrade.out.electricity.total.energy_consumption.kwh'] / comstock_large_office['upgrade.out.electricity.total.energy_consumption.kwh'].max()

# Function to generate load profile for a building
def generate_load_profile(building, comstock_pattern):
    annual_kwh = building['Annual Electric (kWh)']
    peak_kw = building['Peak Electric (kW)']
    
    # Scale the normalized load to the building's annual consumption and peak
    load_profile = comstock_pattern['Normalized Load'] * peak_kw
    total_annual_kwh = load_profile.sum() * (15/60)  # converting 15-min interval to hours
    
    # Scale the profile to match the annual consumption
    scaling_factor = annual_kwh / total_annual_kwh
    load_profile *= scaling_factor
    
    # Resample the load profile to hourly resolution
    load_profile_hourly = load_profile.resample('H').mean()
    
    # Create a DataFrame for the load profile
    profile_df = pd.DataFrame({
        'Timestamp': load_profile_hourly.index,
        'Power Demand (kW)': load_profile_hourly.values
    })
    
    return profile_df

# Generate load profiles for all buildings
all_profiles = {}
for _, building in boston_building_data.iterrows():
    if building['Building Type'] == 'Residential':
        comstock_pattern = comstock_hotel
    else:
        comstock_pattern = comstock_large_office
    
    profile_df = generate_load_profile(building, comstock_pattern)
    all_profiles[building['Project Name']] = profile_df

# Save profiles to CSV files
for project_name, profile_df in all_profiles.items():
    file_path = f"{project_name.replace(' ', '_')}_Load_Profile.csv"
    profile_df.to_csv(file_path, index=False)
    print(f"Saved load profile for {project_name} to {file_path}")
