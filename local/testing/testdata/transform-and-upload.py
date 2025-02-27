#!/usr/bin/python

import argparse
import json
import math
import requests
import time
import uuid
from copy import copy
from requests.adapters import HTTPAdapter, Retry


def create_submodel_payload(json_payload):
    return json.dumps(json_payload)


def create_edc_asset_payload(submodel_url_, asset_id_):
    return json.dumps({
        "@context": {},
        "asset": {
            "@type": "Asset",
            "@id": f"{asset_id_}",
            "properties": {
                "description": "IRS EDC Test Asset"
            }
        },
        "dataAddress": {
            "@type": "DataAddress",
            "type": "HttpData",
            "baseUrl": f"{submodel_url_}",
            "proxyPath": "true",
            "proxyBody": "false",
            "proxyMethod": "false",
            "proxyQueryParams": "false"
        }
    })


def create_edc_registry_asset_payload(registry_url_, asset_prop_id_):
    return json.dumps({
        "@context": {},
        "asset": {
            "@type": "Asset",
            "@id": f"{asset_prop_id_}",  # DTR-EDC-instance-unique-ID
            "properties": {
                "type": "data.core.digitalTwinRegistry",
                "description": "Digital Twin Registry Endpoint of IRS DEV"
            }
        },
        "dataAddress": {
            "@type": "DataAddress",
            "type": "HttpData",
            "baseUrl": f"{registry_url_}",
            "proxyPath": "true",
            "proxyBody": "true",
            "proxyMethod": "true",
            "proxyQueryParams": "true"
        }
    })


def create_edc_notification_asset_payload(ess_url_, asset_id_, notification_type_):
    return json.dumps({
        "@context": {},
        "asset": {
            "@id": f"{asset_id_}",
            "properties": {
                "description": "ESS notification endpoint",
                "contenttype": "application/json",
                "notificationtype": f"{notification_type_}",
                "notificationmethod": "receive"
            }
        },
        "dataAddress": {
            "baseUrl": f"{ess_url_}",
            "type": "HttpData",
            "proxyBody": "true",
            "proxyMethod": "true"
        }
    })


def create_esr_edc_asset_payload(esr_url_, asset_prop_id_, digital_twin_id_):
    return json.dumps({
        "asset": {
            "properties": {
                "asset:prop:id": asset_prop_id_,
                "asset:prop:description": "product description",
                "asset:prop:contenttype": "application/json"
            }
        },
        "dataAddress": {
            "properties": {
                "baseUrl": f"{esr_url_}/{digital_twin_id_}/asBuilt/ISO14001/submodel",
                "type": "HttpData",
                "proxyBody": True,
                "proxyMethod": True
            }
        }
    })


def create_edc_contract_definition_payload(edc_policy_id_, asset_prop_id_):
    return json.dumps({
        "@context": {},
        "@type": "ContractDefinition",
        "accessPolicyId": f"{edc_policy_id_}",
        "contractPolicyId": f"{edc_policy_id_}",
        "assetsSelector": {
            "@type": "CriterionDto",
            "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
            "operator": "=",
            "operandRight": f"{asset_prop_id_}"
        }
    }
    )


def create_aas_shell(global_asset_id_, id_short_, identification_, specific_asset_id_, submodel_descriptors_):
    return json.dumps({
        "description": [],
        "globalAssetId": {
            "value": [
                global_asset_id_
            ]
        },
        "idShort": id_short_,
        "identification": identification_,
        "specificAssetIds": specific_asset_id_,
        "submodelDescriptors": submodel_descriptors_
    })


def create_submodel_descriptor(id_short_, identification_, semantic_id_, endpoint_address_):
    return json.dumps(
        {
            "description": [],
            "idShort": id_short_,
            "identification": identification_,
            "semanticId": {
                "value": [
                    semantic_id_
                ]
            },
            "endpoints": [
                {
                    "interface": "HTTP",
                    "protocolInformation": {
                        "endpointAddress": endpoint_address_,
                        "endpointProtocol": "AAS/IDS",
                        "endpointProtocolVersion": "0.1",
                        "subprotocol": "IDS",
                        "subprotocolBody": "TDB",
                        "subprotocolBodyEncoding": "plain"
                    }
                }
            ]
        }
    )


