import numpy as np
import pandas as pd

# Example data extracted from the image (manual entry for demonstration)
building_data = [
    {'Project Name': '380 Stuart', 'Annual Electric (kWh)': 6543689, 'Peak Electric (kW)': 2742},
    {'Project Name': '22 Drydock', 'Annual Electric (kWh)': 9598306, 'Peak Electric (kW)': 2543},
    {'Project Name': 'Rockwood Manor', 'Annual Electric (kWh)': 482051, 'Peak Electric (kW)': 6.5},
    {'Project Name': '175 N. Harvard Street - Housing', 'Annual Electric (kWh)': 1463392, 'Peak Electric (kW)': 234},
    {'Project Name': '1208C VFW Parkway Residences', 'Annual Electric (kWh)': 587850, 'Peak Electric (kW)': 37},
    {'Project Name': '18-22 Arboretum', 'Annual Electric (kWh)': 1537054, 'Peak Electric (kW)': 812.4},
    {'Project Name': 'Cheney St Apartments (4-18 Cheney)', 'Annual Electric (kWh)': 237220, 'Peak Electric (kW)': 250},
    {'Project Name': '175 N. Harvard St - Affiliate Housing', 'Annual Electric (kWh)': 1463392, 'Peak Electric (kW)': 234}
]

# Load the COMStock dataset for reference pattern
comstock_pattern_path = 'COMStock_large_office_15_minute_timeseries_data_Tugcin.csv'
new_timeseries_data = pd.read_csv(comstock_pattern_path, delimiter=';')
comstock_pattern = new_timeseries_data[['Timestamp (EST)', 'upgrade.out.electricity.total.energy_consumption.kwh']].copy()
comstock_pattern.set_index('Timestamp (EST)', inplace=True)

# Normalize the COMStock pattern to generate a load profile
comstock_pattern['Normalized Load'] = comstock_pattern['upgrade.out.electricity.total.energy_consumption.kwh'] / comstock_pattern['upgrade.out.electricity.total.energy_consumption.kwh'].max()

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
    
    # Create a DataFrame for the load profile
    profile_df = pd.DataFrame({
        'Timestamp': comstock_pattern.index,
        'Power Demand (kW)': load_profile
    })
    
    return profile_df

# Generate and save load profiles for each building
output_files = []
for building in building_data:
    profile_df = generate_load_profile(building, comstock_pattern)
    output_file_path = f'{building["Project Name"].replace(" ", "_")}_Load_Profile.csv'
    profile_df.to_csv(output_file_path, index=False)
    output_files.append(output_file_path)
    print(f'Saved load profile for {building["Project Name"]} to {output_file_path}')

output_files
