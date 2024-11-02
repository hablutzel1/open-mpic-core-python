from pydantic import BaseModel


class RemotePerspective(BaseModel):
    code: str
    # name seems to be an unused var and based on the spec the dot code seems to uniquely define a perspective.
    name: str | None = None
    rir: str
    too_close_codes: list[str] | None = []

    def is_perspective_too_close(self, perspective):
        return perspective.code in self.too_close_codes

    @staticmethod
    def from_rir_code(rir_dot_code: str):
        perspective_parts = rir_dot_code.split('.')
        return RemotePerspective(code=perspective_parts[1], rir=perspective_parts[0])

    def to_rir_code(self):
        return f"{self.rir}.{self.code}"
