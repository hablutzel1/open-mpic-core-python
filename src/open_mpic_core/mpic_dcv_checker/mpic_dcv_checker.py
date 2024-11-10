import time
import dns.resolver
import requests

from open_mpic_core.common_domain.check_request import DcvCheckRequest
from open_mpic_core.common_domain.check_response import DcvCheckResponse, DcvCheckResponseDetails
from open_mpic_core.common_domain.check_response_details import DcvDnsChangeResponseDetails, \
    DcvWebsiteChangeResponseDetails, RedirectResponse
from open_mpic_core.common_domain.enum.dcv_validation_method import DcvValidationMethod
from open_mpic_core.common_domain.remote_perspective import RemotePerspective
from open_mpic_core.common_domain.validation_error import MpicValidationError


# noinspection PyUnusedLocal
class MpicDcvChecker:
    WELL_KNOWN_PKI_PATH = '.well-known/pki-validation'
    WELL_KNOWN_ACME_PATH = '.well-known/acme-challenge'

    def __init__(self, perspective: RemotePerspective):
        self.perspective = perspective
        # TODO self.dns_resolver = dns.resolver.Resolver() -- set up a way to use Unbound here... maybe take a config?

    def check_dcv(self, dcv_request: DcvCheckRequest) -> DcvCheckResponse:
        match dcv_request.dcv_check_parameters.validation_details.validation_method:
            case DcvValidationMethod.WEBSITE_CHANGE_V2:
                return self.perform_website_change_validation(dcv_request)
            case DcvValidationMethod.DNS_CHANGE:
                return self.perform_dns_change_validation(dcv_request)

    def perform_website_change_validation(self, request) -> DcvCheckResponse:
        domain_or_ip_target = request.domain_or_ip_target  # TODO optionally iterate up through the domain hierarchy
        url_scheme = request.dcv_check_parameters.validation_details.url_scheme
        token_path = request.dcv_check_parameters.validation_details.http_token_path
        token_url = f"{url_scheme}://{domain_or_ip_target}/{MpicDcvChecker.WELL_KNOWN_PKI_PATH}/{token_path}"  # noqa E501 (http)
        expected_response_content = request.dcv_check_parameters.validation_details.challenge_value

        # try to get 100 bytes of the response content (or more only if expected)
        # expected_response_content_length = len(expected_response_content.encode('utf-8'))
        # max_bytes_requested = max(100, expected_response_content_length)
        # headers = {"Range": f"bytes=0-{max_bytes_requested}"}  # not all servers support Range header

        response = requests.get(token_url)  # FIXME should probably add a timeout here.. but how long?
        response_history = None
        if hasattr(response, 'history') and response.history is not None and len(response.history) > 0:
            response_history = [
                RedirectResponse(status_code=resp.status_code, url=resp.headers['Location'])
                for resp in response.history
            ]

        if response.status_code == requests.codes.OK:
            result = response.text.strip()
            dcv_check_response = DcvCheckResponse(
                perspective_code=self.perspective.code,
                check_passed=(result == expected_response_content),
                timestamp_ns=time.time_ns(),
                details=DcvWebsiteChangeResponseDetails(
                    response_status_code=response.status_code,
                    response_url=token_url,
                    response_history=response_history
                ),
            )
        else:
            dcv_check_response = DcvCheckResponse(
                perspective_code=self.perspective.code,
                check_passed=False,
                timestamp_ns=time.time_ns(),
                errors=[MpicValidationError(error_type=str(response.status_code), error_message=response.reason)],
                details=DcvWebsiteChangeResponseDetails(
                    response_status_code=response.status_code,
                    response_history=response_history
                )
            )

        return dcv_check_response

    def perform_dns_change_validation(self, request) -> DcvCheckResponse:
        domain_or_ip_target = request.domain_or_ip_target
        dns_name_prefix = request.dcv_check_parameters.validation_details.dns_name_prefix
        dns_record_type = dns.rdatatype.from_text(request.dcv_check_parameters.validation_details.dns_record_type)
        if dns_name_prefix is not None and len(dns_name_prefix) > 0:
            name_to_resolve = f"{dns_name_prefix}.{domain_or_ip_target}"
        else:
            name_to_resolve = domain_or_ip_target
        expected_dns_record_content = request.dcv_check_parameters.validation_details.challenge_value

        # TODO add leading underscore to name_to_resolve if it's not found?

        print(f"Resolving {dns_record_type.name} record for {name_to_resolve}...")
        try:
            lookup = dns.resolver.resolve(name_to_resolve, dns_record_type)
            records_as_strings = []
            for response_answer in lookup.response.answer:
                if response_answer.rdtype == dns_record_type:
                    for record_data in response_answer:
                        # only need to remove enclosing quotes if they're there, e.g., for a TXT record
                        record_data_as_string = record_data.to_text()
                        if record_data_as_string[0] == '"' and record_data_as_string[-1] == '"':
                            records_as_strings.append(record_data_as_string[1:-1])
                        else:
                            records_as_strings.append(record_data_as_string)

            dcv_check_response = DcvCheckResponse(
                perspective_code=self.perspective.code,
                check_passed=expected_dns_record_content in records_as_strings,
                timestamp_ns=time.time_ns(),
                details=DcvDnsChangeResponseDetails()  # FIXME get details (or don't bother with this)
            )
            return dcv_check_response
        except dns.exception.DNSException as e:
            dcv_check_response = DcvCheckResponse(
                perspective_code=self.perspective.code,
                check_passed=False,
                timestamp_ns=time.time_ns(),
                errors=[MpicValidationError(error_type=e.__class__.__name__, error_message=e.msg)],
                details=DcvDnsChangeResponseDetails()
            )
            return dcv_check_response