def create_aas_shell_3_0(global_asset_id_, id_short_, identification_, specific_asset_id_, submodel_descriptors_):
    return json.dumps({
        "description": [],
        "globalAssetId": global_asset_id_,
        "idShort": id_short_,
        "id": identification_,
        "specificAssetIds": specific_asset_id_,
        "submodelDescriptors": submodel_descriptors_
    })


def create_submodel_descriptor_3_0(id_short_, identification_, semantic_id_, dataplane_asset_address_, asset_id_,
                                   endpoint_):
    return json.dumps(
        {
            "description": [],
            "idShort": id_short_,
            "id": identification_,
            "semanticId": {
                "type": "ExternalReference",
                "keys": [
                    {
                        "type": "GlobalReference",
                        "value": semantic_id_
                    }
                ]
            },
            "endpoints": [
                {
                    "interface": "SUBMODEL-3.0",
                    "protocolInformation": {
                        "href": dataplane_asset_address_,
                        "endpointProtocol": "HTTP",
                        "endpointProtocolVersion": ["1.1"],
                        "subprotocol": "DSP",
                        "subprotocolBody": f"id={asset_id_};dspEndpoint={endpoint_}",
                        "subprotocolBodyEncoding": "plain",
                        "securityAttributes": [
                            {
                                "type": "NONE",
                                "key": "NONE",
                                "value": "NONE"
                            }
                        ]
                    }
                }
            ]
        }
    )


def print_response(response_):
    print(response_)
    if response_.status_code > 205:
        print(response_.text)


def check_url_args(submodel_server_upload_urls_, submodel_server_urls_, edc_upload_urls_, edc_urls_, dataplane_urls_):
    nr_of_submodel_server_upload_urls = len(submodel_server_upload_urls_)
    nr_of_submodel_server_urls = len(submodel_server_urls_)
    if nr_of_submodel_server_upload_urls != nr_of_submodel_server_urls:
        raise ArgumentException(
            f"Number and order of submodelserver upload URLs '{submodel_server_upload_urls_}' "
            f"has to match number and order Number and order of submodelserver URLs '{submodel_server_urls_}'")
    nr_of_edc_upload_urls = len(edc_upload_urls_)
    nr_of_edc_urls = len(edc_urls_)
    if nr_of_edc_upload_urls != nr_of_edc_urls:
        raise ArgumentException(
            f"Number and order of edc upload URLs '{edc_upload_urls_}' has to match number and order of edc URLs "
            f"'{edc_urls_}'")
    if nr_of_submodel_server_urls != nr_of_edc_urls:
        raise ArgumentException(
            f"Number and order of edc URLs '{edc_urls_}' has to match number and order of submodelserver URLS "
            f"'{submodel_server_urls_}'")
    nr_of_dataplane_urls = len(dataplane_urls_)
    if nr_of_dataplane_urls != nr_of_edc_urls:
        raise ArgumentException(
            f"Number and order of edc controlplane URLs '{edc_urls_}' has to match number and order of edc dataplane "
            f"URLS'{submodel_server_urls_}'")


class ArgumentException(Exception):
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    @staticmethod  # known case of __new__
    def __new__(*args, **kwargs):  # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


def create_policy(policy_, edc_upload_url_, edc_policy_path_, headers_, session_):
    url_ = edc_upload_url_ + edc_policy_path_
    print(f"Create policy {policy_['@id']} on EDC {url_}")
    response_ = session_.request(method="GET", url=f"{url_}/{policy_['@id']}", headers=headers_)
    if response_.status_code == 200 and response_.json():
        print(f"Policy {policy_['@id']} already exists. Skipping creation.")
    else:
        response_ = session_.request(method="POST", url=url_, headers=headers_, data=json.dumps(policy_))
        print(response_)
        if response_.status_code > 205:
            print(response_.text)
        else:
            print(f"Successfully created policy {response_.json()['@id']}.")


