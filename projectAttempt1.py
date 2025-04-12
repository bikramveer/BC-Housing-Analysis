import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import geo
import sys

#Function to preprocess data

def loading_Data(input_file):
    #reading the data from csv file
    data = pd.read_csv(input_file, low_memory=False)

    #Filter the data for BC region and sort by locality
    dataBC = data[data['addressRegion'] == 'BC']
    dataBC = dataBC.sort_values(by='addressLocality')

    #getting Filtering for required columns
    dataBC = dataBC.filter([
        'streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'latitude',
        'longitude', 'price', 'property-beds', 'property-baths', 'property-sqft', 'Garage',
        'Property Type', 'Square Footage'
    ])

    #filter by property types
    property_types = ['Single Family', 'Condo', 'Townhome', 'MultiFamily']
    data_bc_single_family = dataBC[dataBC['Property Type'].isin(property_types)]

    #filter by metro Vancouver cities
    metro_vancouver_cities = [
        "Vancouver", "Burnaby", "Richmond", "Surrey", "Coquitlam", "North Vancouver",
        "West Vancouver", "New Westminster", "Delta", "Port Coquitlam", "Port Moody", "Langley"
    ]
    data_bc_single_family = data_bc_single_family[data_bc_single_family['addressLocality'].isin(metro_vancouver_cities)]

    #save all cleaned data for future use
    data_bc_single_family.to_csv('data_bc_1.csv')

    return data_bc_single_family

#we need to get the amenities and calualte distances
def amenities_function(data, amenities_file):
    #read the amenities data from csv

    amenities_data = pd.read_csv(amenities_file)

    #find the latitude and longitude
    lat_lon_array = data[['latitude', 'longitude']].to_numpy()

    results = []
    for lat, lon in lat_lon_array:
        amenities = geo.get_specific_amenities_cached(lat, lon, radius=3000)
        conv_distance = []
        transit_distance = []
        school_distance = []

        if amenities:
            for a in amenities:
                dist = geo.haversine(lat, lon, a['latitude'], a['longitude'])
                if a.get('shop') in ['convenience', 'grocery']:
                    conv_distance.append(dist)
                elif a.get('amenity') in ['bus_station', 'subway_station', 'railway_station']:
                    transit_distance.append(dist)
                elif a.get('amenity') in ['school', 'university']:
                    school_distance.append(dist)

        results.append({
            'latitude': lat,
            'longitude': lon,
            'avg_convenience_dist': np.mean(conv_distance) if conv_distance else np.nan,
            'avg_transit_distance': np.mean(transit_distance) if transit_distance else np.nan,
            'avg_school_distance': np.mean(school_distance) if school_distance else np.nan
        })

    results_df = pd.DataFrame(results)

    #save results into CSV/JSON for future use
    results_df.to_json("amenities_distances.json", orient="records")
    results_df.to_csv('amenities_distances.csv', index=False)

    return results_df

#merge then together
def merge_df(main_df, amenities_df):
    return main_df.merge(
        amenities_df,
        on=['latitude', 'longitude'],
        how='left'
    )


#
def price_to_income(data):
    censusdata = pd.read_csv('CensusProfile2021.csv', encoding='latin1')
    filtered_df = censusdata[censusdata.iloc[:, 0].str.contains("Income of individuals in", case=False, na=False)]
    final_df = filtered_df[filtered_df.iloc[:, 1].str.contains("average|median", case=False, na=False)]
    final_2020_df = final_df[final_df.iloc[:, 0].str.contains("2020", na=False) |
                             final_df.iloc[:, 1].str.contains("2020", na=False)]
    final_2020_df = final_2020_df[final_2020_df.iloc[:, 1].str.contains(
        "Median employment income in 2020 for full-year full-time workers in 2020", case=False, na=False)]

    #median income value
    final_2020_df['Unnamed: 2'] = pd.to_numeric(final_2020_df['Unnamed: 2'], errors='coerce')
    median_income = final_2020_df['Unnamed: 2'].iloc[0]

    #finally calculate price-to-income ratio
    data['Price-to-income Ratio'] = data['price'] / median_income
    return data


#scaling an normalizing the data
def scale_data(data):
    features = [
        'price', 'property-beds', 'property-baths', 'property-sqft', 'Garage',
        'Property Type', 'avg_convenience_dist', 'avg_transit_distance', 'avg_school_distance',
        'Price-to-income Ratio'
    ]

    #convert property sqft into numeric
    data['property-sqft'] = pd.to_numeric(data['property-sqft'].str.replace(',', '', regex=False), errors='coerce')

    #property mapped into numeric values
    data['Property Type'] = data['Property Type'].map({
        'Condo': 0.25, 'Townhome': 0.5, 'Single Family': 0.75, 'MultiFamily': 1
    })

    #dealing with values by filling with max*1.1
    convenience_max = data['avg_convenience_dist'].max()
    transit_max = data['avg_transit_distance'].max()
    school_max = data['avg_school_distance'].max()

    data['avg_convenience_dist'] = data['avg_convenience_dist'].fillna(convenience_max * 1.1)
    data['avg_transit_distance'] = data['avg_transit_distance'].fillna(transit_max * 1.1)
    data['avg_school_distance'] = data['avg_school_distance'].fillna(school_max * 1.1)
    data['Garage'] = np.where(data['Garage'] == 'Yes', 1, 0)

    #normalize using minmanscaler
    scaler = MinMaxScaler()
    data_scaled = data.copy()

    data_scaled["price"] = 1 - data_scaled['price']
    data_scaled['avg_convenience_dist'] = 1 - data_scaled['avg_convenience_dist']
    data_scaled['avg_transit_distance'] = 1 - data_scaled['avg_transit_distance']
    data_scaled['avg_school_distance'] = 1 - data_scaled['avg_school_distance']

    data_scaled[features] = scaler.fit_transform(data[features])
    data_scaled = data_scaled.dropna()

    return data_scaled

def final_scores(data_scaled):
    score_features = [
        'price', 'property-beds', 'property-baths', 'property-sqft', 'Garage',
        'Property Type', 'avg_convenience_dist', 'avg_transit_distance', 'avg_school_distance',
        'Price-to-income Ratio'
    ]

    # equal weights for now
    weights = np.array([1/len(score_features)] * len(score_features))

    #find the score
    data_scaled['Score'] = data_scaled[score_features].dot(weights)
    data_scaled.sort_values(by='Score', ascending=False, inplace=True)

    return data_scaled



def main():
    # needs 2 input files --> python projectAttempt1.py data_bc.csv amenities_distances.csv
    if len(sys.argv) != 3:
        print("requires more input file")
        sys.exit(1)

    #get the file paths from the command line
    data_file = sys.argv[1]
    amenities_file = sys.argv[2]

    #load the data
    data_bc_single_family = loading_Data(data_file)

    #get amenities distances in df
    amenities_df = amenities_function(data_bc_single_family, amenities_file)

    # add amenities distances
    data_bc_single_family = merge_df(data_bc_single_family, amenities_df)

    #find alculate price --> income ratio
    data_bc_single_family = price_to_income(data_bc_single_family)

    #normalize and scale the data
    data_scaled = scale_data(data_bc_single_family)

    #calculate scores based on features
    data_scored = final_scores(data_scaled)

    #We now can plot the data
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='addressLocality', y='Score', data=data_scored)
    plt.title('Distribution of House Scores by City')
    plt.xlabel('City')
    plt.ylabel('Score')
    plt.xticks(rotation=45)
    plt.grid(True, axis='y')
    plt.show()

if __name__ == "__main__":
    main()
