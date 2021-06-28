from blackduck import Client
import logging
import argparse
import sys
from pprint import pprint
import requests
from requests.api import head

def readComponentList(compFile):
    compList = []
    try:
        fp = open(compFile, 'r')
        line =  fp.readline()
        while line:
              compList.append(line.strip() )
              line = fp.readline()
        fp.close()
    except:
         logging.error(f"Could not open component list file: {compFile}")
         sys.exit(-1)

     
    return compList


parser = argparse.ArgumentParser("Bulk add component comments (and optionally ignore) from a supplied list to a specific project version")
parser.add_argument("--base-url", required=True, help="Hub server URL e.g. https://your.blackduck.url")
parser.add_argument("--api-key", dest='api_key', required=True, help="containing access token")
parser.add_argument("--project", dest='project_name', required=True)
parser.add_argument("--version", dest="version_name", required=True)
parser.add_argument("--comment", dest="new_comment")
parser.add_argument("--component_list_file", dest="component_list")
parser.add_argument("--no-verify", dest='verify', action='store_false', help="disable TLS certificate verification")
parser.add_argument("--ignore", dest="ignore_comp", action='store_true', help='ignore component after comment')
args = parser.parse_args()

bd = Client(base_url=args.base_url, token=args.api_key, verify=args.verify)

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blackduck").setLevel(logging.WARNING)

bd = Client(base_url=args.base_url, token=args.api_key, verify=args.verify)

print(args.ignore_comp)

params = {
    'q': [f"name:{args.project_name}"]
}
    
projects = [p for p in bd.get_resource('projects', params=params) if p['name'] == args.project_name]
assert len(projects) == 1, f"There should be one, and only one project named {args.project_name}. We found {len(projects)}"
project = projects[0]

params = {
    'q': [f"name:{args.version_name}"]
}

versions = [v for v in bd.get_resource('versions', project, params=params) if v['versionName'] == args.version_name]
assert len(versions) == 1, f"There should be one, and only one version named {args.version_name}. We found {len(versions)}"
version = versions[0]

# get all components from version
components = bd.get_resource('components', version)

# load list of comps for update 
component_list = readComponentList(args.component_list)
# iterate list
for comp in components:
    for comp_to_update in component_list:
        if comp_to_update == comp['componentName']:
            meta = bd.get_metadata('comments', comp)
            url = meta['_meta']['href']

            comment_data = {
                'comment': args.new_comment
            }

            # POST the comment
            try:
                r = bd.session.post(url, json=comment_data)
                r.raise_for_status()
                logging.info("Comment Added")
                logging.debug(f"Component URL: {r.links['self']['url']}")
            except requests.HTTPError as err:
                bd.http_error_handler(err)
            
            if args.ignore_comp:
                compurl = comp['_meta']['href']

                payload = {
                    'ignored': 'true',
                    'componentType': 'KB_COMPONENT'
                }

                headers = {'accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}

                try:
                    r = bd.session.put(compurl, json=payload, headers=headers)
                    r.raise_for_status()
                    logging.info("Ignoring Component")
                except requests.HTTPError as err:
                    bd.http_error_handler(err)