def create_registry_asset(edc_upload_urls_, edc_asset_path_, edc_contract_definition_path_, catalog_path_, header_,
                          session_, edc_urls_, policy_, registry_asset_id_, aas_url_):
    for edc_upload_url_ in edc_upload_urls_:
        index = edc_upload_urls_.index(edc_upload_url_)
        edc_url_ = edc_urls_[index]
        print(edc_url_)
        print(edc_upload_url_)

        catalog_url_ = edc_upload_url_ + catalog_path_
        payload_ = {
            "@context": edc_context(),
            "edc:protocol": "dataspace-protocol-http",
            "edc:providerUrl": f"{edc_url_}/api/v1/dsp",
            "edc:querySpec": {
                "edc:filterExpression": {
                    "@type": "edc:Criterion",
                    "edc:operandLeft": "https://w3id.org/edc/v0.0.1/ns/type",
                    "edc:operator": "=",
                    "edc:operandRight": "data.core.digitalTwinRegistry"
                }
            }
        }
        print(f"Query Catalog for registry asset {catalog_url_}")
        response_ = session_.request(method="POST", url=catalog_url_, headers=header_, data=json.dumps(payload_))

        asset_url_ = edc_upload_url_ + edc_asset_path_
        print(response_.status_code)
        catalog_response_ = response_.json()
        if response_.status_code == 200 and len(catalog_response_['dcat:dataset']) >= 1:
            first_offer_ = catalog_response_['dcat:dataset']
            print(
                f"Offer with type {first_offer_['edc:type']} already exists. Skipping creation.")
        else:
            payload_ = create_edc_registry_asset_payload(aas_url_, registry_asset_id_)
            response_ = session_.request(method="POST", url=asset_url_,
                                         headers=header_,
                                         data=payload_)
            print(response_)
            if response_.status_code > 205:
                print(response_.text)
            else:
                print(f"Successfully created registry asset {response_.json()['@id']}.")

            print("Create registry edc contract definition")
            payload_ = create_edc_contract_definition_payload(policy_, registry_asset_id_)
            response_ = session_.request(method="POST", url=edc_upload_url_ + edc_contract_definition_path_,
                                         headers=header_,
                                         data=payload_)
            print_response(response_)


def edc_context():
    return {
        "dct": "https://purl.org/dc/terms/",
        "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
        "edc": "https://w3id.org/edc/v0.0.1/ns/",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "dcat": "https://www.w3.org/ns/dcat/",
        "dspace": "https://w3id.org/dspace/v0.8/"}


def create_notification_assets(edc_upload_urls_, edc_asset_path_, edc_contract_definition_path_, edc_catalog_path_,
                               edc_public_path_, header_, session_, edc_urls_, policy_, ess_base_url_):
    for edc_upload_url_ in edc_upload_urls_:
        index = edc_upload_urls_.index(edc_upload_url_)
        edc_url_ = edc_urls_[index] + edc_public_path_
        print(edc_url_)
        print(edc_upload_url_)

        notifications_ = [
            {
                "id": "ess-response-asset",
                "type": "ess-supplier-response",
                "path": "/ess/notification/receive"
            },
            {
                "id": "notify-request-asset",
                "type": "ess-supplier-request",
                "path": "/ess/mock/notification/receive"
            },
            {
                "id": "notify-request-asset-recursive",
                "type": "ess-supplier-request",
                "path": "/ess/notification/receive-recursive"
            }
        ]

        for notification_ in notifications_:
            notification_id = notification_['id']
            notification_type = notification_['type']
            ess_url = f"{ess_base_url_}{notification_['path']}"
            response_ = search_for_asset_in_catalog(edc_catalog_path_, edc_upload_url_, edc_url_, header_, session_,
                                                    notification_id)
            asset_url_ = edc_upload_url_ + edc_asset_path_
            print(response_.status_code)
            catalog_response_ = response_.json()
            if response_.status_code == 200 and len(catalog_response_['dcat:dataset']) >= 1:
                print(
                    f"Offer with id {notification_id} already exists. Skipping creation.")
            else:
                payload_ = create_edc_notification_asset_payload(ess_url, notification_id, notification_type)
                response_ = session_.request(method="POST", url=asset_url_, headers=header_, data=payload_)
                print(response_)
                if response_.status_code > 205:
                    print(response_.text)
                else:
                    print(f"Successfully created notification asset {response_.json()['@id']}.")

                print("Create registry edc contract definition")
                payload_ = create_edc_contract_definition_payload(policy_, notification_id)
                response_ = session_.request(method="POST", url=edc_upload_url_ + edc_contract_definition_path_,
                                             headers=header_,
                                             data=payload_)
                print_response(response_)


def search_for_asset_in_catalog(edc_catalog_path_, edc_upload_url_, edc_url_, headers_, session_, asset_id_):
    catalog_url_ = edc_upload_url_ + edc_catalog_path_
    payload_ = {
        "@context": edc_context(),
        "edc:protocol": "dataspace-protocol-http",
        "edc:providerUrl": f"{edc_url_}",
        "edc:querySpec": {
            "edc:filterExpression": {
                "@type": "edc:Criterion",
                "edc:operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                "edc:operator": "=",
                "edc:operandRight": f"{asset_id_}"
            }
        }
    }
    print(f"Query Catalog for notification assets {catalog_url_}")
    return session_.request(method="POST", url=catalog_url_, headers=headers_, data=json.dumps(payload_))


