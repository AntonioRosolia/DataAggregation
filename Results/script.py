import json
import numpy as np
import pandas as pd
import xlrd


from pandas.io.json import json_normalize
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from translate import Translator


geolocator = Nominatim(user_agent='preprocessing')
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

translator = Translator(from_lang='german',to_lang='english')


def setStringToTitle(val, alreadyChanged, sourceSeries, splitter):
    #splitet strings according to the splitter and format them as titles, if 
    #they are more than 3 characters long and do not contain 
    #any numbers or "-". 
    #example: val = 'HARLEY-DAVIDSON', splitter = '-'
    #         return -> 'Harley-Davidson'
    for j, stringElement in enumerate(val.split(splitter)):
        if len(stringElement) >= 4:
            if stringElement not in alreadyChanged and not None and not any(char.isdigit() for char in stringElement) and not '-' in stringElement:
                sourceSeries = sourceSeries.str.replace(stringElement.upper(), stringElement.title())
                alreadyChanged.append(stringElement)
    return alreadyChanged, sourceSeries
    

def setSeriesToTargetDataFormat(sourceSeries, targetSeries):
    #return sourceSeries to format of targetSeries, if element of sourceSeries
    #is not in targetSeries, the setStringToTitle function will be called
    #example: sourceSeries =pd.Series(['bmw', 'fIaT', 'BmW', 'GRAND SPORT GT'])
    #         targetSeries = pd.Series(['BMW', 'Fiat'])  
    #         return -> pd.Series(['BMW','Fiat', 'BMW', 'Grand Sport GT'])   
    source = sourceSeries.unique()
    target = targetSeries.unique()
    
    sourceUnique = [str(val).lower() for val in source]
    targetUnique = [str(val).lower() for val in target]
    
    alreadyChanged = []
    
    for i, val in enumerate(sourceUnique):
        if val in targetUnique:
            index = targetUnique.index(val)
            sourceSeries.replace(source[i], target[index], inplace=True)
        else:
            alreadyChanged, sourceSeries = setStringToTitle(val, alreadyChanged, sourceSeries, '-')
            alreadyChanged, sourceSeries = setStringToTitle(val, alreadyChanged, sourceSeries, ' ')
    return sourceSeries          
    


def getCountryCodeAndZip(series):
    #returns formated country code and zip from series of cities
    #example: series = pd.Series(['Zuzwil'])
    #         return -> pd.Series(['CH']), pd.Series(['Bern'])
    countryCodes = []
    countryZip = []
    locatedCities = []
    locatedCitiesCountryCode=[]
    locatedCitiesZip = []
    for i, val in series.fillna("").iteritems():
        if val=="":
            addCountryCode = np.nan
            addCountryZip = np.nan
        elif val in locatedCities:
            index = locatedCities.index(val)
            addCountryCode = locatedCitiesCountryCode[index]
            addCountryZip = locatedCitiesZip[index]
        else:
            #first has to get coordinates from city to get a structured query
            #from the API
            location = geolocator.geocode(val, language='en')
            loc = geolocator.reverse([location.latitude,location.longitude], language='en')
            addCountryCode = loc.raw['address']['country_code'].upper()
            locatedCities.append(val)
            locatedCitiesCountryCode.append(loc.raw['address']['country_code'].upper())
            locatedCitiesZip.append(loc.raw['address']['state'])
        countryCodes.append(addCountryCode)
        countryZip.append(addCountryZip)
    return countryCodes, countryZip


def translate_column(series):
    #splits the string from series and only the first column will be translated
    #from english to german
    #returns formated translated series
    #example: series = pd.Series(['schwarz met.'])
    #         return -> pd.Series(['Black'])
    addValue=""
    alreadyTranslated = []
    translatedValue = []
    translation = []
    for i, val in series.str.split(expand=True)[0].fillna("").iteritems():
        if val=="":
            addValue = ""
        elif val in alreadyTranslated:
            index = alreadyTranslated.index(val)
            addValue = translatedValue[index]
        else:
            addValue = translator.translate(val).lower()
            alreadyTranslated.append(val)
            translatedValue.append(addValue)
        translation.append(addValue)
    return [str(val).title() for val in translation]


