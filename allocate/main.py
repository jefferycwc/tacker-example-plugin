from service_mapping_plugin_framework.allocate_nssi_abc import AllocateNSSIabc
from .params import OS_MA_NFVO_IP,OS_USER_DOMAIN_NAME,OS_USERNAME,OS_PASSWORD,OS_PROJECT_DOMAIN_NAME,OS_PROJECT_NAME
import json
import os
import requests
import yaml
import glob
import time
import pprint


class NFVOPlugin(AllocateNSSIabc):
    def __init__(self, nm_host, nfvo_host, subscription_host, parameter):
        super().__init__(nm_host, nfvo_host, subscription_host, parameter)
        # Don't devstack environment OS_AUTH_URL can't add 'identity'.
        #self.OS_AUTH_URL = 'http://192.168.1.219:5000/v3/'
        #self.TACKER_URL = 'http://{}'.format(nfvo_host)
        #self.TACKER_URL = "http://192.168.1.219:9890/v1.0"
        self.OS_AUTH_URL = 'http://{}:5000/v3/'.format(OS_MA_NFVO_IP)
        self.TACKER_URL = 'http://{}:9890/v1.0'.format(OS_MA_NFVO_IP)
        self.OS_USER_DOMAIN_NAME = OS_USER_DOMAIN_NAME
        self.OS_USERNAME = OS_USERNAME
        self.OS_PASSWORD = OS_PASSWORD
        self.OS_PROJECT_DOMAIN_NAME = OS_PROJECT_DOMAIN_NAME
        self.OS_PROJECT_NAME = OS_PROJECT_NAME
        self.OS_VIM_NAME = "jefferyvim"
        self.ary_data = list()
        self.nsd_id = str()
        self.nsd_name = str()
        self.get_token_result = str()
        self.project_id = str()
        self.nsinfo = dict()

    def get_token(self):
        # print("\nGet token:")
        self.get_token_result = ''
        #get_token_url = 'http://192.168.1.219:5000/v3/auth/tokens'
        get_token_url = self.OS_AUTH_URL + 'auth/tokens'
        get_token_body = {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'domain': {
                                'name': self.OS_USER_DOMAIN_NAME
                            },
                            'name': self.OS_USERNAME,
                            'password': self.OS_PASSWORD
                        }
                    }
                },
                'scope': {
                    'project': {
                        'domain': {
                            'name': self.OS_PROJECT_DOMAIN_NAME
                        },
                        'name': self.OS_PROJECT_NAME
                    }
                }
            }
        }
        get_token_response = requests.post(get_token_url, data=json.dumps(get_token_body))
        #print("Get OpenStack token status: " + str(get_token_response.status_code))
        self.get_token_result = get_token_response.headers['X-Subject-Token']
        return self.get_token_result

    def get_project_id(self, project_name):
        # print("\nGet Project ID:")
        self.project_id = ''
        get_project_list_url = self.OS_AUTH_URL + 'projects'
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_project_list_response = requests.get(get_project_list_url, headers=headers)
        # print("Get OpenStack project list status: " + str(get_project_list_response.status_code))
        get_project_list_result = get_project_list_response.json()['projects']
        for project in get_project_list_result:
            if project['name'] == project_name:
                self.project_id = project['id']
            pass
        # print("Project ID:" + self.project_id)
        return self.project_id

    def json_to_array(self, json_data):
        self.ary_data = []
        if len(json_data) > 0:
            for key, value in json_data.items():
                self.ary_data.append(value)
        return self.ary_data

    def create_vnf_package(self, vnf_package_path):
        pass

    def upload_vnf_package(self, vnf_package_path):
        file_path_list = glob.glob(os.path.join(vnf_package_path, 'Definitions/*.yaml'))
        vnfd_file = file_path_list[0].replace(os.path.join(vnf_package_path, 'Definitions/'), '')
        vnfd_name = vnfd_file.split('.yaml')[0]
        print('\nUpload VNFD: ' + vnfd_name)
        vnfd_description = 'VNFD:' + vnfd_name
        vnfd_body = {
            'vnfd': {
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'name': vnfd_name,
                'description': vnfd_description,
                'service_types': [
                    {
                        'service_type': 'vnfd'
                    }
                ],
                'attributes': {
                    'vnfd': yaml.safe_load(open(file_path_list[0], 'r+').read())
                }
            }
        }
        #upload_vnfd_url = 'http://192.168.1.219:9890/v1.0/vnfds'
        upload_vnfd_url = self.TACKER_URL + "/vnfds"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        response = requests.post(upload_vnfd_url, data=json.dumps(vnfd_body), headers=headers)
        print('Upload VNFD status: ' + str(response.status_code))

    def upload_ns_descriptor(self, ns_descriptor_path):
        file_path_list = glob.glob(os.path.join(ns_descriptor_path, 'Definitions/*.yaml'))
        nsd_file = file_path_list[0].replace(os.path.join(ns_descriptor_path, 'Definitions/'), '')
        self.nsd_name = nsd_file.split('.yaml')[0]
        print('\nUpload NSD: ' + self.nsd_name)
        nsd_description = 'NSD:' + self.nsd_name
        nsd_body = {
            'nsd': {
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'name': self.nsd_name,
                'description': nsd_description,
                'attributes': {
                    'nsd': yaml.safe_load(open(file_path_list[0], 'r+').read())
                }
            }
        }
        print(str(nsd_body))
        #upload_nsd_url = 'http://192.168.1.219:9890/v1.0/nsds'
        upload_nsd_url = self.TACKER_URL + "/nsds"
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        response = requests.post(upload_nsd_url, data=json.dumps(nsd_body), headers=headers)
        print('Upload NSD status: ' + str(response.status_code))
        self.nsd_id = response.json()['nsd']['id']

    def create_ns_descriptor(self):
        pass

    def check_feasibility(self):
        pass

    def create_ns_instance(self):
        pass

    def list_vim(self):
        get_vim_list_url = self.TACKER_URL + '/vims'
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_vim_list_response = requests.get(get_vim_list_url, headers=headers)
        print("Get Tacker vim list status: " + str(get_vim_list_response.status_code))
        get_vim_list_result = get_vim_list_response.json()
        #text = get_vim_list_response.text
        #print(get_vim_list_result)
        #print(text)
        return get_vim_list_result

    def get_vim_id(self, vim_name):
        vim_list = self.list_vim()
        #print(vim_list)
        vim_id = None
        for vim in vim_list['vims']:
            if vim['name'] == vim_name:
                vim_id = vim['id']
                #print (vim_id)
            pass
        return vim_id


    def ns_instantiation(self, ns_descriptor_path):
        nsd_params_file = os.path.join(ns_descriptor_path, 'Definitions/params/{}.yaml').format(
            self.nsd_name)
        print('\nNS instantiation: ' + self.nsd_name)
        ns_description = "NS:" + self.nsd_name
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        res_show_ns = {}
        if os.path.isfile(nsd_params_file):
            nsd_params = yaml.safe_load(open(nsd_params_file, 'r+').read())
        else:
            nsd_params = {}
        vim_id = self.get_vim_id(self.OS_VIM_NAME)
        ns_body = {
            'ns': {
                'name': self.nsd_name,
                'nsd_id': self.nsd_id,
                'description': ns_description,
                'tenant_id': self.get_project_id(self.OS_PROJECT_NAME),
                'attributes': {
                    'param_values': nsd_params
                },
                'vim_id': vim_id,
            }
        }
        #create_ns_url = 'http://192.168.1.219:9890/v1.0/nss'
        create_ns_url = self.TACKER_URL + "/nss"
        res_create_ns = requests.post(create_ns_url, data=json.dumps(ns_body), headers=headers)
        print('Create NS status: ' + str(res_create_ns.status_code))
        ns_id = res_create_ns.json()['ns']['id']
        create_ns_status = res_create_ns.json()['ns']['status']
        count = 0
        while create_ns_status != 'ACTIVE' and create_ns_status != 'ERROR':
            show_ns_url = self.TACKER_URL + '/nss/' + ns_id
            res_show_ns = requests.get(show_ns_url, headers=headers).json()
            create_ns_status = res_show_ns['ns']['status']
            time.sleep(1)
            count = count + 1
            print('wait ' + str(count) + 's')
        pprint.pprint(res_show_ns)
        ns_instance_id = res_show_ns['ns']['id']
        description = res_show_ns['ns']['description']
        nsd_info_id = res_show_ns['ns']['nsd_id']
        vnf_info = res_show_ns['ns']['vnf_ids']
        vnffg_info = res_show_ns['ns']['vnffg_ids']
        ns_state = res_show_ns['ns']['status']
        monitoringParameter = res_show_ns['ns']['mgmt_urls']
        self.nsinfo = {
            'id': ns_instance_id,
            'nsInstanceDescription': description,
            'nsdInfoId': nsd_info_id,
            'vnfInstance': vnf_info,
            'vnffgInfo': vnffg_info,
            'nsState': ns_state,
            'monitoringParameter': monitoringParameter
        }
        #self.add_vnf_monitor(ns_instance_id,vnf_info)

    def get_vnf_attr(self,vnf_id):
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        get_vnf_url = self.TACKER_URL + "/vnfs/" + vnf_id
        res_get_vnf = requests.get(get_vnf_url,headers=headers)
        attributes = res_get_vnf.json()['vnf']['attributes']
        heat_template = attributes['heat_template']
        floating_ip_address=""
        index = heat_template.find("floating_ip_address")
        index = index+21
        while(1):
            if heat_template[index]=='\n':
                break
            floating_ip_address+=heat_template[index]
            index = index+1
        #floating_ip_address = heat_template[index+21:index+33]
    
        vnf_name = ""
        index = heat_template.find("name")
        index = index+6
        while(1):
            if heat_template[index]=='\n':
                break
            vnf_name+=heat_template[index]
            index = index+1
        #floating_ip_address = attributes['floating_ip_address']
        return vnf_name,floating_ip_address

    def add_vnf_monitor(self,ns_instance_id,vnf_info):
        vnf_info = vnf_info[1:-1]
        vnf_info_list = vnf_info.split(", ")
        vnf_id = []        
        for obj in vnf_info_list:
            sub_obj_list = obj.split(": ")
            sub_obj = sub_obj_list[1][1:-1]
            vnf_id.append(sub_obj)

        
        url = 'http://192.168.1.103:5010/vnf_monitor'
        for i in vnf_id:
            vnf_name,floating_ip_address = self.get_vnf_attr(i)
            #print("vnf_name:{} floating_ip_address:{}".format(vnf_name,floating_ip_address))
            body = {
                'vnf_name': vnf_name,
                'floating_ip_address': floating_ip_address
            }
            response = requests.post(url,json=body)
            print('Add VNF Monitor on {}'.format(vnf_name))
        
        '''for i in floating_ip_dict:
            print(i)'''
        
    def list_vnf(self):
        token = self.get_token()
        headers = {'X-Auth-Token': token}
        list_vnf_url = self.TACKER_URL + 'vnfs'
        res_list_vnf = requests.get(list_vnf_url, headers=headers).json()
        printf(str(res_list_vnf))

    def coordinate_tn_manager(self):
        pass

    def create_vnf_package_subscriptions(self, vnf):
        pass

    def listen_on_vnf_package_subscriptions(self):
        pass

    def create_ns_descriptor_subscriptions(self, ns_des):
        pass

    def listen_on_ns_descriptor_subscriptions(self):
        pass

    def create_ns_instance_subscriptions(self):
        pass

    def listen_on_ns_instance_subscriptions(self):
        pass

    def scale_ns_instantiation(self, ns_instance_id, scale_info):
        pass

    def update_ns_instantiation(self, ns_instance_id, update_info):
        pass

    def read_ns_instantiation(self, ns_instance_id):
        pass

    def read_ns_descriptor(self, nsd_object_id):
        pass

    def read_vnf_package(self, vnf_pkg_id):
        pass
