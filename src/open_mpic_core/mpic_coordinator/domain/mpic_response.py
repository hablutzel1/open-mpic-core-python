from abc import ABC
from typing import Union, Literal

from open_mpic_core.common_domain.enum.check_type import CheckType
from pydantic import BaseModel, Field

from open_mpic_core.common_domain.check_response import CaaCheckResponse, DcvCheckResponse
from open_mpic_core.mpic_coordinator.domain.mpic_orchestration_parameters import MpicEffectiveOrchestrationParameters
from open_mpic_core.mpic_coordinator.domain.mpic_orchestration_parameters import MpicRequestOrchestrationParameters
from open_mpic_core.common_domain.check_parameters import CaaCheckParameters, DcvCheckParameters
from typing_extensions import Annotated


class BaseMpicResponse(BaseModel, ABC):
    request_orchestration_parameters: MpicRequestOrchestrationParameters | None = None
    actual_orchestration_parameters: MpicEffectiveOrchestrationParameters | None = None
    is_valid: bool | None = False


class MpicCaaResponse(BaseMpicResponse):
    check_type: Literal[CheckType.CAA] = CheckType.CAA
    perspectives: list[CaaCheckResponse] | None = None  # not set in less verbose mode
    caa_check_parameters: CaaCheckParameters | None = None  # not set in less verbose mode


class MpicDcvResponse(BaseMpicResponse):
    check_type: Literal[CheckType.DCV] = CheckType.DCV
    perspectives: list[DcvCheckResponse] | None = None  # not set in less verbose mode
    dcv_check_parameters: DcvCheckParameters | None = None


MpicResponse = Annotated[Union[MpicCaaResponse, MpicDcvResponse], Field(discriminator='check_type')]