def main():
    
    ###############
    #preprocessing#
    ###############
    
    #try open target data and load it into DataFrame
    try:
        workbook = xlrd.open_workbook('Target Data.xlsx')
        sheet = workbook.sheet_by_index(0)
        xls_file = pd.ExcelFile('Target Data.xlsx')
        df_target = xls_file.parse()
    except:
        print('Error, could not open Excel File')
            
    #try open supplier data
    try:
        supplier_data = [json.loads(line) for line in open('supplier_car.json', 'r', encoding='utf8')]
    except:
        print('Error, could not open JSON File')
    
    
    #create DataFrame from the normal structured columns
    df = pd.DataFrame.from_dict(json_normalize(supplier_data))
    
    #create DataFrame with the attributes
    df_attributes = df.iloc[:,:2]
    
    #delete first 3 columns
    df = df.iloc[:,3:-1]
    
    #converts the attributes to normal sturcture DataFrame
    for attribute in df_attributes['Attribute Names'].unique():
        df[attribute]=df_attributes['Attribute Values'][df_attributes['Attribute Names'] == attribute]
    
    
    #renamte DataFrame columns to corresponding columns
    df = df.rename(columns={'MakeText': 'make', 'ModelText': 'model', 'TypeName': 'model_variant', 'FirstRegYear': 'manufacture_year', 'City': 'city', 'ConsumptionTotalText':'fuel_consumption_unit', 'FirstRegMonth':'manufacture_month', 'BodyColorText':'color', 'Km':'mileage', 'BodyTypeText':'carType'})
        
    #if 'l/100km' is in fuel_consumption_unit, fuel_consumption_unit
    #is set to l_km_consumption, which is the same as in target_data
    df['fuel_consumption_unit'] = pd.np.where(df.fuel_consumption_unit.str.contains('l/100km'), 'l_km_consumption', df['fuel_consumption_unit'])
    
    #if column from target_data is not in df yet, it will be added
    column_names = sheet.row_values(0)
    for column in column_names:
        if column not in df:
            df[column] = None    
    
    #set some columns to numeric
    df['manufacture_month'] = pd.to_numeric(df['manufacture_month'])
    df['manufacture_year'] = pd.to_numeric(df['manufacture_year'])
    df['mileage'] = pd.to_numeric(df['mileage'])
    
    #condition is made up from ConditionTypeText and Properties columns
    df['condition'] = df['ConditionTypeText'].fillna("") + df['Properties'].fillna("")
    df.loc[df.mileage>=1001, 'condition'] = 'Used'
    df.loc[df.mileage<1001, 'condition'] = 'New'
    
    #if mileage is greater than or equal to 0, mileage_unit is in km, since
    #all the the units were in km from the source file
    df.loc[df.mileage>=0, 'mileage_unit'] = 'kilometer'
    df.loc[df.fuel_consumption_unit=='l_km_consumption', 'mileage_unit'] = 'kilometer'
    
    #if car has only one seat it is a singleseater
    df.loc[df.Seats=='1', 'carType'] = 'Single seater'
    
    #check various strings if they are in model_variant 
    #and set the corresponding carType    
    df['carType'] = pd.np.where(df.model_variant.str.contains('coupé', case=False), 'Coupé',
                       pd.np.where(df.model_variant.str.contains('cpé', case=False), 'Coupé',
                       pd.np.where(df.model_variant.str.contains('limous', case=False), 'Saloon',
                       pd.np.where(df.model_variant.str.contains('targa', case=False), 'Targa',
                       pd.np.where(df.model_variant.str.contains('roadst', case=False), 'Convertible / Roadster',
                       pd.np.where(df.model_variant.str.contains('spid', case=False), 'Convertible / Roadster',
                       pd.np.where(df.model_variant.str.contains('spyd', case=False), 'Convertible / Roadster',
                       pd.np.where(df.model_variant.str.contains('convert', case=False), 'Convertible / Roadster',
                       pd.np.where(df.model_variant.str.contains('cabr', case=False), 'Convertible / Roadster',df['carType'])))))))))
    
    
    #set country and zip column from city series
    df['country'], df['zip'] = getCountryCodeAndZip(df['city'])
    
    #remove all columns, which are not in column_names
    #column_names is the header row from target data
    df = df[column_names] 
    
    df_preprocessing = df.copy()
     
    ###################
    #end preprocessing#
    ###################
    
    #####################
    #start normalisation#
    #####################
    
    #First Normalisation, translate color column and adjust format
    df['color'] = translate_column(df['color'])
    
    #Second Normalisation
    #normalize make column for Ford
    df['make'].replace('FORD (USA)','FORD',inplace=True)
    
    #normalize BMW, set model_variant as seen in target data for BWM Alpina
    df.loc[df.make=='BMW-ALPINA', 'model_variant'] = df['model']+' '+df['model_variant']
    #set model as seen in target data for BWM Alpina
    df.loc[df.make=='BMW-ALPINA', 'model'] = 'Alpina'
    #normalize BMW
    df['make'].replace('BMW-ALPINA', 'BMW', inplace=True)
    
    #adjust format as seen in target data
    df['make'] = setSeriesToTargetDataFormat(df['make'], df_target['make'])
    
    #Third Normalisation for column condition
    #if "Ab MFK" is in condition, set to "Used with guarantee" 
    df['condition'] = pd.np.where(df.condition.str.contains('Ab MFK'), 'Used with guarantee', df['condition'])

    #replace Neu with New
    df['condition'].replace('Neu', 'New', inplace = True)
    
    #replace various strings to used
    used = ['Occasion', 'Vorführmodell', '"Rennwagen"', '"Tuning"', 'Oldtimer', '"Direkt-/Parallelimport"']
    for val in used:
        df['condition'].replace(val, 'Used', inplace = True)
    
    
    #Forth Normalisation
    df['carType'].replace('Cabriolet', 'Convertible / Roadster', inplace = True)
    df['carType'].replace('Limousine', 'Saloon', inplace = True)
    df['carType'].replace('SUV / Geländewagen', 'SUV', inplace = True)
    df['carType'].replace('Kombi', 'Station Wagon', inplace = True)
    df['carType'].replace('Wohnkabine', 'Other', inplace = True)
    df['carType'].replace('Sattelschlepper', 'Other', inplace = True)
    df['carType'].replace('Kleinwagen', 'Other', inplace = True)
    df['carType'].replace('Kompaktvan / Minivan', 'Other', inplace = True)
    df['carType'].replace('Pick-up', 'Other', inplace = True)
    
    
    #Fifth Normalisation
    df['model'] = setSeriesToTargetDataFormat(df['model'], df_target['model'])
    
    
    #Sixth Normalisation
    df['model_variant'] = setSeriesToTargetDataFormat(df['model_variant'], df_target['model_variant'])
        
    df_normalisation = df.copy()
    
    ###################
    #end normalisation#    
    ###################
    
    
    ###################
    #start integration#
    ###################
    
    df_integration = pd.DataFrame()
    df_integration = pd.concat([df, df_target], ignore_index=True)
    
    
    #################
    #end integration#
    #################
    
    with pd.ExcelWriter('AntonioRosolia_RemoteTask_output.xlsx') as writer:  # doctest: +SKIP
        df_preprocessing.to_excel(writer, sheet_name='pre-processing')
        df_normalisation.to_excel(writer, sheet_name='normalisation')
        df_integration.to_excel(writer, sheet_name='integration')    
    
if __name__ == "__main__": main()

