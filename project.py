import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import geo

data_file = sys.argv[1]
amenities_file = sys.argv[2]
income_file = sys.argv[3]

data = pd.read_csv(data_file, low_memory=False)

dataBC = data[data['addressRegion'] == 'BC']
dataBC = dataBC.sort_values(by='addressLocality')

dataBC = dataBC.filter([
    'streetAddress',
    'addressLocality',
    'addressRegion',
    'postalCode',
    'latitude',
    'longitude',
    'price',
    'property-beds',
    'property-baths',
    'property-sqft',
    'Garage',
    'Property Type', #Agricultural, Condo, Condo/Townhouse, Duplex, Manufactured Home, Mobile Home, MultiFamily, Single Family, Townhome, Vacant Land
    'Square Footage',
    ])

property_types = ['Single Family','Condo', 'Townhome', 'MultiFamily']
data_filtered = dataBC[dataBC['Property Type'].isin(property_types)]

metro_vancouver_cities = [
    "Vancouver", "Burnaby", "Richmond", "Surrey", "Coquitlam",
    "North Vancouver", "West Vancouver", "New Westminster",
    "Delta", "Port Coquitlam", "Port Moody", "Langley"
]
data_filtered = data_filtered[data_filtered['addressLocality'].isin(metro_vancouver_cities)]

lat_lon_array = data_filtered[['latitude', 'longitude']].to_numpy()

def enrich_main_data(main_df, amenities_df):
    return main_df.merge(
        amenities_df,
        on=['latitude', 'longitude'],
        how='left'
    )

amenities_data = pd.read_csv(amenities_file)
data_filtered = enrich_main_data(data_filtered, amenities_data)


censusdata = pd.read_csv(income_file, encoding='latin1')
filtered_df = censusdata[censusdata.iloc[:, 0].str.contains("Income of individuals in", case=False, na=False)]
final_df = filtered_df[filtered_df.iloc[:, 1].str.contains("average|median", case=False, na=False)]
final_2020_df = final_df[
    final_df.iloc[:, 0].str.contains("2020", na=False) |
    final_df.iloc[:, 1].str.contains("2020", na=False)
]
final_2020_df = final_2020_df[final_2020_df.iloc[:, 1].str.contains("Median employment income in 2020 for full-year full-time workers in 2020", case=False, na=False)]
final_2020_df['Unnamed: 2'] = pd.to_numeric(final_2020_df['Unnamed: 2'], errors='coerce')
median_income = final_2020_df['Unnamed: 2'].iloc[0]

data_filtered['Price-to-income Ratio'] = data_filtered['price'] / median_income 

features = [
            'price',
            'property-beds', 
            'property-baths', 
            'property-sqft', 
            'Garage',
            'Property Type', 
            'avg_convenience_dist', 
            'avg_transit_distance', 
            'avg_school_distance', 
            'Price-to-income Ratio',
        ]
data_filtered['property-sqft'] = (data_filtered['property-sqft'].str.replace(',', '', regex=False).astype(float))
data_filtered['property-sqft'] = pd.to_numeric(data_filtered['property-sqft'], errors='coerce')
data_filtered['Property Type'] = data_filtered['Property Type'].map({'Condo': 0.25, 'Townhome': 0.5, 'Single Family': 0.75, 'MultiFamily': 1})

convenience_max = data_filtered['avg_convenience_dist'].max()
transit_max = data_filtered['avg_transit_distance'].max()
school_max = data_filtered['avg_school_distance'].max()
data_filtered['avg_convenience_dist'] = data_filtered['avg_convenience_dist'].fillna(convenience_max * 1.1)
data_filtered['avg_transit_distance'] = data_filtered['avg_transit_distance'].fillna(transit_max * 1.1)
data_filtered['avg_school_distance'] = data_filtered['avg_school_distance'].fillna(school_max * 1.1)
data_filtered['Garage'] = np.where(data_filtered['Garage'] == 'Yes', 1, 0)

