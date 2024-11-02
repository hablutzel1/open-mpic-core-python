from abc import ABC
from typing import Literal, Union

from typing_extensions import Annotated

from open_mpic_core.common_domain.enum.check_type import CheckType
from pydantic import BaseModel, model_validator, Field

from open_mpic_core.mpic_coordinator.domain.mpic_orchestration_parameters import MpicRequestOrchestrationParameters
from open_mpic_core.common_domain.check_parameters import CaaCheckParameters, DcvCheckParameters


class BaseMpicRequest(BaseModel, ABC):
    domain_or_ip_target: str
    check_type: CheckType
    orchestration_parameters: MpicRequestOrchestrationParameters | None = None

    @model_validator(mode='after')
    def check_perspectives_and_perspective_count_together(self) -> 'BaseMpicRequest':
        if self.orchestration_parameters:
            assert not (self.orchestration_parameters.perspectives and self.orchestration_parameters.perspective_count), "Request contains both 'perspectives' and 'perspective_count'."
        return self


class MpicCaaRequest(BaseMpicRequest):
    check_type: Literal[CheckType.CAA] = CheckType.CAA
    caa_check_parameters: CaaCheckParameters | None = None


class MpicDcvRequest(BaseMpicRequest):
    check_type: Literal[CheckType.DCV] = CheckType.DCV
    dcv_check_parameters: DcvCheckParameters


class MpicDcvWithCaaRequest(MpicDcvRequest):  # inherits from MpicDcvRequest rather than BaseMpicRequest
    check_type: Literal[CheckType.DCV_WITH_CAA] = CheckType.DCV_WITH_CAA
    caa_check_parameters: CaaCheckParameters | None = None


MpicRequest = Annotated[Union[MpicCaaRequest, MpicDcvRequest, MpicDcvWithCaaRequest], Field(discriminator='check_type')]
