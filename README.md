# Data Aggregation

## Introduction
An e-commerce shop would like to onboard new suppliers efficiently. To enable the onboarding process, the customer needs
us to integrate product data from suppliers in various formats and styles into the pre-defined data structure of their e-commerce shop application.

## Tasks
Your goal is to transform the supplier data so that it could be directly loaded into the target dataset without any other changes.
For each step, you should first profile the data to understand what you can do for the customer, then implement a few selected
functions (you can keep it lightweight), and tell the customer what you can also potentially do for them, using examples to
illustrate.

### Pre-processing
Here you need to transform the supplier data so that has the same granularity as the target data. (Hint: how many rows per
product do you have in the target data?).
Be aware of character encodings when processing the data.

### Normalisation
Normalisation is required in case an attribute value is different but actually is the same (different spelling, language, different unit used etc.).
Example: if the source encodes Booleans as “Yes”/”No”, but the target as 1/0, then you would need to normalize “Yes” to 1
and “No” to 0.
Please normalize at least 3 attributes, and describe which normalizations are required for the other attributes.
Input: pre-processed data
Output: normalized supplier data

### Integration
Data Integration is to transform the supplier data with a specific data schema into a new dataset with target data schema,
such as to:
- keep any attributes that you can map to the target schema
- discard attributes not mapped to the target schema
- keep the number of records as unchanged
Input: normalized supplier data
Output: integrated supplier data

### Results
* An Excel/LibreOffice spreadsheet (no csv/txt) with 3 tabs showing the results of each step above (i.e., pre-processing/normalisation/integration)
* A script (R/Python/SQL/etc.) that can be executed to provide the above Excel file
* A customer presentation (PowerPoint or similar) to describe the above processing. Assume that the audience is the
customer onboarding manager – someone with business knowledge, and medium technical knowledge