scaler = MinMaxScaler()
# since lower is better, we inverse our price and our distance values before scoring
data_filtered["price"] = 1 - data_filtered['price']
data_filtered['avg_convenience_dist'] = 1 - data_filtered['avg_convenience_dist']
data_filtered['avg_transit_distance'] = 1 - data_filtered['avg_transit_distance']
data_filtered['avg_school_distance'] = 1 - data_filtered['avg_school_distance']

data_filtered[features] = scaler.fit_transform(data_filtered[features])
data_filtered = data_filtered.dropna()
data_filtered.to_csv('data.csv')

score_features = [
            'price',
            'property-beds', 
            'property-baths', 
            'property-sqft', 
            'Garage',
            'Property Type', 
            'avg_convenience_dist', 
            'avg_transit_distance', 
            'avg_school_distance', 
            'Price-to-income Ratio',
        ]

# currently setting all our features to hold equal weight. This can be adjusted if needed. Maybe user input?
weights = np.array([1/len(score_features)] * len(score_features))
# again, copied to save our original, but not needed in final .py file

data_filtered['Score'] = data_filtered[score_features].dot(weights)
data_filtered.sort_values(by='Score', ascending=False, inplace=True)
data_filtered = data_filtered.drop_duplicates()

plt.figure(figsize=(12, 6))
sns.boxplot(x='addressLocality', y='Score', data=data_filtered)

plt.title('Distribution of House Scores by City')
plt.xlabel('City')
plt.ylabel('Score')
plt.xticks(rotation=45)
plt.grid(True, axis='y')
plt.savefig('distribution.svg')

medians = data_filtered.groupby('addressLocality')['Score'].median().sort_values()
cities = medians.index.to_list()

plt.figure(figsize=(12, 6))
sns.boxplot(x='addressLocality', y='Score', data=data_filtered, order=cities)

plt.title('Distribution of House Scores Sorted by City ')
plt.xlabel('City')
plt.ylabel('Score')
plt.xticks(rotation=45)
plt.grid(True, axis='y')
plt.savefig('distribution_sorted.svg')

X = data_filtered[[
                # 'price',
                'property-beds',
                'property-baths',
                'property-sqft',
                'Garage',
                'Property Type',
                'avg_convenience_dist',
                'avg_transit_distance',
                'avg_school_distance',
                # 'Price-to-income Ratio'
                ]]
X = sm.add_constant(X)
y = data_filtered['price']

model = sm.OLS(y, X).fit()
coefficients = model.params.drop('const')
errors = model.bse.drop('const')
model_summary = model.summary()

print(model_summary)

plt.figure(figsize=(12, 6))
coefficients.plot(kind='bar', yerr=errors, capsize=5, color='blue')
plt.title('Feature Significane on House Price (OLS)')
plt.ylabel('Coefficient Value ($ Impact)')
plt.axhline(0, color='gray', linestyle='--')
plt.grid(True, axis='y')
plt.savefig('feature_significance.svg')

X = data_filtered[[
                # 'price',
                'property-beds',
                'property-baths',
                # 'property-sqft',
                'Garage',
                'Property Type',
                'avg_convenience_dist',
                'avg_transit_distance',
                'avg_school_distance',
                # 'Price-to-income Ratio'
                ]]
X = sm.add_constant(X)
y = data_filtered['price']

model = sm.OLS(y, X).fit()
coefficients = model.params.drop('const')
errors = model.bse.drop('const')
model_summary = model.summary()

print(model_summary)

plt.figure(figsize=(12, 6))
coefficients.plot(kind='bar', yerr=errors, capsize=5, color='blue')
plt.title('Feature Significane on House Price (OLS)')
plt.ylabel('Coefficient Value ($ Impact)')
plt.axhline(0, color='gray', linestyle='--')
plt.grid(True, axis='y')
plt.savefig('feature_significance_minus_sqft.svg')