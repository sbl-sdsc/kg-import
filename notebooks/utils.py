#!/usr/bin/env python
# coding: utf-8

def create_node_headers(dirname, filename):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # read metadata file
    df = pd.read_csv(os.path.join(dirname, filename))
    df.fillna('', inplace=True)

    # create column names for header file
    df['colName'] = df['property'] + ':' + df['type']
    
    # Create unique ID for primary key
    node = re.split('\.|_', filename)[0]
    df['colName'].iloc[0] = df['property'].iloc[0] + ':ID(' + node + '-ID)'

    # create header of original csv file
    propertys = df['property'].values
    csv_header = ','.join(propertys)

    # create Neo4j import header
    col_names = df['colName'].values
    import_header = ','.join(col_names)

    return {'node': node, 'metadataHeader': csv_header,
            'importHeader': import_header, 'metadataPath': os.path.join(dirname,filename)}

def create_relationship_headers(dirname, filename):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # read metadata file
    df = pd.read_csv(os.path.join(dirname, filename))
    df.fillna('', inplace=True)

    # create column names for header file
    df['colName'] = df['property'] + ':' + df['type']
    
    # Create unique ID for primary key
    #parts = re.split('\.|_', filename)
    #basename = re.split('\.|_', filename)
    
    # remove extension from filename
    basename = filename.split('.')[0]
    # split nodes from relationship
    parts = basename.split('-', 2)
    source_node = parts[0]
    relationship = parts[1]
    # remove any extra tags separated by underscore
    target_node = parts[2].split('_')[0]
    
    df['colName'].iloc[0] = ':START_ID(' + source_node + '-ID)'
    df['colName'].iloc[1] = ':END_ID(' + target_node + '-ID)'

    # create header of original csv file
    propertys = df['property'].values
    csv_header = ','.join(propertys)

    # create Neo4j import header
    col_names = df['colName'].values
    import_header = ','.join(col_names)

    return {'relationship': relationship, 'metadataHeader': csv_header, 
            'importHeader': import_header, 'source': source_node, 'target': target_node, 'metadataPath': os.path.join(dirname,filename)}

def get_node_data_headers(dirname, filename):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # get node name
    node = re.split('\.|_', filename)[0]
    
    # read metadata file
    data_path = os.path.join(dirname, filename)
    df = pd.read_csv(data_path, nrows=0)
    
    # create csv header
    columns = list(df.columns)
    csv_header = ','.join(columns)
    
    return {'node': node, 'dataHeader': csv_header, 'dataPath': data_path}

def get_relationship_data_headers(dirname, filename):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # get relationship name
    #parts = re.split('\.|_', filename)
    parts = filename.split('-', 2)
    relationship = parts[1]
    
    # read metadata file
    data_path = os.path.join(dirname, filename)
    df = pd.read_csv(data_path, nrows=0)
    
    # create csv header
    columns = list(df.columns)
    csv_header = ','.join(columns)
    
    return {'relationship': relationship, 'dataHeader': csv_header, 'dataPath': data_path}

def create_meta_node(node_name, property_dir, metadata_path):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # read metadata file
    df = pd.read_csv(metadata_path)
    df.fillna('', inplace=True)
    
    df['propertyDescription'] = df['description'] + ' (' + df['type'] + ')'
    df = df[['property', 'propertyDescription']]
    
    meta_dir =property_dir.copy()

    for name, description in df.itertuples(index=False):
        meta_dir[name] = description
        
    meta_dir['nodeName:ID(MetaNode-ID)'] = node_name
    
    return meta_dir

def create_meta_relationship(relationship_name, source, target, property_dir, metadata_path):
    import os
    from os.path import join
    import re
    import pandas as pd
    
    # read metadata file
    df = pd.read_csv(metadata_path)
    df.fillna('', inplace=True)
    
    df['propertyDescription'] = df['description'] + ' (' + df['type'] + ')'
    df = df[['property', 'propertyDescription']]
    
    meta_dir = property_dir.copy()

    for name, description in df.itertuples(index=False):
        meta_dir[name] = description
        
    meta_dir['relationshipName'] = relationship_name
    meta_dir['source:START_ID(MetaNode-ID)'] = source
    meta_dir['target:END_ID(MetaNode-ID)'] = target
    
    return meta_dir

    
    