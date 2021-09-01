from blackduck import Client
import logging
import argparse
import sys
from pprint import pprint
import requests
import pandas as pd


parser = argparse.ArgumentParser("Adds a list of components to a project fed from the components csv report. Creates components with origin id")
parser.add_argument("--base-url", required=True, help="Hub server URL e.g. https://your.blackduck.url")
parser.add_argument("--api-key", dest='api_key', required=True, help="containing access token")
parser.add_argument("--project", dest='project_name', required=True)
parser.add_argument("--version", dest="version_name", required=True)
parser.add_argument("--component_list_file", dest="component_list", required=True, help="location of component csv")
parser.add_argument("--no-verify", dest='verify', action='store_false', help="disable TLS certificate verification")
args = parser.parse_args()

bd = Client(base_url=args.base_url, token=args.api_key, verify=args.verify)

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blackduck").setLevel(logging.WARNING)

# build param for project name search
params = {
    'q': [f"name:{args.project_name}"]
}

# find project base on name    
projects = [p for p in bd.get_resource('projects', params=params) if p['name'] == args.project_name]
assert len(projects) == 1, f"There should be one, and only one project named {args.project_name}. We found {len(projects)}"
project = projects[0]

# build param for version search
params = {
    'q': [f"name:{args.version_name}"]
}

# find project by version name
versions = [v for v in bd.get_resource('versions', project, params=params) if v['versionName'] == args.version_name]
assert len(versions) == 1, f"There should be one, and only one version named {args.version_name}. We found {len(versions)}"
version = versions[0]

# grab project version url for final call
project_url = version['_meta']['href']

# read csv file from args provided
cols = ['Component id', 'Version id', 'Component origin id']
df = pd.read_csv(args.component_list, usecols=cols)

# iterate df to grab the columns we care about and post them to the project
for index,row in df.iterrows():
    component_id = row['Component id']
    version_id = row['Version id']
    origin_id = row['Component origin id']
    
    component_endpoint = ""+project_url+"/components"

    component_data = {
        "component" : ""+args.base_url+"/api/components/"+component_id+"/versions/"+version_id+"/origin/"+origin_id+""
        }
    
    headers = {
        'Content-Type' : 'application/vnd.blackducksoftware.bill-of-materials-6+json'
    }
    
    r = bd.session.post(component_endpoint, json=component_data, headers=headers)
    if r.status_code == 200:
        logging.info("added component")
        logging.debug(component_data)
    else:
        bd.http_error_handler(r)
    