if __name__ == "__main__":
    timestamp_start = time.time()
    parser = argparse.ArgumentParser(description="Script to upload testdata into CX-Network.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--file", type=str, help="Test data file location", required=True)
    parser.add_argument("-s", "--submodel", type=str, nargs="*", help="Submodel server display URLs", required=True)
    parser.add_argument("-su", "--submodelupload", type=str, nargs="*", help="Submodel server upload URLs",
                        required=False)
    parser.add_argument("-a", "--aas", type=str, help="aas url", required=True)
    parser.add_argument("-au", "--aasupload", type=str, help="aas url", required=False)
    parser.add_argument("-edc", "--edc", type=str, nargs="*", help="EDC provider control plane display URLs",
                        required=True)
    parser.add_argument("-eu", "--edcupload", type=str, nargs="*", help="EDC provider control plane upload URLs",
                        required=False)
    parser.add_argument("-k", "--apikey", type=str, help="EDC provider api key", required=True)
    parser.add_argument("-e", "--esr", type=str, help="ESR URL", required=False)
    parser.add_argument("--ess", help="Enable ESS data creation with invalid EDC URL", action='store_true',
                        required=False)
    parser.add_argument("--bpn", help="Faulty BPN which will create a non existing EDC endpoint", required=False)
    parser.add_argument("-p", "--policy", help="Default Policy which should be used for EDC contract definitions",
                        required=False)
    parser.add_argument("-bpns", "--bpns", type=str, nargs="*", help="Filter upload to upload only specific BPNs",
                        required=False)
    parser.add_argument("--aas3", help="Create AAS assets in version 3.0", action='store_true', required=False)
    parser.add_argument("-d", "--dataplane", type=str, nargs="*", help="EDC provider data plane display URLs",
                        required=False)
    parser.add_argument("--allowedBPNs", type=str, nargs="*",
                        help="The allowed BPNs for digital twin registration in the registry.", required=False)
    parser.add_argument("--essURL", type=str, help="The base URL of the ESS Service API", required=False)

    args = parser.parse_args()
    config = vars(args)

    filepath = config.get("file")
    submodel_server_urls = config.get("submodel")
    submodel_server_upload_urls = config.get("submodelupload")
    aas_url = config.get("aas")
    aas_upload_url = config.get("aasupload")
    edc_urls = config.get("edc")
    edc_upload_urls = config.get("edcupload")
    edc_api_key = config.get("apikey")
    esr_url = config.get("esr")
    is_ess = config.get("ess")
    ess_base_url = config.get("essURL")
    bpnl_fail = config.get("bpn")
    default_policy = config.get("policy")
    bpns_list = config.get("bpns")
    is_aas3 = config.get("aas3")
    dataplane_urls = config.get("dataplane")
    allowedBPNs = config.get("allowedBPNs")

    if is_aas3 and dataplane_urls is None:
        raise ArgumentException("Dataplane URLs have to be specified with -d or --dataplane if --aas flag is set!")
    if is_ess and ess_base_url is None:
        raise ArgumentException("ESS base URL has to be specified with --essURL if --ess flag is set!")

    if submodel_server_upload_urls is None:
        submodel_server_upload_urls = submodel_server_urls
    if edc_upload_urls is None:
        edc_upload_urls = edc_urls

    if default_policy is None:
        default_policy = "default-policy"

    if aas_upload_url is None:
        aas_upload_url = aas_url

    if allowedBPNs is None:
        allowedBPNs = []

    registry_path = "/registry/shell-descriptors"
    if is_aas3:
        registry_path = "/shell-descriptors"

    check_url_args(submodel_server_upload_urls, submodel_server_urls, edc_upload_urls, edc_urls, dataplane_urls)

    edc_asset_path = "/management/v2/assets"
    edc_policy_path = "/management/v2/policydefinitions"
    edc_contract_definition_path = "/management/v2/contractdefinitions"
    edc_catalog_path = "/management/v2/catalog/request"
    dataplane_public_path = "/api/public"
    controlplane_public_path = "/api/v1/dsp"

    registry_asset_id = "registry-asset"

    headers = {
        'Content-Type': 'application/json'
    }

    headers_with_api_key = {
        'X-Api-Key': edc_api_key,
        'Content-Type': 'application/json'
    }

    default_policy_definition = {
        "default": {
            "@context": {
                "odrl": "http://www.w3.org/ns/odrl/2/"
            },
            "@type": "PolicyDefinitionRequestDto",
            "@id": "default-policy",
            "policy": {
                "@type": "Policy",
                "odrl:permission": []
            }
        }
    }

    # Opening JSON file
    f = open(filepath)
    data = json.load(f)
    f.close()
    testdata = data["https://catenax.io/schema/TestDataContainer/1.0.0"]
    policies = default_policy_definition
    if "policies" in data.keys():
        policies.update(data["policies"])

    contract_number = 1

    retries = Retry(total=5,
                    backoff_factor=0.1)
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))

    if policies:
        for policy in policies.keys():
            for url in edc_upload_urls:
                create_policy(policies[policy], url, edc_policy_path, headers_with_api_key, session)

    create_registry_asset(edc_upload_urls, edc_asset_path, edc_contract_definition_path, edc_catalog_path,
                          headers_with_api_key, session, edc_urls, default_policy, registry_asset_id, aas_url)

    if is_ess:
        create_notification_assets(edc_upload_urls, edc_asset_path, edc_contract_definition_path, edc_catalog_path,
                                   controlplane_public_path, headers_with_api_key, session, edc_urls, default_policy,
                                   ess_base_url)

    edc_asset_ids = []
    for url in dataplane_urls:
        edc_asset_ids.append(uuid.uuid4().urn)
    print(edc_asset_ids)

    esr = "urn:bamm:io.catenax.esr_certificates.esr_certificate_state_statistic:1.0.1#EsrCertificateStateStatistic"
    apr = "urn:bamm:io.catenax.single_level_bom_as_built:1.0.0#SingleLevelBomAsBuilt"
    for tmp_data in testdata:
        if bpns_list is None or tmp_data["bpnl"] in bpns_list or not bpns_list:
            catenax_id = tmp_data["catenaXId"]
            identification = uuid.uuid4().urn
            tmp_keys = tmp_data.keys()

            specific_asset_ids = []

            submodel_descriptors = []

            name_at_manufacturer = ""
            specific_asset_ids_temp = []
            for tmp_key in tmp_keys:
                if "Batch" in tmp_key or "SerialPart" in tmp_key:
                    specific_asset_ids_temp = copy(tmp_data[tmp_key][0]["localIdentifiers"])
                    name_at_manufacturer = tmp_data[tmp_key][0]["partTypeInformation"]["nameAtManufacturer"].replace(
                        " ",
                        "")
                if "PartAsPlanned" in tmp_key:
                    name_at_manufacturer = tmp_data[tmp_key][0]["partTypeInformation"]["nameAtManufacturer"].replace(
                        " ",
                        "")
                    specific_asset_ids_temp.append({
                        "value": tmp_data[tmp_key][0]["partTypeInformation"]["manufacturerPartId"],
                        "key": "manufacturerPartId"
                    })
            print(name_at_manufacturer)

            manufacturerId = {
                "key": "manufacturerId",
                "value": tmp_data["bpnl"]
            }
            if manufacturerId not in specific_asset_ids_temp:
                specific_asset_ids_temp.append(manufacturerId)
            if is_aas3:
                keys = [{
                    "type": "GlobalReference",
                    "value": "PUBLIC_READABLE"
                }]
                for bpn in allowedBPNs:
                    keys.append({
                        "type": "GlobalReference",
                        "value": bpn
                    })
                externalSubjectId = {
                    "type": "ExternalReference",
                    "keys": keys
                }
                for asset in specific_asset_ids_temp:
                    specific_asset_ids.append({
                        "name": asset.get("key"),
                        "value": asset.get("value"),
                        "externalSubjectId": externalSubjectId
                    })
            else:
                specific_asset_ids = specific_asset_ids_temp

            if esr_url and apr in tmp_keys and "childItems" in tmp_data[apr][0] and tmp_data[apr][0]["childItems"]:
                tmp_data.update({esr: ""})

            policy_id = default_policy
            if "policy" in tmp_keys:
                policy_id = tmp_data["policy"]
            print(f"Policy: {policy_id}")

            for tmp_key in tmp_keys:
                if "PlainObject" not in tmp_key and "catenaXId" not in tmp_key and "bpn" not in tmp_key \
                        and "policy" not in tmp_key and "urn:bamm:io.catenax.aas:1.0.0#AAS" not in tmp_key:
                    # Prepare submodel endpoint address
                    submodel_url = submodel_server_urls[contract_number % len(submodel_server_urls)]
                    submodel_upload_url = submodel_server_upload_urls[
                        contract_number % len(submodel_server_upload_urls)]
                    edc_url = edc_urls[contract_number % len(edc_urls)]
                    edc_upload_url = edc_upload_urls[contract_number % len(edc_upload_urls)]
                    dataplane_url = dataplane_urls[contract_number % len(dataplane_urls)]
                    edc_asset_id = edc_asset_ids[contract_number % len(edc_asset_ids)]

                    submodel_name = tmp_key[tmp_key.index("#") + 1: len(tmp_key)]
                    submodel_identification = uuid.uuid4().urn
                    semantic_id = tmp_key
                    if is_ess and tmp_data["bpnl"] in bpnl_fail:
                        endpoint_address = f"http://idonotexist/{catenax_id}-{submodel_identification}/submodel?content=value&extent=withBlobValue"
                    elif submodel_name == "EsrCertificateStateStatistic" and esr_url is not None:
                        endpoint_address = f"{esr_url}/{catenax_id}/asBuilt/ISO14001/submodel"
                    else:
                        endpoint_address = f"{edc_url}/{catenax_id}-{submodel_identification}/submodel?content=value&extent=withBlobValue"

                    if is_aas3:
                        endpoint_address = f"{dataplane_url}{dataplane_public_path}/data/{submodel_identification}"
                        if is_ess and tmp_data["bpnl"] in bpnl_fail:
                            endpoint_address = f"http://idonotexist/{dataplane_public_path}/data/{submodel_identification}"
                        descriptor = create_submodel_descriptor_3_0(submodel_name, submodel_identification, semantic_id,
                                                                    endpoint_address,
                                                                    edc_asset_id,
                                                                    edc_url)
                        submodel_descriptors.append(json.loads(descriptor))
                    else:
                        descriptor = create_submodel_descriptor(submodel_name, submodel_identification, semantic_id,
                                                                endpoint_address)
                        submodel_descriptors.append(json.loads(descriptor))

                    if is_aas3:
                        asset_prop_id = edc_asset_id
                    else:
                        asset_prop_id = f"{catenax_id}-{submodel_identification}"

                    print("Create submodel on submodel server")
                    if tmp_data[tmp_key] != "":
                        payload = create_submodel_payload(tmp_data[tmp_key][0])
                        response = session.request(method="POST",
                                                   url=f"{submodel_upload_url}/data/{submodel_identification}",
                                                   headers=headers, data=payload)
                        print_response(response)

                    asset_path = edc_upload_url + edc_asset_path
                    print(f"Create edc asset on EDC {asset_path}")
                    if submodel_name == "EsrCertificateStateStatistic" and esr_url is not None:
                        payload = create_esr_edc_asset_payload(esr_url, asset_prop_id, catenax_id)
                    else:
                        payload = create_edc_asset_payload(submodel_url, asset_prop_id)
                    response = session.request(method="POST", url=asset_path, headers=headers_with_api_key,
                                               data=payload)
                    print_response(response)
                    if response.status_code > 205:
                        print("Asset creation failed. Skipping creation of contract definition.")
                    else:
                        print("Create edc contract definition")
                        payload = create_edc_contract_definition_payload(policy_id, asset_prop_id)
                        response = session.request(method="POST", url=edc_upload_url + edc_contract_definition_path,
                                                   headers=headers_with_api_key,
                                                   data=payload)
                        print_response(response)
                    contract_number = contract_number + 1

            if submodel_descriptors:
                print("Create aas shell")
                if is_aas3:
                    payload = create_aas_shell_3_0(catenax_id, name_at_manufacturer, identification, specific_asset_ids,
                                                   submodel_descriptors)
                else:
                    payload = create_aas_shell(catenax_id, name_at_manufacturer, identification, specific_asset_ids,
                                               submodel_descriptors)
                response = session.request(method="POST", url=f"{aas_upload_url}{registry_path}",
                                           headers=headers,
                                           data=payload)
                print_response(response)

    timestamp_end = time.time()
    duration = timestamp_end - timestamp_start
    print(f"Test data upload completed in {math.ceil(duration)} Seconds")
